#!/usr/bin/env bash

wget http://download.tensorflow.org/models/object_detection/faster_rcnn_inception_v2_coco_2018_01_28.tar.gz
tar -xzvf faster_rcnn_inception_v2_coco_2018_01_28.tar.gz --wildcards  */model.ckpt.* --strip-components 1
rm faster_rcnn_inception_v2_coco_2018_01_28.tar.gz
for f in model.ckpt.*; do mv "$f" "$(echo "$f" | sed s/model.ckpt/faster_rcnn_resnet101_coco/)"; done