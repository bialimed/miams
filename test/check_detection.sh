#!/usr/bin/env bash

# Manage parameters
TEST_DIR=`dirname $0`
APP_DIR=`dirname ${TEST_DIR}`
ENV_NAME="app"

# Set utilities
function submit {
    "$@"
    local exit_status=$?
    if [ $exit_status -ne 0 ]
    then
        echo -e "[`date '+%Y-%m-%d %H:%M:%S'`][\033[0;31mERROR\033[0m] in subcommand $@" >&2
        exit $exit_status
    fi
}

# Clean previous install
if [ -d ${TEST_DIR}/out_detection ]
then
    rm -rf ${TEST_DIR}/out_detection
fi

# Execute msi detection test
submit source activate ${ENV_NAME}

submit mkdir -p ${TEST_DIR}/out_detection
submit wget -q ftp://ftp.ensembl.org/pub/release-75/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.75.dna.chromosome.14.fa.gz --directory-prefix ${TEST_DIR}/out_detection > /dev/null
submit gzip -d ${TEST_DIR}/out_detection/Homo_sapiens.GRCh37.75.dna.chromosome.14.fa.gz > /dev/null
submit bwa index ${TEST_DIR}/out_detection/Homo_sapiens.GRCh37.75.dna.chromosome.14.fa > /dev/null
submit ${APP_DIR}/jflow/bin/jflow_cli.py msi \
--R1 ${TEST_DIR}/data/instable/I17G01612_S13_L001_R1.fastq.gz \
--R2 ${TEST_DIR}/data/instable/I17G01612_S13_L001_R2.fastq.gz \
--R1 ${TEST_DIR}/data/stable/I17G01744_S19_L001_R1.fastq.gz \
--R2 ${TEST_DIR}/data/stable/I17G01744_S19_L001_R2.fastq.gz \
--targets ${TEST_DIR}/data/msi.bed \
--intervals ${TEST_DIR}/data/msi_intervals.tsv \
--baseline ${TEST_DIR}/data/MSI_BASELINE.tsv \
--genome-seq ${TEST_DIR}/out_detection/Homo_sapiens.GRCh37.75.dna.chromosome.14.fa \
--output-dir ${TEST_DIR}/out_detection > /dev/null
submit rm -rf ${TEST_DIR}/out_detection

source deactivate
