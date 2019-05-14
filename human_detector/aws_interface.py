import json
import os
import tempfile
import decimal
import boto3
import logging
import sys

from utils import DecimalDecoder
from video_analyzer import VideoAnalyzer


###############
# S3 functions
###############

def get_object_from_s3(bucket_name, key, local_filename):
    """
    download file from s3 to local file. You must have access rights

    :param bucket_name: name of the bucket
    :param key: key of the file to get in the bucket
    :param local_filename: path to file to write
    :return: None
    """
    print("getting file {} from bucket {}".format(key, bucket_name))
    s3 = boto3.resource('s3')

    try:
        s3.Bucket(bucket_name).download_file(key, local_filename)
        print("file received")
    except Exception as e:
        print(e)
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise e


def put_object_to_s3(local_filename, bucket_name, key):
    """
    upload file to s3 from local file. You must have access rights

    :param local_filename: path to file to write
    :param bucket_name: name of the bucket
    :param key: key of the file to write in the bucket
    :return: None
    """
    print("uploading file {} to bucket {}".format(key, bucket_name))
    s3 = boto3.client('s3')

    try:
        s3.upload_file(local_filename, bucket_name, key)
        print("file uploaded")
    except Exception as e:
        raise e


#####################
# DynamoDB functions
#####################


def get_video_info_from_dynamo_db(region_id, tableId, search_keys):
    """
    get a document in dynamoDB (index is VideoId, must exist and be filled, no auto-increment)

    :param region_id: region of the table to get from
    :param tableId: table to get from
    :param document: dict to get from
    :return: None
    """
    dynamodb = boto3.resource('dynamodb', region_name=region_id) #, endpoint_url="http://localhost:8000")
    table = dynamodb.Table(tableId)
    # trick to turn floats and ints to Decimal for DynamoDB
    response = table.get_item(Key=search_keys)
    try:
        return json.loads(json.dumps(response["Item"], indent=4, cls=DecimalDecoder))
    except KeyError:
        raise Exception('Could not find document in dynamoDB with request {}'.format(search_keys))


def send_video_info_to_dynamo_db(region_id, tableId, document):
    """
    put or update a document in dynamoDB (index is VideoId, must exist and be filled, no auto-increment)

    :param region_id: region of the table to insert into
    :param tableId: table to insert into
    :param document: dict to insert
    :return: None
    """
    dynamodb = boto3.resource('dynamodb', region_name=region_id) #, endpoint_url="http://localhost:8000")
    table = dynamodb.Table(tableId)
    # trick to turn floats and ints to Decimal for DynamoDB
    response = table.put_item(Item=json.loads(json.dumps(document), parse_float=decimal.Decimal))
    return response


def process_video(step_name,
                  video_id, video_analyzer,
                  video_s3_bucket, video_s3_key,
                  dyndb_region_id, dyndb_tableId,
                  logger):

    # get doc from dynamodb
    logger.debug("Getting doc from dynamoDB")
    video_doc = get_video_info_from_dynamo_db(dyndb_region_id, dyndb_tableId, {"VideoId": int(video_id)})
    video_doc["process_steps"].append({"step": step_name, "state": "running"})
    send_video_info_to_dynamo_db(dyndb_region_id, dyndb_tableId, video_doc)

    video_temp_file = tempfile.NamedTemporaryFile(delete=False)
    results_temp_file = tempfile.NamedTemporaryFile(delete=False)
    try:
        # get video from s3
        logger.debug("Getting video from S3: {}/{}".format(video_s3_bucket, video_s3_key))
        get_object_from_s3(video_s3_bucket, video_s3_key, video_temp_file.name)
        video_name = os.path.basename(video_s3_key)
        video_name = video_name[:video_name.rfind('.')]

        # analyze video
        logger.debug("Analyzing video")
        results = video_analyzer.analyze_video(video_temp_file.name)
        with open(results_temp_file.name, 'w') as f:
            json.dump(results, f)

        # push result to s3
        video_key_path = os.path.dirname(video_s3_key)  # this is project_name/split
        result_key = os.path.join(os.path.dirname(video_key_path), step_name, video_name + '.json')
        logger.debug("Pushing results to s3 : {}/{}".format(video_s3_bucket, result_key))
        put_object_to_s3(results_temp_file.name, video_s3_bucket, result_key)

        # update dynamoDB document
        logger.debug("Updating doc on dynamoDB")
        for i in range(len(video_doc["process_steps"])):
            if video_doc["process_steps"][i]["step"] == step_name:
                video_doc["process_steps"][i]["state"] = "done"
                video_doc["process_steps"][i]["result_file"] = {"bucket": video_s3_bucket, "key": result_key}
                break
        send_video_info_to_dynamo_db(dyndb_region_id, dyndb_tableId, video_doc)

    except Exception as e:
        # update dynamoDB document
        for i in range(len(video_doc["process_steps"])):
            if video_doc["process_steps"][i]["step"] == step_name:
                video_doc["process_steps"][i]["state"] = "error"
                break
        send_video_info_to_dynamo_db(dyndb_region_id, dyndb_tableId, video_doc)
        raise e

    finally:
        # clean
        os.remove(video_temp_file.name)
        os.remove(results_temp_file.name)


if __name__ == "__main__":

    with open("variables.json") as f:
        params = json.load(f)

    current_detector = "human_detection"
    sqs_queue_name = params["aws_queues"][current_detector]
    module_parameters = params["human_detection"]

    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger = logging.getLogger("HumanDetectionAWSInterface")

    logger.info("Starting up. Connecting to SQS queue {}".format(sqs_queue_name))
    sqs_queue = None
    try:
        sqs = boto3.resource('sqs')
        sqs_queue = sqs.get_queue_by_name(QueueName=sqs_queue_name)
        logger.info("Connected to SQS")
    except Exception as e:
        logger.error("Could not connect to SQS : {}. Exiting".format(e))
        exit()

    logger.info("Instantiating analyzer")
    try:
        video_analyzer = VideoAnalyzer(**module_parameters)
    except Exception as e:
        logger.error("Could not instantiate analyzer : {}. Exiting".format(e))
        exit()

    logger.info("Entering main loop")
    run = True
    while run:
        for message in sqs_queue.receive_messages(WaitTimeSeconds=10):
            try:
                message_body = json.loads(message.body)
                logger.info("Received new message : {}".format(message_body))
                # manage stop command
                if "command" in message_body:
                    if message_body["command"] == "stop":
                        logging.info("Received stop command, exiting")
                        run = False
                        break

                video_id = message_body["VideoId"]
                video_file = message_body["s3"]

                process_video(video_id, video_analyzer,
                              video_file["bucket"], video_file["key"],
                              params["dynamodb"]["region"], params["dynamodb"]["table_id"],
                              logger)
            except Exception as e:
                logger.error("Error processing message: {}".format(e))

            # Let the queue know that the message is processed
            message.delete()

    video_analyzer.close()
