import json
import os
import tempfile

import cv2
import boto3


###############
# S3 functions
###############

def get_object_from_s3(region_id, bucket_name, key, local_filename):
    """
    download file from s3 to local file. You must have access rights

    :param bucket_name: name of the bucket
    :param key: key of the file to get in the bucket
    :param local_filename: path to file to write
    :return: None
    """
    s3 = boto3.resource('s3', region_name=region_id)
    try:
        res = s3.Bucket(bucket_name).download_file(key, local_filename)
    except Exception as e:
        if hasattr(e, "message"):
            e.message = "S3 : " + e.message
        raise e


def put_object_to_s3(region_id, local_filename, bucket_name, key):
    """
    upload file to s3 from local file. You must have access rights

    :param local_filename: path to file to write
    :param bucket_name: name of the bucket
    :param key: key of the file to write in the bucket
    :return: None
    """
    s3 = boto3.client('s3', region_name=region_id)
    try:
        s3.upload_file(local_filename, bucket_name, key)
    except Exception as e:
        if hasattr(e, "message"):
            e.message = "S3 : " + e.message
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
        raise Exception('DynamoDB : Could not find document in dynamoDB with request {}'.format(search_keys))
    except Exception as e:
        if hasattr(e, "message"):
            e.message = "DynamoDB : " + e.message
        raise e


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
    try:
        response = table.put_item(Item=json.loads(json.dumps(document), parse_float=decimal.Decimal))
        return response
    except Exception as e:
        if hasattr(e, "message"):
            e.message = "DynamoDB : " + e.message
        raise e


#####################
# Main functions
#####################

def create_movie_from_result_file(video_file, result_file, output_video_file):
    with open(result_file) as f:
        results = json.load(f)
        frames_results = results["frames"]

    cap = cv2.VideoCapture(video_file)

    out_video = cv2.VideoWriter(output_video_file,
                                cv2.VideoWriter_fourcc(*'MP4V'),
                                cap.get(cv2.CAP_PROP_FPS),
                                (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))

    current_frame_ind = 0

    while True:
        if not frames_results:
            break

        r, img = cap.read()
        if not r:
            break

        current_frame_ind += 1
        while frames_results and frames_results[0]["frame_index"] < current_frame_ind:
            frames_results.pop(0)
        if not frames_results or frames_results[0]["frame_index"] > current_frame_ind:
            continue

        im_height, im_width, _ = img.shape
        frame_values = frames_results[0]
        out_img = img.copy()
        for key in frame_values:
            if key.lower() in ["human", "face"]:
                for box, score in zip(frame_values[key]["boxes"], frame_values[key]["scores"]):
                    cv2.rectangle(out_img,
                                  (int(box[1] * im_width), int(box[0] * im_height)),
                                  (int(box[3] * im_width), int(box[2] * im_height)),
                                  (255, 0, 0) if key.lower() == "human" else (0, 255, 0), 2)
                    cv2.putText(out_img,
                                "{:.2f}".format(score),
                                (int(box[1] * im_width) + 2, int(box[0] * im_height) + 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.2, (0, 0, 255), 1, cv2.LINE_4)

        out_video.write(out_img)
        # cv2.imwrite('test.jpg', out_img)

    out_video.release()


def create_control_movie( video_id, step_name,
                          video_s3_region_id, video_s3_bucket, video_s3_key,
                          dyndb_region_id, dyndb_tableId,
                          logger):

    # get doc from dynamodb
    logger.info("Getting doc from dynamoDB")
    video_doc = get_video_info_from_dynamo_db(dyndb_region_id, dyndb_tableId, {"VideoId": int(video_id)})

    result_file = None
    for i in range(len(video_doc["process_steps"])):
        if video_doc["process_steps"][i]["step"] == step_name:
            if "result_file" in video_doc["process_steps"][i]:
                result_file = video_doc["process_steps"][i]["result_file"]
            break

    if result_file is None:
        logger.error('Could not find path to result file for doc {}, step {}'.format(video_id, step_name))

    video_temp_file = tempfile.NamedTemporaryFile(delete=False)
    results_temp_file = tempfile.NamedTemporaryFile(delete=False)
    output_video_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')

    try:
        # get video from s3
        logger.info("Getting video from S3: {}/{}".format(video_s3_bucket, video_s3_key))
        get_object_from_s3(video_s3_region_id, video_s3_bucket, video_s3_key, video_temp_file.name)
        video_name = os.path.basename(video_s3_key)
        video_name = video_name[:video_name.rfind('.')]

        # get result file
        logger.info("Getting result file from S3: {}/{}".format(result_file["bucket"], result_file["key"]))
        get_object_from_s3(video_s3_region_id, result_file["bucket"], result_file["key"], results_temp_file.name)

        # generate video
        logger.info("Generating control video")
        create_movie_from_result_file(video_temp_file.name, results_temp_file.name, output_video_temp_file.name)

        # push result to s3
        video_key_path = os.path.dirname(video_s3_key)  # this is project_name/split
        result_key = os.path.join(os.path.dirname(video_key_path), "control_videos", step_name, video_name + '.mp4')
        logger.info("Pushing control video to s3 : {}/{}".format(video_s3_bucket, result_key))
        put_object_to_s3(video_s3_region_id, results_temp_file.name, video_s3_bucket, result_key)

        # update dynamoDB document
        logger.info("Updating doc on dynamoDB")
        for i in range(len(video_doc["process_steps"])):
            if video_doc["process_steps"][i]["step"] == step_name:
                video_doc["process_steps"][i]["state"] = "done"
                video_doc["process_steps"][i]["control_video"] = {"bucket": video_s3_bucket, "key": result_key}
                break
        send_video_info_to_dynamo_db(dyndb_region_id, dyndb_tableId, video_doc)

    except Exception as e:
        raise e

    finally:
        # clean
        os.remove(video_temp_file.name)
        os.remove(results_temp_file.name)
        os.remove(output_video_temp_file.name)


if __name__ == "__main__":
    # input_file = "/home/cyril/PycharmProjects/Derby/human_detector/src/example/derby_testmatch_1_firstjam.mp4"
    # result_file = "/home/cyril/PycharmProjects/Derby/human_detector/src/test.json"
    # out_file = "/home/cyril/PycharmProjects/Derby/results_viewer/test.mp4"
    #
    # create_movie_from_result_file(input_file, result_file, out_file)

    create_control_movie()