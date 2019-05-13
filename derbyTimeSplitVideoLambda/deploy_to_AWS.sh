#!/usr/bin/env bash

AWS_LAMBDAFUNCTION_NAME="derbyTimeSplitVideoLambda"

mkdir lambda_package
echo -e "\e[35m\e[1muninstall boto3\e[21m"
pipenv uninstall boto3
echo -e "\e[35m\e[1mcreate lambda package\e[21m"
pipenv lock -r > requirements.txt
pip install -r requirements.txt --no-deps -t lambda_package

echo -e "\e[35m\e[1mDownloading and adding ffmpeg exe\e[21m"
if [[ ! -f ffmpeg-release-amd64-static.tar.xz ]]; then
    wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
fi
mkdir ffmpeg-release-amd64-static && tar -xJf ffmpeg-release-amd64-static.tar.xz -C ffmpeg-release-amd64-static --strip-components 1
mv ffmpeg-release-amd64-static/ffmpeg lambda_package/
#zip -g lambda_package.zip ffmpeg-release-amd64-static/ffprobe

cd lambda_package
zip -r ../lambda_package.zip *
cd ..
zip -g lambda_package.zip lambda_function.py
zip -g lambda_package.zip variables.json

echo -e "\e[35m\e[1mupdate lambda function on AWS\e[21m"
aws lambda update-function-code --function-name ${AWS_LAMBDAFUNCTION_NAME} --zip-file fileb://lambda_package.zip
echo -e "\e[35m\e[1mclean artifacts\e[21m"
rm -rf lambda_package lambda_package.zip requirements.txt
rm -rf ffmpeg-release-amd64-static
echo -e "\e[35m\e[1mreinstall boto3\e[21m"
pipenv install boto3