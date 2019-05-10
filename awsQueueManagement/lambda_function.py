# Copyright 2019 Cyril Poulet, cyril.poulet@centraliens.net
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import boto3
import json

with open("variables.json") as f:
    params = json.load(f)


def lambda_handler(event, context):
    sqs = boto3.resource('sqs')

    #check that queues exists, create those that don't
    existing_queues = []
    for queue in sqs.queues.all():
        existing_queues.append(queue.attributes['QueueArn'].split(':')[-1])

    queues_to_create = set(params["aws_queues"].values()) - set(existing_queues)
    for queue_name in queues_to_create:
        print('Creating queue : {}'.format(queue_name))
        queue = sqs.create_queue(QueueName=queue_name)
        print("Created queue: {}".format(queue.url))

    # process event (dynamoDB update)
    for record in event["Records"]:
        record = record["dynamodb"]
        videoId = record['Keys']["VideoId"]["N"]
        updated_values = record["NewImage"]
        s3_bucket = updated_values["bucket"]["S"]
        s3_key = updated_values["key"]["S"]

        if s3_key[:7] != "project":
            print("Ignoring videoId {} because not in the 'project' directory".format(videoId))
            continue

        current_process_step = updated_values["process_step"]["S"]
        try:
            current_process_step_ind = params["process_steps"].index(current_process_step)
        except ValueError as e:
            print('Process step not found : {}'.format(current_process_step))
            continue

        if current_process_step == len(params["process_steps"]) - 1:
            continue
        next_process_step = params["process_steps"][current_process_step_ind+1]

        # print(videoId, s3_bucket, s3_key, current_process_step)
        target_queue_name = params["aws_queues"][next_process_step].lower()
        queue = sqs.get_queue_by_name(QueueName=target_queue_name)
        message_body = json.dumps({
            'VideoId': videoId,
            "s3": {
                "bucket": s3_bucket,
                "key": s3_key
            }
        })
        queue.send_message(MessageBody=message_body)
        print("sending {} to {}".format(message_body, target_queue_name))


if __name__ == "__main__":

    with open("variables.json") as f:
        params = json.load(f)

    test_event = {
      "Records": [
        {
          "eventID": "5d451b30988a1506157a9a710bd26446",
          "eventName": "MODIFY",
          "eventVersion": "1.1",
          "eventSource": "aws:dynamodb",
          "awsRegion": "eu-west-1",
          "dynamodb": {
            "ApproximateCreationDateTime": 1557504563,
            "Keys": {
              "VideoId": {
                "N": "-42547415307778220"
              }
            },
            "NewImage": {
              "bucket": {
                "S": "cp-derby-bucket"
              },
              "creation_time": {
                "S": "2019-04-22T10:34:20.909635"
              },
              "duration": {
                "N": "11.31"
              },
              "extension": {
                "S": "mp4"
              },
              "VideoId": {
                "N": "-42547415309978380"
              },
              "size": {
                "L": [
                  {
                    "N": "960"
                  },
                  {
                    "N": "540"
                  }
                ]
              },
              "fps": {
                "N": "30"
              },
              "name": {
                "S": "public_3"
              },
              "audio": {
                "BOOL": False
              },
              "process_step": {
                "S": "upload"
              },
              "sub_videos": {
                "L": [
                  {
                    "N": "-42547415307778220"
                  }
                ]
              },
              "key": {
                "S": "project/public_3/split/public_3_0.mp4"
              }
            },
            "OldImage": {
              "bucket": {
                "S": "cp-derby-bucket"
              },
              "creation_time": {
                "S": "2019-04-22T10:34:20.909635"
              },
              "duration": {
                "N": "11.31"
              },
              "extension": {
                "S": "mp4"
              },
              "VideoId": {
                "N": "-42547415309978380"
              },
              "size": {
                "L": [
                  {
                    "N": "960"
                  },
                  {
                    "N": "540"
                  }
                ]
              },
              "fps": {
                "N": "30"
              },
              "name": {
                "S": "public_3"
              },
              "audio": {
                "BOOL": True
              },
              "process_step": {
                "S": "upload"
              },
              "sub_videos": {
                "L": [
                  {
                    "N": "-42547415307778220"
                  }
                ]
              },
              "key": {
                "S": "upload/public_3.mp4"
              }
            },
            "SequenceNumber": "95331000000000006078371714",
            "SizeBytes": 426,
            "StreamViewType": "NEW_AND_OLD_IMAGES"
          },
          "eventSourceARN": "arn:aws:dynamodb:eu-west-1:262436596026:table/my_derby_project/stream/2019-05-10T15:59:08.265"
        }
      ]
    }

    lambda_handler(test_event, None)
