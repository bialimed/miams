#!/usr/bin/env python3
#
# Copyright (C) 2019 IUCT-O
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2019 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import os
import re
import sys
import time
import shutil
import hashlib
import logging
import argparse
import subprocess
from statistics import median
from sklearn.utils import shuffle

APP_FOLDER = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
LIB_DIR = os.path.join(APP_FOLDER, "jflow", "workflows", "lib")
sys.path.insert(0, LIB_DIR)

from anacore.sv import HashedSVIO, SVIO
from anacore.bed import getAreas
from anacore.sequenceIO import FastqIO


########################################################################
#
# FUNCTIONS
#
########################################################################
def getLogInfo(log_path):
    """
    Return information form MIAmS_tag logging file.

    :param log_path: Path to the MIAmS_tag logging file.
    :type log_path: str
    :return: The logging information.
    :rtype: dict
    """
    log_info = dict()
    with open(log_path) as FH_in:
        for line in FH_in:
            line = line.strip()
            tag, value = line.split("=", 1)
            log_info[tag] = value
            if value == "":
                log_info[tag] = None
            elif tag.endswith("_time"):
                log_info[tag] = int(float(value))
    return log_info


def getSplFromLibName(lib_name):
    """
    Return sample name from library name.

    :param lib_name: The library name.
    :type lib_name: str
    :return: The sample name.
    :rtype: str
    """
    return lib_name.split("_")[0]


def getLibNamefromFileName(filename):
    """
    Return library name from fastq filename.

    :param filename: The fastq filename.
    :type filename: str
    :return: The library name.
    :rtype: str
    """
    libname = None
    match = re.match("^([^_]+_S\d+)_.+.fastq.gz$", filename)
    if match is not None:  # spl-1_S1_L001_R1_001.fastq.gz
        libname = match.group(1)
    else:  # spl-1_R1.fastq.gz
        libname = filename.split("_")[0]
    return libname


def getLibFromDataFolder(data_folder):
    """
    Return libraries information from folder containing fastq.

    :param data_folder: Path to the folder containing fastq.
    :type data_folder: str
    :return: The list of libraries. Each element is a dictionary containing the following keys: name, spl_name, R1, R2.
    :rtype: list
    """
    libraries = []
    for run_folder_name in os.listdir(data_folder):
        run_folder_path = os.path.join(data_folder, run_folder_name)
        for filename in os.listdir(run_folder_path):
            if filename.endswith(".fastq.gz") and "_R1" in filename:
                filepath = os.path.join(run_folder_path, filename)
                lib_name = getLibNamefromFileName(filename)
                libraries.append({
                    "name": lib_name,
                    "spl_name": getSplFromLibName(lib_name),
                    "R1": filepath,
                    "R2": filepath.replace("_R1", "_R2")
                })
    return libraries


def getStatus(in_annotations, samples):
    """
    Return status by locus by sample.

    :param in_annotations: Path to the file containing status by locus by sample (format: TSV).
    :type in_annotations: str
    :param samples: List of samples names.
    :type samples: list
    :return: Status by locus by sample.
    :rtype: dict
    """
    status_by_spl = {}
    samples = set(samples)
    with HashedSVIO(in_annotations, title_starter="") as FH:
        for record in FH:
            spl_name = getSplFromLibName(record["sample"])
            if spl_name in samples:
                status_by_spl[spl_name] = {key: value for key, value in record.items() if key not in ["sample", "sample_status"]}
                status_by_spl[spl_name]["sample"] = record["sample_status"]
    for spl in samples:
        if spl not in status_by_spl:
            raise Exception("Sample {} has no expected data.".format(spl))
    return status_by_spl


def execCommand(cmd):
    """
    Execute command in MIAmS environment.

    :param cmd: The command to execute.
    :type cmd: list
    """
    # Manage virtualenv
    env_activate_cmd = [
        "source",
        os.path.join(APP_FOLDER, "envs", "miniconda3", "bin", "activate"),
        "MIAmS"
    ]
    env_deactivate_cmd = [
        "source",
        os.path.join(APP_FOLDER, "envs", "miniconda3", "bin", "deactivate")
    ]
    # Create command
    cmd = " && ".join([
        " ".join(env_activate_cmd),
        " ".join(cmd),
        " ".join(env_deactivate_cmd)
    ])
    # Execute command
    subprocess.check_call(
        cmd,
        shell=True
    )


