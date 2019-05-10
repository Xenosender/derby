#!/usr/bin/env bash

for f in *.sh; do
    if [[ "$f" != "download_all_models.sh" ]]; then
        ./$f
    fi;
done;