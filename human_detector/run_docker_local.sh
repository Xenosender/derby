#!/usr/bin/env bash

# simple command to start your docker image locally.
# ~/.aws contains your aws identification files, which will be used automatically by the boto3 library in the docker container
# nvidia runtime is mandatory to get GPU mappings

docker run -it \
        --runtime=nvidia \
        -v ~/.aws:/root/.aws \
        derby/human_detector