#!/usr/bin/env bash

# Manage parameters
if [ $# -eq 0 ]
then
    echo -e "[\033[0;31mERROR\033[0m] The installion directory must be specified: $0 INSTALL_DIR" >&2
    exit 1
fi
INSTALL_DIR=$1
SOFT_VERSION="v3.4"

# Clean previous install
if [ -d ${INSTALL_DIR}/msings ]
then
    rm -rf ${INSTALL_DIR}/msings
fi

# Install msings
alias python=python2.7

cd ${INSTALL_DIR} && \
git clone https://bitbucket.org/uwlabmed/msings.git && \
cd msings && \
git checkout ${SOFT_VERSION} && \
PYTHON=`which python2` dev/bootstrap.sh
