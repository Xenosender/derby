#!/usr/bin/env bash

# register task in ecs
aws ecs register-task-definition --cli-input-json file://human_detector_taskdef.json
# cloudformation templates are cleaner but resourceRequirements is not yet supported by cloudformation
#aws cloudformation deploy --stack-name ecs-task-derby-human-detector --template-file human_detector_taskdef.yml


# run task on cluster
export cluster=$(aws cloudformation describe-stacks --stack-name ecs-cluster-derby --query 'Stacks[0].Outputs[?OutputKey==`ClusterName`].OutputValue' --output text)
echo "Current Cluster is : $cluster"
aws ecs run-task \
        --cluster $cluster \
        --task-definition derbyHumanDetectionTask