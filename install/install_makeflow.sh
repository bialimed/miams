#!/usr/bin/env bash

# Manage parameters
if [ $# -eq 0 ]
then
    echo -e "[\033[0;31mERROR\033[0m] The installion directory must be specified: $0 INSTALL_DIR" >&2
    exit 1
fi
INSTALL_DIR=$1
SOFT_VERSION="6.1.6"
USER_PWD=$PWD

# Clean previous install
if [ -d ${INSTALL_DIR}/cctools ]
then
    rm -rf ${INSTALL_DIR}/cctools
fi

# Install makeflow
cd ${INSTALL_DIR} && \
git clone https://github.com/cooperative-computing-lab/cctools.git && \
cd cctools && \
git checkout release/${SOFT_VERSION} && \
./configure --prefix ./build --without-system-sand --without-system-apps --without-system-allpairs --without-system-wavefront --without-system-ftp-lite --without-system-chirp --without-system-grow --without-system-umbrella --without-system-parrot --without-system-doc --without-system-prune --without-system-resource_monitor && \
make install && \
cd ${USER_PWD} && \
mv ${INSTALL_DIR}/cctools/build/bin/makeflow ${INSTALL_DIR} && \
rm -rf ${INSTALL_DIR}/cctools
