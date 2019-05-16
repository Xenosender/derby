#!/usr/bin/env bash

aws cloudformation deploy --stack-name ecs-cluster-derby --template-file ecs-cluster-def.yml --capabilities CAPABILITY_IAM