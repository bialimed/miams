#!/usr/bin/env bash

# Manage parameters
TEST_DIR=`dirname $0`
APP_DIR=`dirname ${TEST_DIR}`
ENV_NAME="MIAmS"

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
if [ -d ${TEST_DIR}/out_model ]
then
    rm -rf ${TEST_DIR}/out_model
fi

# Execute msi detection test
submit source activate ${ENV_NAME}

submit mkdir -p ${TEST_DIR}/bank
if [ ! -f ${TEST_DIR}/bank/Homo_sapiens.GRCh37.75.dna.chromosome.14.fa.bwt ]
then
    submit wget -q ftp://ftp.ensembl.org/pub/release-75/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.75.dna.chromosome.14.fa.gz --directory-prefix ${TEST_DIR}/bank > /dev/null
    submit gzip -d ${TEST_DIR}/bank/Homo_sapiens.GRCh37.75.dna.chromosome.14.fa.gz > /dev/null
    submit bwa index ${TEST_DIR}/bank/Homo_sapiens.GRCh37.75.dna.chromosome.14.fa > /dev/null
fi

submit mkdir -p ${TEST_DIR}/out_detection
submit ${APP_DIR}/envs/msings/scripts/create_intervals.py \
  --input-bed ${APP_DIR}/test/data/targets.bed \
  --output ${APP_DIR}/test/out_model/intervals.tsv

submit ${APP_DIR}/jflow/bin/jflow_cli.py miamslearn \
  --R1 ${APP_DIR}/test/data/stable/spl001_S19_L001_R1.fastq.gz \
  --R2 ${APP_DIR}/test/data/stable/spl001_S19_L001_R2.fastq.gz \
  --R1 ${APP_DIR}/test/data/unstable/spl002_S13_L001_R1.fastq.gz \
  --R2 ${APP_DIR}/test/data/unstable/spl002_S13_L001_R2.fastq.gz \
  --min-support-samples 1 \
  --annotations ${APP_DIR}/test/data/learn_annot.tsv \
  --targets ${APP_DIR}/test/data/targets.bed \
  --genome-seq ${APP_DIR}/test/bank/Homo_sapiens.GRCh37.75.dna.chromosome.14.fa \
  --intervals ${APP_DIR}/test/data/intervals.tsv \
  --output-baseline ${APP_DIR}/test/out_model/baseline.tsv \
  --output-training ${APP_DIR}/test/out_model/models.json \
  --output-log ${APP_DIR}/test/out_model/baseline_log.txt > /dev/null

submit rm -rf ${TEST_DIR}/out_model

source deactivate
