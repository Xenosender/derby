#!/usr/bin/env bash

BUILD=0

while getopts ":b" arg; do
  case $arg in
    b) BUILD=1;;
  esac
done

docker_tag="derby/human_detector"
aws_ecr_configfile="aws_ecr_conf.json"

# build image
if [[ ${BUILD} == 1 ]]; then
    ./build_dockerfile.sh ${docker_tag}
fi


./push_to_aws_ecr.sh ${docker_tag} ${aws_ecr_configfile}

./register_and_run_task.sh