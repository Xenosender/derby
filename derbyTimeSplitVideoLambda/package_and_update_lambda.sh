#!/usr/bin/env bash

mkdir lambda_package
echo "uninstall boto3"
pipenv uninstall boto3
echo "create lambda package"
pipenv lock -r > requirements.txt
pip install -r requirements.txt --no-deps -t lambda_package
cd lambda_package
zip -r ../lambda_package.zip *
cd ..
zip -g lambda_package.zip lambda_function.py
zip -g lambda_package.zip variables.json
echo "update lambda function on AWS"
aws lambda update-function-code --function-name derbyTimeSplitVideoLambda --zip-file fileb://lambda_package.zip
echo "clean artifacts"
rm -rf lambda_package lambda_package.zip requirements.txt
echo "reinstall boto3"
pipenv install boto3