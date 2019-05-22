#!/usr/bin/env bash

image_name=$1
if [[ -z "$image_name" ]]; then
echo "hop"
    image_name="derby/human_detector"
fi

original_variables_files=$(readlink -f variables.json)

rm variables.json
cp $original_variables_files variables.json

docker build -t ${image_name} .

rm variables.json
ln -s ../variables.json variables.json