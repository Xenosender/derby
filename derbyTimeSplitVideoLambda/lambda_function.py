import json
import boto3
import os
import tempfile
from moviepy.editor import VideoFileClip


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


def transfer_and_split_in_sequences(input_s3_bucket, input_file_key, output_s3_bucket, output_key_prefix, subvid_duration_in_sec):
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
    video_format = video_name[video_name.rfind('.')+1:]
    video_name = video_name[:video_name.rfind('.')]

    print("starting time-based split")
    video_object = VideoFileClip(temp_file.name)
    current_start = 0
    current_index = 0

    while current_start < video_object.duration:
        # get new subvid and write it to s3
        new_subvid = video_object.subclip(current_start, min(current_start+subvid_duration_in_sec, video_object.duration))
        output_key = os.path.join(output_key_prefix.format(video_name=video_name), "{}_{}.{}".format(video_name, current_index, video_format))
        subvid_temp = tempfile.NamedTemporaryFile(delete=False, prefix="/tmp/", suffix='.{}'.format(video_format))
        new_subvid.write_videofile(subvid_temp.name)
        put_video_to_s3(subvid_temp.name, output_s3_bucket, output_key)
        os.remove(subvid_temp.name)
        current_index += 1
        current_start += subvid_duration_in_sec

    # clean
    os.remove(temp_file.name)
    print("split finished")


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

    try:
        print("moving to /tmp")
        os.chdir('/tmp')
        transfer_and_split_in_sequences(input_bucket, input_key,
                                        params["video_split"]["output_bucket"], params["video_split"]["output_key_prefix"],
                                        params["video_split"]["output_files_duration_in_sec"])
        # TODO implement
        return {
            'statusCode': 200,
            'body': json.dumps('Done splitting {} !'.format(input_key))
        }

    except Exception as e:
        print(e)
        return {
            'statusCode': 1,
            'body': json.dumps('Error processing {} : {}'.format(input_key, e))
        }


if __name__ == "__main__":

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
                        "name": "cp-derby-bucket",
                        "ownerIdentity": {
                            "principalId": "EXAMPLE"
                        },
                        "arn": "arn:aws:s3:::cp-derby-bucket"
                    },
                    "object": {
                        "key": "upload/public_3.mp4",
                        "size": 1024,
                        "eTag": "0123456789abcdef0123456789abcdef",
                        "sequencer": "0A1B2C3D4E5F678901"
                    }
                }
            }
        ]
    }

    lambda_handler(test_event, None)
