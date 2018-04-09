#!/usr/bin/env bash

# Manage parameters
SCRIPT_DIR=`dirname $0`
APP_DIR=`dirname ${SCRIPT_DIR}`
ENV_NAME="app"

# Set utilities
function submit {
    "$@"
    local exit_status=$?
    if [ $exit_status -ne 0 ]
    then
        echo -e "[`date '+%Y-%m-%d %H:%M:%S'`][\033[0;31mERROR\033[0m] in subcommand $@" >&2
        exit exit_status
    fi
}

# Install conda
echo -e "[`date '+%Y-%m-%d %H:%M:%S'`][\e[34mINFO\033[0m] Install conda"
mkdir -p ${APP_DIR}/envs
submit wget -q https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh --directory-prefix ${APP_DIR}/envs > /dev/null
submit chmod u+x ${APP_DIR}/envs/Miniconda3-latest-Linux-x86_64.sh > /dev/null
submit ${APP_DIR}/envs/Miniconda3-latest-Linux-x86_64.sh -bf -p ${APP_DIR}/envs/miniconda3 > /dev/null
export PATH=${APP_DIR}/envs/miniconda3/bin:$PATH

# Add channels in conda
echo -e "[`date '+%Y-%m-%d %H:%M:%S'`][\e[34mINFO\033[0m] Add repositories to conda"
submit conda config --add channels conda-forge > /dev/null
submit conda config --add channels bioconda > /dev/null

# Create environment with dependencies
echo -e "[`date '+%Y-%m-%d %H:%M:%S'`][\e[34mINFO\033[0m] Create app environment"
submit ${SCRIPT_DIR}/create_env.sh ${APP_DIR}/envs/miniconda3/envs/${ENV_NAME}/bin ${ENV_NAME}

# Create environment mSINGS
echo -e "[`date '+%Y-%m-%d %H:%M:%S'`][\e[34mINFO\033[0m] Install mSINGS"
submit ${SCRIPT_DIR}/install_msings.sh ${APP_DIR}/envs
submit ln -s ${APP_DIR}/jflow/workflows/MSI/bin/run_msings.py ${APP_DIR}/envs/msings/scripts

# Update application.properties
echo -e "[`date '+%Y-%m-%d %H:%M:%S'`][\e[34mINFO\033[0m] Update applications.properties"
submit sed 's/###APP_FOLDER###/${APP_DIR}/g' ${APP_DIR}/jflow/application.properties.tpl > ${APP_DIR}/jflow/application.properties

# Execute install test
echo -e "[`date '+%Y-%m-%d %H:%M:%S'`][\e[34mINFO\033[0m] Test install"
##########################submit source activate ${ENV_NAME}
##########################${APP_DIR}/jflow/bin/jflow_cli.py msi --R1 --R2 ...
##########################source deactivate

echo -e "[`date '+%Y-%m-%d %H:%M:%S'`][\e[92mSUCCESS\033[0m] Installation completed successfully"
