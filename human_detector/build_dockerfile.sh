#!/usr/bin/env bash

image_name=$1
if [[ -z "$image_name" ]]; then
    image_name="derby/human_detector"
fi

original_variables_files=$(readlink -f src/variables.json)

rm src/variables.json
cp $original_variables_files src/variables.json

docker build -t ${image_name}:latest .

rm src/variables.json
ln -s $original_variables_files src/variables.json