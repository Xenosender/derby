#!/usr/bin/env bash

# automatically gets all .sh files that are not itself and calls them

for f in *.sh; do
    if [[ "$f" != "download_all_models.sh" ]]; then
        ./$f
    fi;
done;