def train(libraries, annotations_file, design_folder, out_baseline, out_models, out_log, args):
    """
    Execute MIAmS_learn.

    :param libraries: The list of libraries. Each element is a dictionary containing the following keys: name, spl_name, R1, R2.
    :type libraries: list
    :param annotations_file: Path to the file containing status by locus by sample (format: TSV).
    :type annotations_file: str
    :param design_folder: Path to the folder containing targets.bed, intervales.tsv and genome.fa.
    :type design_folder: str
    :param out_baseline: Path to the ouputted baseline.
    :type out_baseline: str
    :param out_models: Path to the ouputted model.
    :type out_models: str
    :param out_log: Path to the ouputted log.
    :type out_log: str
    :param args: Arguments of the script.
    :type args: argparse.NameSpace
    """
    train_cmd = list(map(str, [
        os.path.join(APP_FOLDER, "jflow", "bin", "jflow_cli.py"), "miamslearn",
        "--min-support-reads", args.learn_min_support_reads,
        "--min-support-samples", 9,
        "--max-mismatch-ratio", 0.25,
        "--min-pair-overlap", 40,
        "--min-zoi-overlap", 12,
        "--targets", os.path.join(design_folder, "targets.bed"),
        "--intervals", os.path.join(design_folder, "intervals.tsv"),
        "--genome-seq", os.path.join(design_folder, "genome.fa"),
        "--output-baseline", out_baseline,
        "--output-training", out_models,
        "--output-log", out_log,
        "--annotations", annotations_file
    ]))
    if os.path.exists(os.path.join(design_folder, "trimmed_R1.fasta")):
        train_cmd.extend([
            "--R1-end-adapter", os.path.join(design_folder, "trimmed_R1.fasta"),
            "--R2-end-adapter", os.path.join(design_folder, "trimmed_R2.fasta")
        ])
    for lib in libraries:
        train_cmd.extend([
            "--R1", lib["R1"],
            "--R2", lib["R2"]
        ])
    execCommand(train_cmd)


