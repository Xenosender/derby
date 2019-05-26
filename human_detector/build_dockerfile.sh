#!/usr/bin/env bash

# First argument in the call, if there is an argument, is used as image name for the built image
image_name=$1
if [[ -z "$image_name" ]]; then
    image_name="derby/human_detector"
fi

# Due to the fact that we link the variables from the root to each subproject, but that docker scope is limited to the working directory,
# we replace the symnnolic link by a hard copy for the duration of the build, then remake it a symbolic link
original_variables_files=$(readlink -f src/variables.json)

rm src/variables.json
cp $original_variables_files src/variables.json

docker build -t ${image_name}:latest .

rm src/variables.json
ln -s $original_variables_files src/variables.json