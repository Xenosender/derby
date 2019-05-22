#!/usr/bin/env bash

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