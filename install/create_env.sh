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
        exit $exit_status
    fi
}

# Create environment
submit conda create --yes --quiet --name ${ENV_NAME} python=3.6 > /dev/null
submit source activate ${ENV_NAME}

submit conda config --add channels conda-forge > /dev/null
submit conda config --add channels bioconda > /dev/null
submit conda install --yes --quiet scipy=1.2.0=py36he2b7bc3_0 > /dev/null
submit conda install --yes --quiet scikit-learn=0.20.0=py36h22eb022_1 > /dev/null
submit conda install --yes --quiet cherrypy=14.0.1=py36_0 > /dev/null
submit conda install --yes --quiet pysam=0.14.1=py36hae42fb6_1 > /dev/null
submit conda install --yes --quiet git=2.20.1=pl526hc122a05_1001 > /dev/null
submit conda install --yes --quiet make=4.2.1=h14c3975_2004 > /dev/null
submit conda install --yes --quiet bwa=0.7.17=h84994c4_5 > /dev/null
submit conda install --yes --quiet samtools=1.8=h46bd0b3_5 > /dev/null
submit conda install --yes --quiet cutadapt=1.18=py36h14c3975_1 > /dev/null
submit ${SCRIPT_DIR}/install_makeflow.sh ${ENV_BIN} > /dev/null
submit conda install --yes --quiet openjdk=8.0.152=h46b5887_1 > /dev/null

source deactivate
