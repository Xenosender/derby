Docker images with human detector function in video clips
===================

This is project which:

- subscribe to a message queue on AWS SQS
- when getting a notification:
    - get a video from s3
    - get the corresponding document from dynamoDB
    - detects humans and faces in every frame of the video
    - stores the resul file in S3
    - updates the document in dynamoDB

This is more an example of how to deploy a service on AWS via a docker container using GPUs, though there are a few interesting tricks in the python code:
    - how to use a factory
    - how to load and use a trained tensorflow model
    - how to correctly connect and call aws services via boto3 library

This project explains how to build a docker container using GPUs (via the nvidia docker runtime), push it on the AWS docker registry ECR, then create a task description to run the description and launch the task on the cluster.

This supposes that you have a cluster deployed on ECS (See _cluster_deployement.md_ at the root of the global project), launched, with at least one instance of p2xlarge type running.
At the moment, running an EC2 cluster is mandatory, as Fargate does not yet supports GPU requirements.

If you don't want to use GPU, the changes to make are:
    - change tensorflow-gpu to tensorflow : tensorflow-gpu needs CUDA to run, and will not load if CUDA libs are not found
    - deploy the task on fargate, or change the EC2 instances to a smaller type with no GPU (less costly)


IMPORTANT : 
    - the versions chosen for TF-gpu needs CUDA 9. The base image for the container is chosen for that.
    - this project DOES NOT ENTER IN AWS FREE TIER!! it will incur costs for :
        - storing images in ECR (the free tier is very small)
        - running EC2 p2xlarge instances  (around 1$/hour)

    If you want to stay in the free tier, remove gpu requirements.


Files
-----
Code:

- _src/detector.py_ : base Detector class for images processing
- _src/human_detector.py_ : HumanDetector class for images processing
- _src/face_detector.py_ : FaceDetector class for images processing
- _src/video_analyzer.py_ : VideoAnalyzer class that applies detectors to frames in a video
- _src/aws_interface.py_ : entrypoint to apply VideoAnalyzer to video while using interfaces to AWS services
- _src/variables.json_ : json file with variables used in the projects (symbolic link to ../variables.json)
- _src/utils.py_ : utility functions
- _src/model/get_faster_rcnn_resnet101_coco.sh_ : bash script to download and extract the model for the HumanDetector
- _src/model/get_mobilenet_ssd_widerface.sh_ : bash script to download and extract the model for the FaceDetector
- _src/model/download_all_models.sh_ : bash script to call all other download scripts
- _src/requirements.txt_ : needed python packages

Deployment:

- _Dockerfile_ : build description file for docker image
- _.dockerfile_ : ignore rules for file copying during docker image build
- _build_dockerfile.sh_ : build script for docker image
- _push_to_aws_ecr.sh_ : script to push docker image to AWS ECR (docker registry)
- _human_detector_taskdef.json_ : json file describing the aws ECS task (for aws ecs register-task-definition)
- _human_detector_taskdef.yml_ : yaml file describing the aws ECS task (for aws cloudformation deploy)
- _register_and_run_task.sh_ : script to push the task description to AWS ECS and run it on the running cluster
- _deply_to_aws.sh_ : script to apply all steps of the deployment (docker build, docker push, task registry and task run)
- _run_docker_local.sh_ : helper script to test your docker image locally


Relevant variables
-----------------

```json
    "aws_region": "eu-west-1",
    "video_split": {
		"output_bucket": "cp-derby-bucket",                         // output bucket for the videos to process
	},
    "aws_queues": {
        "human_detection": "derby-call-humandetector"               // SQS queue to use
    },
    "human_detection": {
        "detectors": [
            ["HumanDetector", {"min_detection_score": 0.4, "max_batch_size": 5}],
            ["FaceDetector", {"min_detection_score": 0.4, "max_batch_size": 5}]
        ],
        "frame_ratio": 0.2
    },
	"dynamodb": {
		"region": "eu-west-1",                                      // region of the DynamoDB table
		"table_id": "my_derby_project"                              // DynamoDB table name
	}
```

The "human_detection" part is designed to be passed as argument to VideoAnalyzer : json keys correspond to the class instantiation arguments.
Same for the detectors, which are tuples (detector_name, detector instantiation args)

See the classes in src/ to get the description of the possible arguments.


DynamoDB documents changes
---------------

Start of the process : creates the "human_detection" step with the status "running"

```json
{
    "VideoId": int_id,
    "process_steps": [ 
      ...
      {"step": "human_detector", "state": "running"}
}
```

End of the process : changes the "human_detection" step to "done" and adds path to result file. If error, state is set to "error"

```json
{
    "VideoId": int_id,
    "process_steps": [
      ...
      {"step": "human_detector", "state": "done", "result_file": {"bucket": ..., "key": ...}}
    ],
}
```

Local Configuration
------------
You need to have the AWS util installed. You also need to have docker installed, with the [nvidia runtime](https://github.com/NVIDIA/nvidia-docker)

This code also needs to have CUDA 9 installed (for GPU usage), otherwise you have to change tensorflow-gpu to tensorflow.

IMPORTANT : pipenv does not work with tensorflow-gpu, as it does not manage correctly the paths to CUDA and CuDNN.
Therefore here only a requirements.txt is given. You have to have CUDA 9.0 and CuDNN installed


AWS setup
---------
This project needs access to **s3**, **dynamoDB**, **SQS**, **ECS**, **ECR** (and in the future **cloudformation**)

Regarding the access policies:
- ECS and ECR are called directly by you, so you have to have personnally the rights to call these services
- s3, dynamoDB and SQS are called by the container :
    - the buckets, table and queue are existing resources from the "derbyTimeSplitVideoLambda" and awsQueueManagement projects. Refer to it if you don't already have these.
    - locally, the container uses your own credentials, so you need to have rights to access these resources
    - remotely, the rights are provided by the *derbyEcsTaskExecutionRole* deployed at the same time as the cluster by cloudformation (see _cluster_deployement.md_ at the root of the global project). Refer to the cluster deployment files for more info


Deployment
----------

The deployment is in 3 parts :

- pushing the container to the AWS conntainer registry (ECR)
- creating the task definition
- running the task

Before starting the deployement, you have to create the container locally, and test it. To manage te connection to AWS you have to mount the relevant directory (~/.aws) in your container. See _run_local_docker.sh_ for an example.

To create the task definition, at the moment you have to use the json file: it supports the "resourceRequirements" field which is necessary to declare the need for a GPU, but does not support templating.
The yaml file is a cloudformation template which supports templating, but cloudformation does not support "resourceRequirements" at the moment (support is declared comming in the months to come). That is why you cannot use it at the moment.

IMPORTANT : 
- "resourceRequirements" says that the task needs a GPU, but that is only translated to the fact that ECS will use the nvidia runtime when launching the container for the task. 
- "placementConstraints" forces ECS to launch the container on a specific type of instance (here, one with GPUs), but NOT that your task requires access to the GPU

YOU NEED BOTH to make sure that your container will be on an instance which has GPUs, and that container can actually access them.

Finally, to run the task, you need to have your cluster deployed and running (ie with at least one instance running and registered in the cluster). See _cluster_deployement.md_ at the root of the global project.


Possible improvements
--------------------



Author : Cyril Poulet, cyril.poulet@centraliens.net
May 2019