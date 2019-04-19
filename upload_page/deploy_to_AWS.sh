#!/usr/bin/env bash

echo -e "\e[35m\e[1mUploading webpages to s3\e[21m"
aws s3 sync . s3://cp-derby-uploadpage --delete