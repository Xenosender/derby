#!/usr/bin/env bash

aws cloudformation deploy --stack-name ecs-cluster-derby --capabilities CAPABILITY_NAMED_IAM --template-file ecs-cluster-def.yml