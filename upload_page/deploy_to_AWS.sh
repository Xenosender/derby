#!/usr/bin/env bash

WEBPAGE_S3_BUCKET="cp-derby-uploadpage"

echo -e "\e[35m\e[1mUploading webpages to s3\e[21m"
aws s3 sync . s3://${WEBPAGE_S3_BUCKET} --delete