#!/usr/bin/env bash

# This script builds the docker image, pushes it to AWS ECR, then registers the task in ECS and runs it.
# if '-nb' is passed as argument, the build is not done and the last generated docker image will be pushed

BUILD=1

while getopts ":nb" arg; do
  case $arg in
    b) BUILD=0;;
  esac
done

docker_tag="derby/human_detector"
aws_ecr_configfile="aws_ecr_conf.json"

# build image
if [[ ${BUILD} == 1 ]]; then
    ./build_dockerfile.sh ${docker_tag}
fi

# push to ECR
./push_to_aws_ecr.sh ${docker_tag} ${aws_ecr_configfile}

# register and run task
./register_and_run_task.sh