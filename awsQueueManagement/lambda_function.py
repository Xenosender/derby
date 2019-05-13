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


def lambda_handler(event, context):
    print(event)

    with open("variables.json") as f:
        params = json.load(f)

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

        current_process_step = updated_values["process_steps"]["L"][-1]["M"]
        step_name = current_process_step["step"]["S"]
        step_status = current_process_step["state"]["S"]
        try:
            current_process_step_ind = params["process_steps"].index(step_name)
        except ValueError as e:
            print('Process step not found : {}'.format(step_name))
            continue

        if step_status.lower() != "done":
            print('Found state for step {} is not "done". skipping'.format(step_name))
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


# if __name__ == "__main__":
#
#     with open("variables.json") as f:
#         params = json.load(f)
#
#     test_event = {
#         "Records": [
#             {
#                 "eventID": "f537de3f871d5a99533630503b72e77c",
#                 "eventName": "MODIFY",
#                 "eventVersion": "1.1",
#                 "eventSource": "aws:dynamodb",
#                 "awsRegion": "eu-west-1",
#                 "dynamodb": {
#                     "ApproximateCreationDateTime": 1557769415.0,
#                     "Keys": {
#                         "VideoId": {
#                             "N": "-42547355050985230"
#                         }
#                     },
#                     "NewImage": {
#                         "bucket": {
#                             "S": "cp-derby-bucket"
#                         },
#                         "creation_time": {
#                             "S": "2019-05-13T17:23:39.443548"
#                         },
#                         "duration": {
#                             "N": "30"
#                         },
#                         "extension": {
#                             "S": "mp4"
#                         },
#                         "parent_video": {
#                             "N": "-42547355053242230"
#                         },
#                         "VideoId": {
#                             "N": "-42547355050985230"
#                         },
#                         "size": {
#                             "L": [
#                                 {
#                                     "N": "640"
#                                 },
#                                 {
#                                     "N": "360"
#                                 }
#                             ]
#                         },
#                         "fps": {
#                             "N": "30"
#                         },
#                         "name": {
#                             "S": "derby_testmatch_1_firstjam_0.mp4"
#                         },
#                         "audio": {
#                             "BOOL": True
#                         },
#                         "key": {
#                             "S": "project/derby_testmatch_1_firstjam/split/derby_testmatch_1_firstjam_0.mp4"
#                         },
#                         "process_steps": {
#                             "L": [
#                                 {
#                                     "M": {
#                                         "step": {
#                                             "S": "timesplit"
#                                         },
#                                         "state": {
#                                             "S": "done"
#                                         }
#                                     }
#                                 }
#                             ]
#                         }
#                     },
#                     "OldImage": {
#                         "bucket": {
#                             "S": "cp-derby-bucket"
#                         },
#                         "creation_time": {
#                             "S": "2019-05-13T17:23:39.443548"
#                         },
#                         "duration": {
#                             "N": "30"
#                         },
#                         "extension": {
#                             "S": "mp4"
#                         },
#                         "parent_video": {
#                             "N": "-42547355053242230"
#                         },
#                         "VideoId": {
#                             "N": "-42547355050985230"
#                         },
#                         "size": {
#                             "L": [
#                                 {
#                                     "N": "640"
#                                 },
#                                 {
#                                     "N": "360"
#                                 }
#                             ]
#                         },
#                         "fps": {
#                             "N": "30"
#                         },
#                         "name": {
#                             "S": "derby_testmatch_1_firstjam_0.mp4"
#                         },
#                         "audio": {
#                             "BOOL": True
#                         },
#                         "key": {
#                             "S": "project/derby_testmatch_1_firstjam/split/derby_testmatch_1_firstjam_0.mp4"
#                         },
#                         "process_steps": {
#                             "L": [
#                                 {
#                                     "M": {
#                                         "step": {
#                                             "S": "timesplit"
#                                         },
#                                         "state": {
#                                             "S": "done"
#                                         }
#                                     }
#                                 }
#                             ]
#                         }
#                     },
#                     "SequenceNumber": "109139700000000006052830023",
#                     "SizeBytes": 628,
#                     "StreamViewType": "NEW_AND_OLD_IMAGES"
#                 },
#                 "eventSourceARN": "arn:aws:dynamodb:eu-west-1:262436596026:table/my_derby_project/stream/2019-05-10T15:59:08.265"
#             }
#         ]
#     }
#     lambda_handler(test_event, None)
