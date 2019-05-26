#!/usr/bin/env bash

#	This script registers the ECS task definition, then runs it
#	If the task definition already exists, it just creates a new revision that replaces the previous one
#
#	To run the task, your EC2 cluster must be started and a p2xlarge instance running.
#
#	At the moment the task definition is a json file not templated (because 'aws ecs register-task-definition' does not support templating)
# 	You can also deploy task definition with cloudformation (with can be templated), unfortunately at the moment it does not support 'resourceRequirements', used to 
#	express the need of a GPU. Therefore the yml file is given, but does not work yet. 
#	This missing support is currently on tracks for the next versions of aws command line tool


# register task in ecs
aws ecs register-task-definition --cli-input-json file://human_detector_taskdef.json
# For later use...
# aws cloudformation deploy --stack-name ecs-task-derby-human-detector --template-file human_detector_taskdef.yml


# run task on cluster
export cluster=$(aws cloudformation describe-stacks --stack-name ecs-cluster-derby --query 'Stacks[0].Outputs[?OutputKey==`ClusterName`].OutputValue' --output text)
echo "Current Cluster is : $cluster"
aws ecs run-task \
        --cluster $cluster \
        --task-definition derbyHumanDetectionTask