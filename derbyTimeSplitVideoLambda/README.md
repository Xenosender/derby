LAMBDA FUNCTION PROJECT TO SPLIT AN UPLOADED VIDEO TO X-SECONDS-LONG VIDEOS
===================

This is lambda function which:
    - get a video from s3
    - split it in subvideos
    - insert information about all videos in DynamoDB
    - upload all new videos to s3
    
It is launched when a new video is uploaded to the chosen s3 bucket.

It is serverless, efficient, scalable and reactive (the function is triggered each time a video is uploaded to the source s3 bucket)



Files
-----
- _lambda_function.py_ : the python code of the lambda. AWS entry point is lambda_function.lambda_handler
- _Pipfile_ : configuration file for pipenv
- _variables.json_ : json file with variables used in the projects (symbolic link to ../variables.json)
- _deploy_to_AWS.sh_ : script to deploy the lambda


Relevant variables
-----------------

```json
    "video_split": {
		"output_bucket": "cp-derby-bucket",                         // output bucket for the new videos
		"output_key_prefix": "project/{video_name}/split",          // configurable path in the bucket
		"output_files_duration_in_sec": 30                          // length of new files, in sec
	},
	"dynamodb": {
		"region": "eu-west-1",                                      // region of the DynamoDB table
		"table_id": "my_derby_project"                              // DynamoDB table name
	}
```

DynamoDB documents inserted
---------------

```json
{
    "VideoId": int_id,                              // randomly generated primary key
    "process_step": "timesplit",                    // step at which the video was created ("upload" or "timesplit", at the moment)
    "creation_time": "date_isoformat",              // creation time
    "bucket": "storing_bucket",                     // storage bucket
    "key": "storing_path",                          // storage key
    "name": "storing_name",                         // storage name
    "extension": "video_file_extension",            // file extension
    "size": [W, H],                                 // image size, as ints
    "fps": 30,                                      // nb of images / sec
    "duration": 30,                                 // duration of the video file
    "audio": true,                                  // does it have an audio track ?
    "parent_video": video_id,                       // only if the video has been generated from a previous one
    "sub_videos": [video_id1, video_id2, ...]       // only if the video has been used to generate new videos
}
```


Local Configuration
------------
You need to have the AWS util installed, and Pipenv
To develop locally, use "pipenv install"


AWS setup
---------
- **S3** : if you're using an output bucket which is not the input bucket, you'll have to create a new one (private)
- **lambda**: create a lambda with the name you want, in python 3.6. It should create the associated IAM role.
    - If you plan on using the current code, you have to change the timeout to several minutes, and the min ram above 300Mo
    - you can configure the trigger from there, from your input S3 bucket:
        - use the event type "ObjectCreated"
        - if your output bucket is the same as the input bucket, set the prefix to your input directory
- **DynamoDB** : create a table with VideoId (Number) as primary key
- **IAM**: add inline policies to the role associated to the lambda:
    - readObject permission on input bucket
    - WriteObject permission on output bucket


Deployment
----------
To deploy a lambda, it must come zipped with all its dependencies. However, locally we need boto3 to connect to AWS services, but on AWS it is on the python path.
For this reason, the script:
    
- uninstalls boto3 locally
- installs all dependencies in a local directory
- zips it and adds code to it
- uploads to AWS lambda
- cleans
- reinstall boto3 locally
    

To setup the name of the lambda to update, change AWS_LAMBDAFUNCTION_NAME in the deployment script.


Possible improvements
--------------------
We should make sure that this process has not been already done for a given video. This is more or less done by the auto-trigger on new videos uploaded, but it would be cleaner to ask dynamoDB.

We should also check when inserting the document in DynamoDB that there is no primary key conflict






Author : Cyril Poulet, cyril.poulet@centraliens.net
April 2019