def predict(libraries, design_folder, in_baseline, in_models, out_folder, args):
    """
    Execute MIAmS_tag.

    :param libraries: The list of libraries. Each element is a dictionary containing the following keys: name, spl_name, R1, R2.
    :type libraries: list
    :param annotations_file: Path to the file containing status by locus by sample (format: TSV).
    :type annotations_file: str
    :param design_folder: Path to the folder containing targets.bed, intervales.tsv and genome.fa.
    :type design_folder: str
    :param in_baseline: Path to the baseline (format: TSV).
    :type in_baseline: str
    :param in_models: Path to the model (format: JSON).
    :type in_models: str
    :param out_folder: Path to the outputted folder.
    :type out_folder: str
    :param args: Arguments of the script.
    :type args: argparse.NameSpace
    """
    predict_cmd = list(map(str, [
        os.path.join(APP_FOLDER, "jflow", "bin", "jflow_cli.py"), "miamstag",
        "--min-support-reads", args.tag_min_support_reads,
        "--random-seed", 42,
        "--max-mismatch-ratio", 0.25,
        "--min-pair-overlap", 40,
        "--min-zoi-overlap", 12,
        "--loci-consensus-method", args.consensus_method,
        "--min-voting-loci", args.min_voting_loci,
        "--instability-ratio", args.instability_ratio,
        "--instability-count", args.instability_count,
        "--undetermined-weight", args.undetermined_weight,
        ("--locus-weight-is-score" if args.locus_weight_is_score else ""),
        "--targets", os.path.join(design_folder, "targets.bed"),
        "--intervals", os.path.join(design_folder, "intervals.tsv"),
        "--baseline", in_baseline,
        "--models", in_models,
        "--genome-seq", os.path.join(design_folder, "genome.fa"),
        "--output-dir", out_folder
    ]))
    if os.path.exists(os.path.join(design_folder, "trimmed_R1.fasta")):
        predict_cmd.extend([
            "--R1-end-adapter", os.path.join(design_folder, "trimmed_R1.fasta"),
            "--R2-end-adapter", os.path.join(design_folder, "trimmed_R2.fasta")
        ])
    for lib in libraries:
        predict_cmd.extend([
            "--R1", lib["R1"],
            "--R2", lib["R2"]
        ])
    execCommand(predict_cmd)


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description="Launch classification on evaluation datasets.")
    parser.add_argument('--random-state', type=int, default=42, help="The random seed used to select samples in datasets. [Default: %(default)s]")
    parser.add_argument('--nb-jobs', nargs='+', type=int, default=[1, 25, 50, 100], help="The number of jobs submitted in parallel. [Default: %(default)s]")
    parser.add_argument('--nb-samples', nargs='+', type=int, default=[1, 25, 50, 100], help="The number of samples in test datasets. [Default: %(default)s]")
    parser.add_argument('--nb-tests', type=int, default=5, help="The number of test on different samples for each nb_samples and nb_jobs. [Default: %(default)s]")
    parser.add_argument('--nb-in-train', type=int, default=100, help="The number of samples in training dataset. [Default: %(default)s]")
    parser.add_argument('--reference-method', default="ngs", help="The prefix of the columns in status_by_spl.tsv used as expected values (example: ngs, electro). [Default: %(default)s]")
    parser.add_argument('--default-classifier', default="SVCPairs", help='The classifier used in MIAmS. [Default: %(default)s]')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    # Loci classification
    group_loci = parser.add_argument_group('Loci classification')
    group_loci.add_argument('--tag-min-support-reads', default=100, type=int, help='The minimum numbers of reads for determine the status. [Default: %(default)s]')
    group_loci.add_argument('--learn-min-support-reads', default=400, type=int, help='The minimum numbers of reads for use loci in learning step. [Default: %(default)s]')
    # Sample classification
    group_spl = parser.add_argument_group('Sample classification')
    group_spl.add_argument('--consensus-method', default='ratio', choices=['count', 'majority', 'ratio'], help='Method used to determine the sample status from the loci status. Count: if the number of unstable is upper or equal than instability-count the sample will be unstable otherwise it will be stable ; Ratio: if the ratio of unstable/determined loci is upper or equal than instability-ratio the sample will be unstable otherwise it will be stable ; Majority: if the ratio of unstable/determined loci is upper than 0.5 the sample will be unstable, if it is lower than stable the sample will be stable. [Default: %(default)s]')
    group_spl.add_argument('--min-voting-loci', default=3, type=int, help='Minimum number of voting loci (stable + unstable) to determine the sample status. If the number of voting loci is lower than this value the status for the sample will be undetermined. [Default: %(default)s]')
    group_spl.add_argument('--instability-ratio', default=0.2, type=float, help='[Only with consensus-method = ratio] If the ratio unstable/(stable + unstable) is superior than this value the status of the sample will be unstable otherwise it will be stable. [Default: %(default)s]')
    group_spl.add_argument('--instability-count', default=3, type=int, help='[Only with consensus-method = count] If the number of unstable loci is upper or equal than this value the sample will be unstable otherwise it will be stable. [Default: %(default)s]')
    # Sample classification score
    group_score = parser.add_argument_group('Sample prediction score')
    group_score.add_argument('--undetermined-weight', default=0.0, type=float, help='[Used for all the classifiers different from MSINGS] The weight of undetermined loci in sample prediction score calculation. [Default: %(default)s]')
    group_score.add_argument('--locus-weight-is-score', action='store_true', help='[Used for all the classifiers different from MSINGS] Use the prediction score of each locus as wheight of this locus in sample prediction score calculation. [Default: %(default)s]')
    # Inputs
    group_input = parser.add_argument_group('Inputs')
    group_input.add_argument('--data-folder', required=True, help="The folder containing data to process. It must contain design/, raw_by_run/ and status_by_spl.tsv.")
    group_input.add_argument('--work-folder', default=os.getcwd(), help="The working directory. [Default: %(default)s]")
    # Outputs
    group_output = parser.add_argument_group('Outputs')
    group_output.add_argument('-m', '--output-metrics', default="exec_time.tsv", help='Path to the table containing execution times by execution parameters (format: TSV). [Default: %(default)s]')
    args = parser.parse_args()

    # Parameters
    annotation_path = os.path.join(args.data_folder, "status_by_spl.tsv")
    raw_folder = os.path.join(args.data_folder, "raw_by_run")
    design_folder = os.path.join(args.data_folder, "design")
    if not os.path.exists(args.work_folder):
        os.makedirs(args.work_folder)

    # Logger
    logging.basicConfig(format='%(asctime)s -- [%(filename)s][pid:%(process)d][%(levelname)s] %(message)s')
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    log.info("Command: " + " ".join(sys.argv))

    # Load data
    log.info("Load dataset")
    librairies = getLibFromDataFolder(raw_folder)
    status_by_spl = getStatus(annotation_path, [lib["spl_name"] for lib in librairies])
    for lib in librairies:
        lib["status"] = status_by_spl[lib["spl_name"]]
    loci = set(locus.name for locus in getAreas(os.path.join(design_folder, "targets.bed")))

    # Get nb nt
    log.info("Get the number of nucleotids by sample")
    for spl in librairies:
        spl["nb_nt"] = 0
        spl["nb_frag"] = 0
        for fastq in [spl["R1"], spl["R2"]]:
            with FastqIO(fastq) as FH_in:
                for rec in FH_in:
                    spl["nb_nt"] += len(rec.string)
                    spl["nb_frag"] += 1

    # Process assessment
    app_config = os.path.join(APP_FOLDER, "jflow", "application.properties")
    app_config_bck = app_config + ".bck"
    shutil.copyfile(app_config, app_config_bck)
    try:
        is_first = True
        for nb_spl in args.nb_samples:  # [1, 50, 100]
            for eval_idx in range(args.nb_tests):  # 10
                samples = shuffle(librairies, random_state=args.random_state + eval_idx + nb_spl)
                for nb_jobs in args.nb_jobs:  # [1, 50, 100]
                    log.info("Process test #{} on {} samples with {} jobs".format(eval_idx + 1, nb_spl, nb_jobs))
                    # Create datasets
                    train_idx = range(nb_spl + 1, nb_spl + 1 + args.nb_in_train)
                    test_idx = range(nb_spl + 1)
                    train_samples = [spl for idx, spl in enumerate(samples) if idx in train_idx]
                    test_samples = [spl for idx, spl in enumerate(samples) if idx in test_idx]
                    dataset_id = hashlib.md5(",".join([spl["name"] for spl in test_samples]).encode('utf-8')).hexdigest()
                    # Temp file
                    baseline_path = os.path.join(args.work_folder, "baseline_dataset-{}.tsv".format(dataset_id))
                    models_path = os.path.join(args.work_folder, "models_dataset-{}.tsv".format(dataset_id))
                    learn_log_path = os.path.join(args.work_folder, "log_dataset-{}.tsv".format(dataset_id))
                    out_folder = os.path.join(args.work_folder, "out_dataset-{}".format(dataset_id))
                    # Process learn and tag
                    train(train_samples, annotation_path, design_folder, baseline_path, models_path, learn_log_path, args)
                    with open(app_config_bck) as FH_in:
                        with open(app_config, "w") as FH_out:
                            for line in FH_in:
                                FH_out.write(line.replace("limit_submission = 100", "limit_submission = " + str(nb_jobs)))
                    start_time = time.time()
                    predict(test_samples, design_folder, baseline_path, models_path, out_folder, args)
                    end_time = time.time()
                    # Write results and dataset
                    out_mode = "w" if is_first else "a"
                    with SVIO(args.output_metrics, out_mode) as FH_out:
                        FH_out.titles = ["datatset_id", "nb_loci", "nb_spl", "median_nb_nt", "sum_nb_nt", "median_nb_reads", "sum_nb_reads", "nb_jobs", "exec_time"]
                        FH_out.write([
                            dataset_id,
                            len(loci),
                            nb_spl,
                            median([spl["nb_nt"] for spl in test_samples]),
                            sum([spl["nb_nt"] for spl in test_samples]),
                            median([spl["nb_frag"] * 2 for spl in test_samples]),
                            sum([spl["nb_frag"] * 2 for spl in test_samples]),
                            nb_jobs,
                            (end_time - start_time) / 60
                        ])
                    is_first = False
                    # Clean tmp
                    for tmp_file in [baseline_path, models_path, learn_log_path, out_folder]:
                        if os.path.isdir(tmp_file):
                            shutil.rmtree(tmp_file)
                        else:
                            os.remove(tmp_file)
    finally:
        if os.path.exists(app_config_bck):
            shutil.move(app_config_bck, app_config)
    log.info("End of job")
