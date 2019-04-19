# Author : Cyril Poulet, cyril.poulet@centraliens.net
# April 2019

import json
import os
import tempfile
import time
import datetime
import math
import random
import decimal
import boto3
from moviepy.editor import VideoFileClip



###############
# S3 functions
###############

def get_video_from_s3(bucket_name, key, local_filename):
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


def put_video_to_s3(local_filename, bucket_name, key):
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

CUSTOM_EPOCH = 1300000000000 # artificial epoch


def generate_row_id():
    """
    generate random ID

    :return: int
    """
    ts = time.time() - CUSTOM_EPOCH
    randid = math.floor(random.random() * 512)
    ts = ts * 64  # bit-shift << 6
    return (ts * 512) + (randid % 512)


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if abs(o) % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


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
    print("PutItem succeeded:")
    print(json.dumps(response, indent=4, cls=DecimalEncoder))


###############
# split functions
###############

def transfer_and_split_in_sequences(input_s3_bucket, input_file_key, output_s3_bucket, output_key_prefix,
                                    subvid_duration_in_sec, dynamodb_region_id, dynamodb_tableId):
    """
    Gets a video from s3, split it in subvids based on duration, and uploads all resulting files back to s3. You must have access rights

    :param input_s3_bucket: name of the s3 bucket to get input video from
    :param input_file_key: key of the file to get in the bucket
    :param output_s3_bucket: name of the s3 bucket to write to
    :param output_key_prefix: prefix to use for the keys of the files to write in the bucket
                              should contain "{video_name}", which will be replaced by the input video name.
                              final keys will be : output_key_prefix.format(video_name)/video_name_i.video_format
    :param subvid_duration_in_sec: length of subvids in seconds. Last vid may be shorter
    :return: None
    """

    # get video from s3
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    get_video_from_s3(input_s3_bucket, input_file_key, temp_file.name)
    video_name = os.path.basename(input_file_key)
    video_format = video_name[video_name.rfind('.') + 1:]
    video_name = video_name[:video_name.rfind('.')]

    print("starting time-based split")
    video_object = VideoFileClip(temp_file.name)
    upload_video_information = {
        "VideoId": generate_row_id(),
        "process_step": "upload",
        "creation_time": datetime.datetime.now().isoformat(),
        "bucket": input_s3_bucket,
        "key": input_file_key,
        "name": video_name,
        "extension": video_format,
        "size": video_object.size,
        "fps": video_object.fps,
        "duration": video_object.duration,
        "audio": (video_object.audio is not None),
        "sub_videos": []
    }
    send_video_info_to_dynamo_db(dynamodb_region_id, dynamodb_tableId, upload_video_information)

    current_start = 0
    current_index = 0

    while current_start < video_object.duration:
        # get new subvid and write it to s3
        new_subvid = video_object.subclip(current_start,
                                          min(current_start + subvid_duration_in_sec, video_object.duration))
        output_key = os.path.join(output_key_prefix.format(video_name=video_name),
                                  "{}_{}.{}".format(video_name, current_index, video_format))
        subvid_temp = tempfile.NamedTemporaryFile(delete=False, prefix="/tmp/", suffix='.{}'.format(video_format))
        new_subvid.write_videofile(subvid_temp.name)
        put_video_to_s3(subvid_temp.name, output_s3_bucket, output_key)

        subvideo_information = {
            "VideoId": generate_row_id(),
            "process_step": "timesplit",
            "creation_time": datetime.datetime.now().isoformat(),
            "bucket": output_s3_bucket,
            "key": output_key,
            "name": os.path.basename(output_key),
            "extension": video_format,
            "size": new_subvid.size,
            "fps": new_subvid.fps,
            "duration": new_subvid.duration,
            "audio": (new_subvid.audio is not None),
            "parent_video": upload_video_information["VideoId"]
        }
        send_video_info_to_dynamo_db(dynamodb_region_id, dynamodb_tableId, subvideo_information)
        upload_video_information["sub_videos"].append(subvideo_information["VideoId"])

        os.remove(subvid_temp.name)
        current_index += 1
        current_start += subvid_duration_in_sec

    send_video_info_to_dynamo_db(dynamodb_region_id, dynamodb_tableId, upload_video_information)
    # clean
    os.remove(temp_file.name)
    print("split finished")


#################
# Lambda handler
#################

def lambda_handler(event, context):
    """
    AWS lambda entry point

    :param event: trigger event (json)
    :param context: trigger context (json)
    :return: dict
    """
    print("Incoming Event: ", event)
    input_bucket = event['Records'][0]['s3']['bucket']['name']
    input_key = event['Records'][0]['s3']['object']['key']
    message = "File is uploaded in - {} -> {}".format(input_bucket, input_key)
    print(message)

    with open("variables.json") as f:
        params = json.load(f)

    current_dir = os.getcwd()
    try:
        print("moving to /tmp")
        os.chdir('/tmp')
        transfer_and_split_in_sequences(input_bucket, input_key,
                                        params["video_split"]["output_bucket"], params["video_split"]["output_key_prefix"],
                                        params["video_split"]["output_files_duration_in_sec"],
                                        params["dynamodb"]["region"], params["dynamodb"]["table_id"])
        # TODO implement
        return_dict = {
            'statusCode': 200,
            'body': json.dumps('Done splitting {} !'.format(input_key))
        }

    except Exception as e:
        print(e)
        return_dict = {
            'statusCode': 1,
            'body': json.dumps('Error processing {} : {}'.format(input_key, e))
        }
    finally:
        os.chdir(current_dir)

    return return_dict


if __name__ == "__main__":

    with open("variables.json") as f:
        params = json.load(f)

    test_key = "upload/public_3.mp4"

    test_event = {
        "Records": [
            {
                "eventVersion": "2.0",
                "eventSource": "aws:s3",
                "awsRegion": "eu-west-1",
                "eventTime": "1970-01-01T00:00:00.000Z",
                "eventName": "ObjectCreated:Put",
                "userIdentity": {
                    "principalId": "EXAMPLE"
                },
                "requestParameters": {
                    "sourceIPAddress": "127.0.0.1"
                },
                "responseElements": {
                    "x-amz-request-id": "EXAMPLE123456789",
                    "x-amz-id-2": "EXAMPLE123/5678abcdefghijklambdaisawesome/mnopqrstuvwxyzABCDEFGH"
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "testConfigRule",
                    "bucket": {
                        "name": params["video_upload"]["upload_bucket_name"],
                        "ownerIdentity": {
                            "principalId": "EXAMPLE"
                        },
                        "arn": "arn:aws:s3:::{}".format(params["video_upload"]["upload_bucket_name"])
                    },
                    "object": {
                        "key": test_key,
                        "size": 1024,
                        "eTag": "0123456789abcdef0123456789abcdef",
                        "sequencer": "0A1B2C3D4E5F678901"
                    }
                }
            }
        ]
    }

    lambda_handler(test_event, None)
