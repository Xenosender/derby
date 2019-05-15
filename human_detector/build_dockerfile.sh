#!/usr/bin/env bash

original_variables_files=$(readlink -f variables.json)

rm variables.json
cp $original_variables_files variables.json

docker build -t derby/human_detector .

rm variables.json
ln -s ../variables.json variables.json