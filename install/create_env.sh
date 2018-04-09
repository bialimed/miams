#!/usr/bin/env bash

# Manage parameters
if [ $# -eq 0 ]
then
    echo -e "[\033[0;31mERROR\033[0m] The installion directory and environment name must be specified: $0 ENV_BIN ENV_NAME"
    exit 1
fi
SCRIPT_DIR=`dirname $0`
ENV_BIN=$1
ENV_NAME=$2

# Set utilities
function submit {
    "$@"
    local exit_status=$?
    if [ $exit_status -ne 0 ]
    then
        echo -e "[\033[0;31mERROR\033[0m] in subcommand $@" >&2
        exit exit_status
    fi
}

# Create environment
submit conda create --yes --name ${ENV_NAME} > /dev/null
submit source activate ${ENV_NAME}

submit conda install --yes --quiet git > /dev/null
submit conda install --yes --quiet make > /dev/null
submit conda install --yes --quiet bwa==0.7.8 > /dev/null
submit conda install --yes --quiet samtools==1.8 > /dev/null
submit conda install --yes --quiet cutadapt==1.9.1 > /dev/null
submit conda install --yes --quiet scipy==1.0.1 > /dev/null
submit conda install --yes --quiet cherrypy==14.0.1 > /dev/null
submit conda install --yes --quiet openjdk==8.0.152 > /dev/null
submit ${SCRIPT_DIR}/install_makeflow.sh ${ENV_BIN} > /dev/null

source deactivate
