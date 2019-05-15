#!/usr/bin/env bash

docker run -it \
        --runtime=nvidia \
        -v ~/.aws:/root/.aws \
        derby/human_detector