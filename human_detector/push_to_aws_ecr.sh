#!/usr/bin/env bash

# script to push a docker image to ECR
# 	- creates a repository in ECR (ie a naming convention that will group all versions of a same docker image)
# 	- saves the config of this repository in a local file
#	- tags the local image with the correct naming convention for ECR
#	- logs with docker to the ECR repository
# 	- pushes the image
#
#	Arguments
#		1) name of the image (opt. default : "derby/human_detector")
#		2) name of the file to save the ECR repo conf to (opt. default : "aws_ecr_conf.json")

image_name=$1
if [[ -z "$image_name" ]]; then
    image_name="derby/human_detector"
fi

aws_ecr_configfile=$2
if [[ -z "$aws_ecr_configfile" ]]; then
    aws_ecr_configfile="aws_ecr_conf.json"
fi

ret=$(aws ecr create-repository --repository-name ${image_name})
aws ecr describe-repositories --repository-names ${image_name} > ${aws_ecr_configfile}
# get repo uri and tag image to push
ecr_repo_uri=$(cat ${aws_ecr_configfile} | jq -r '.repositories[0].repositoryUri')
docker tag ${image_name} ${ecr_repo_uri}
# login to ecr repo in docker
login_cmd=$(aws ecr get-login --no-include-email)
${login_cmd}

#push image
docker push ${ecr_repo_uri}