#!/usr/bin/env bash


current_dir=$(pwd)
for dir in ${current_dir}/*/     # list directories in the form "/tmp/dirname/"
do
    if [[ -f ${dir}deploy_to_AWS.sh ]]; then
        cd ${dir};
        echo -e "\e[35m\e[1mdeploying ${dir}\e[21m";
        ./deploy_to_AWS.sh;
        cd ${current_dir}
    fi
done