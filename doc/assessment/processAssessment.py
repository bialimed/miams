#!/usr/bin/env python3
#
# Copyright (C) 2018 IUCT-O
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
__copyright__ = 'Copyright (C) 2018 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '1.3.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import os
import re
import sys
import json
import shutil
import hashlib
import logging
import argparse
import subprocess
import pandas as pd
from sklearn.model_selection import ShuffleSplit

from anacore.msi import MSIReport, MSISample, LocusResPairsCombi, Status
from anacore.sv import HashedSVIO
from anacore.bed import getAreas


def getLogInfo(log_path):
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
    return lib_name.split("_")[0]

def getLibNamefromFileName(filename):
    libname = None
    match = re.match("^([^_]+_S\d+)_.+.fastq.gz$", filename)
    if match is not None:  # spl-1_S1_L001_R1_001.fastq.gz
        libname = match.group(1)
    else:  # spl-1_R1.fastq.gz
        libname = filename.split("_")[0]
    return libname

def getSammplesFromDataFolder(data_folder):
    samples = []
    for run_folder_name in os.listdir(data_folder):
        run_folder_path = os.path.join(data_folder, run_folder_name)
        for filename in os.listdir(run_folder_path):
            if filename.endswith(".fastq.gz") and "_R1" in filename:
                filepath = os.path.join(run_folder_path, filename)
                samples.append({
                    "name": getLibNamefromFileName(filename),
                    "R1": filepath,
                    "R2": filepath.replace("_R1", "_R2"),
                    "status": {}
                })
    return samples

def getStatusFromFile(status_file, in_separator="\t"):
    status_by_spl = dict()
    with open(status_file) as FH_status:
        titles = [elt.strip() for elt in FH_status.readline().split(in_separator)]
        if titles[0].startswith("#"):
            titles[0] = titles[0][1:]
        for line in FH_status:
            fields = {titles[idx]: elt.strip() for idx, elt in enumerate(line.split(in_separator))}
            if fields["sample_id"] in status_by_spl:
                raise Exception("Duplicated sample {} in {}.".format(fields["sample_id"], status_file))
            status_by_spl[fields["sample_id"]] = {"ngs": {}, "electro": {}, "MMR": {}}
            electro_res = status_by_spl[fields["sample_id"]]["electro"]
            ngs_res = status_by_spl[fields["sample_id"]]["ngs"]
            for locus_name in ["BAT25", "BAT26", "NR21", "NR22", "NR24", "NR27", "HT17"]:
                tag = "electro_" + locus_name + "_status"
                electro_res[locus_name] = (None if tag not in fields or fields[tag] == "" else fields[tag])
                tag = "ngs_" + locus_name + "_status"
                ngs_res[locus_name] = (None if tag not in fields or fields[tag] == "" else fields[tag])
            electro_res["sample"] = (None if fields["electro_sample_status"] == "" else fields["electro_sample_status"])
            ngs_res["sample"] = (None if fields["ngs_sample_status"] == "" else fields["ngs_sample_status"])
    return status_by_spl

def addExpectedStatus(samples, status_by_spl, ref_method="ngs"):
    for spl in samples:
        status_by_elt = status_by_spl[getSplFromLibName(spl["name"])]
        if status_by_elt[ref_method]["sample"] is None:
            raise Exception("Sample {} has no expected data.".format(getSplFromLibName(spl["name"])))
        spl["status"] = status_by_spl[getSplFromLibName(spl["name"])]

def samplesToAnnot(samples, loci_path, annot_path, ref_method="ngs"):
    loci = getAreas(loci_path)
    with HashedSVIO(annot_path, "w", title_starter="") as FH_out:
        FH_out.titles = ["sample"] + [locus.name for locus in loci]
        for spl in samples:
            record = {"sample": spl["name"]}
            for locus in loci:
                record[locus.name] = spl["status"][ref_method][locus.name]
            FH_out.write(record)

def execCommand(cmd):
    app_folder = "../.."
    # Manage virtualenv
    env_activate_cmd = [
        "source",
        os.path.join(app_folder, "envs", "miniconda3", "bin", "activate"),
        "MIAmS"
    ]
    env_deactivate_cmd = [
        "source",
        os.path.join(app_folder, "envs", "miniconda3", "bin", "deactivate")
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

def train(samples, annotations_file, design_folder, out_baseline, out_models, out_log, args):
    app_folder = "../.."
    train_cmd = list(map(str, [
        os.path.join(app_folder, "jflow", "bin", "jflow_cli.py"), "miamslearn",
        "--min-support-reads", args.learn_min_support_reads,
        "--max-mismatch-ratio", 0.25,
        "--min-pair-overlap", 40,
        "--min-zoi-overlap", 12,
        "--R1-end-adapter", os.path.join(design_folder, "trimmed_R1.fasta"),
        "--R2-end-adapter", os.path.join(design_folder, "trimmed_R2.fasta"),
        "--targets", os.path.join(design_folder, "targets.bed"),
        "--intervals", os.path.join(design_folder, "intervals.tsv"),
        "--genome-seq", os.path.join(design_folder, "genome.fa"),
        "--output-baseline", out_baseline,
        "--output-training", out_models,
        "--output-log", out_log,
        "--annotations", annotations_file
    ]))
    for spl in samples:
        train_cmd.extend([
            "--R1", spl["R1"],
            "--R2", spl["R2"]
        ])
    execCommand(train_cmd)

def predict(samples, design_folder, baseline, models, out_folder, args):
    app_folder = "../.."
    predict_cmd = list(map(str, [
        os.path.join(app_folder, "jflow", "bin", "jflow_cli.py"), "miamstag",
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
        "--R1-end-adapter", os.path.join(design_folder, "trimmed_R1.fasta"),
        "--R2-end-adapter", os.path.join(design_folder, "trimmed_R2.fasta"),
        "--targets", os.path.join(design_folder, "targets.bed"),
        "--intervals", os.path.join(design_folder, "intervals.tsv"),
        "--baseline", baseline,
        "--models", models,
        "--genome-seq", os.path.join(design_folder, "genome.fa"),
        "--output-dir", out_folder
    ]))
    for spl in samples:
        predict_cmd.extend([
            "--R1", spl["R1"],
            "--R2", spl["R2"]
        ])
    execCommand(predict_cmd)

def getResInfoTitles(loci_id_by_name):
    titles = [
        "dataset_id",
        "lib_name",
        "method_name",
        "spl_expected_status",
        "spl_observed_status",
        "spl_pred_score"
    ]
    for locus_name in sorted(loci_id_by_name):
        titles.extend([
            locus_name + "_expected_status",
            locus_name + "_observed_status",
            locus_name + "_pred_score",
            locus_name + "_pred_support"
        ])
    return titles

def getMethodResInfo(dataset_id, loci_id_by_name, reports, samples_by_name, method_name, res_method_name=None):
    if res_method_name is None:
        res_method_name = method_name
    dataset_res = []
    for curr_report in reports:
        expected = samples_by_name[curr_report.name.replace("_L001", "")]
        row = [dataset_id, curr_report.name, res_method_name]  # Dataset id, sample name and method
        row.extend([
            expected["sample"],  # expected
            curr_report.results[method_name].status,  # observed
            curr_report.results[method_name].score  # score
        ])
        for locus_name in sorted(loci_id_by_name):
            loci_pos = loci_id_by_name[locus_name]
            nb_support = None
            if method_name == "MSINGS":
                nb_support = 0
                for curr_peak in curr_report.loci[loci_pos].results[method_name].data["peaks"]:
                    nb_support += curr_peak["DP"]
            else:
                nb_support = curr_report.loci[loci_pos].results[method_name].getNbFrag() * 2
            row.extend([
                expected[locus_name],  # expected
                curr_report.loci[loci_pos].results[method_name].status,  # observed
                curr_report.loci[loci_pos].results[method_name].score,  # score
                nb_support  # support
            ])
        dataset_res.append(row)
    return dataset_res

def getResInfo(dataset_id, loci_id_by_name, reports, samples_by_name, methods):
    dataset_res = []
    for method_name in methods:
        dataset_res.extend(
            getMethodResInfo(dataset_id, loci_id_by_name, reports, samples_by_name, method_name)
        )
    return dataset_res

def getDatasetsInfoTitles(loci_id_by_name):
    titles = ["dataset_id", "dataset_md5"]
    # Train dataset
    titles.extend(["train_nb_spl", "train_nb_spl_stable", "train_nb_spl_unstable", "train_nb_spl_undetermined"])
    for locus_name in sorted(loci_id_by_name):
        titles.extend([
            "train_nb_" + locus_name + "_stable",
            "train_nb_" + locus_name + "_unstable",
            "train_nb_" + locus_name + "_undetermined"
        ])
    titles.append("learn_exec_time")
    # Test dataset
    titles.extend(["test_nb_spl", "test_nb_spl_stable", "test_nb_spl_unstable", "test_nb_spl_undetermined"])
    for locus_name in sorted(loci_id_by_name):
        titles.extend([
            "test_nb_" + locus_name + "_stable",
            "test_nb_" + locus_name + "_unstable",
            "test_nb_" + locus_name + "_undetermined"
        ])
    titles.append("tag_exec_time")
    # Samples
    titles.extend(["train_samples", "test_samples"])
    return titles

def getDatasetsInfo(dataset_id, dataset_md5, loci_id_by_name, models, reports, learn_log, tag_log, samples_by_name):
    train_status = [samples_by_name[spl.name.replace("_L001", "")] for spl in models]
    test_status = [samples_by_name[spl.name.replace("_L001", "")] for spl in reports]
    row = [dataset_id, dataset_md5]
    # Train dataset
    spl_status = [spl_status["sample"] for spl_status in train_status]
    row.extend([
        len(models),
        spl_status.count("MSS"),
        spl_status.count("MSI"),
        spl_status.count("Undetermined")
    ])
    for locus_name in sorted(loci_id_by_name):
        locus_status = [spl_status[locus_name] for spl_status in train_status]
        row.extend([
            locus_status.count("MSS"),
            locus_status.count("MSI"),
            locus_status.count("Undetermined")
        ])
    row.append(learn_log["End_time"] - learn_log["Start_time"])
    # Test dataset
    spl_status = [spl_status["sample"] for spl_status in test_status]
    row.extend([
        len(reports),
        spl_status.count("MSS"),
        spl_status.count("MSI"),
        spl_status.count("Undetermined")
    ])
    for locus_name in sorted(loci_id_by_name):
        locus_status = [spl_status[locus_name] for spl_status in test_status]
        row.extend([
            locus_status.count("MSS"),
            locus_status.count("MSI"),
            locus_status.count("Undetermined")
        ])
    row.append(tag_log["End_time"] - tag_log["Start_time"])
    # Samples
    row.extend([
        ", ".join([spl.name for spl in models]),
        ", ".join([spl.name for spl in reports])
    ])
    return row

def getMSISamples(in_folder):
    samples_res = list()
    for filename in os.listdir(in_folder):
        filepath = os.path.join(in_folder, filename)
        data = None
        with open(filepath) as FH:
            data = json.load(FH)[0]
        curr_spl = MSISample.fromDict(data)
        samples_res.append(curr_spl)
    return samples_res

def lociInitData(reports, src_method, dest_method):
    for curr_report in reports:
        for locus_id, locus in curr_report.loci.items():
            src_data = locus.results[src_method].data
            locus.results[dest_method] = LocusResPairsCombi(Status.none, None, src_data)

def submitAddClf(train_path, test_path, res_path, args, method_name, clf, clf_params=None):
    app_folder = "../.."
    cmd = list(map(str, [
        os.path.join(app_folder, "jflow", "workflows", "MIAmS_tag", "bin", "miamsClassify.py"),
        "--classifier", clf,
        "--random-seed", 42,
        "--method-name", method_name,
        "--min-support-fragments", int(args.tag_min_support_reads / 2),
        "--consensus-method", args.consensus_method,
        "--min-voting-loci", args.min_voting_loci,
        "--instability-ratio", args.instability_ratio,
        "--instability-count", args.instability_count,
        "--undetermined-weight", args.undetermined_weight,
        ("--locus-weight-is-score" if args.locus_weight_is_score else ""),
        "--input-references", train_path,
        "--input-evaluated", test_path,
        "--output-report", res_path
    ]))
    if clf_params is not None:
        cmd.extend([
            "--classifier-params", "'" + clf_params + "'"
        ])
    if "PYTHONPATH" in os.environ:
        os.environ["PYTHONPATH"] = os.environ['PYTHONPATH'] + os.pathsep + os.path.dirname(__file__)
    else:
        os.environ["PYTHONPATH"] = os.path.dirname(__file__)
    execCommand(cmd)

def launchAddClf(reports_path, args):
    for clf_name in args.add_classifiers:
        method_name = clf_name
        clf_params = None
        if clf_name.startswith("RandomForest:"):
            n_estimators = clf_name.split(":")[1]
            clf_name = "RandomForest"
            clf_params = '{"n_estimators": ' + n_estimators + '}'
        # Copy combination produced by MIAmS in data of the new method
        reports = MSIReport.parse(out_reports_path)
        lociInitData(reports, args.default_classifier, method_name)
        MSIReport.write(reports, out_reports_path)
        # Submit classification
        submitAddClf(models_path, out_reports_path, out_reports_path, args, method_name, clf_name, clf_params)


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description="Launch classification on evaluation datasets.")
    parser.add_argument('-i', '--start-dataset-id', type=int, default=0, help="This option allow you to skip the n first test. [Default: %(default)s]")
    parser.add_argument('-n', '--nb-tests', type=int, default=100, help="The number of couple of test and train datasets created from the original dataset. [Default: %(default)s]")
    parser.add_argument('-m', '--reference-method', default="ngs", help="The prefix of the columns in status_by_spl.tsv used as expected values (example: ngs, electro). [Default: %(default)s]")
    parser.add_argument('-k', '--default-classifier', default="SVCPairs", help='The classifier used in MIAmS. [Default: %(default)s]')
    parser.add_argument('-c', '--add-classifiers', default=[], nargs='+', help="The additional sklearn classifiers evaluates on MIAmS pairs combination results (example: DecisionTree, KNeighbors, LogisticRegression, RandomForest, RandomForest:n).")
    parser.add_argument('-v', '--version', action='version', version=__version__)
    # Loci classification
    group_loci = parser.add_argument_group('Loci classification')
    group_loci.add_argument('-t', '--tag-min-support-reads', default=100, type=int, help='The minimum numbers of reads for determine the status. [Default: %(default)s]')
    group_loci.add_argument('-e', '--learn-min-support-reads', default=400, type=int, help='The minimum numbers of reads for use loci in learning step. [Default: %(default)s]')
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
    group_input.add_argument('-d', '--data-folder', required=True, help="The folder containing data to process. It must contain design/, raw_by_run/ and status_by_spl.tsv.")
    group_input.add_argument('-w', '--work-folder', default=os.getcwd(), help="The working directory. [Default: %(default)s]")
    # Outputs
    group_output = parser.add_argument_group('Outputs')
    group_output.add_argument('-r', '--results-path', default="results.tsv", help='Path to the output file containing the description of the results and expected value for each samples in each datasets (format: TSV). [Default: %(default)s]')
    group_output.add_argument('-s', '--datasets-path', default="datasets.tsv", help='Path to the output file containing the description of the datasets (format: TSV). [Default: %(default)s]')
    args = parser.parse_args()

    # Parameters
    status_path = os.path.join(args.data_folder, "status_by_spl.tsv")
    raw_folder = os.path.join(args.data_folder, "raw_by_run")
    design_folder = os.path.join(args.data_folder, "design")
    if not os.path.exists(args.work_folder):
        os.makedirs(args.work_folder)

    # Logger
    logging.basicConfig(format='%(asctime)s - %(name)s [%(levelname)s] %(message)s')
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    log.info("Command: " + " ".join(sys.argv))

    # Load data
    loci_id_by_name = {locus.name: "{}:{}-{}".format(locus.chrom, locus.start - 1, locus.end) for locus in getAreas(os.path.join(design_folder, "targets.bed"))}
    status_by_spl = getStatusFromFile(status_path)
    samples = getSammplesFromDataFolder(raw_folder)
    addExpectedStatus(samples, status_by_spl, args.reference_method)
    samples_by_name = {spl["name"]: spl["status"][args.reference_method] for spl in samples}

    # Process assessment
    annotations_path = os.path.join(args.work_folder, "annot.tsv")
    samplesToAnnot(samples, os.path.join(design_folder, "targets.bed"), annotations_path, args.reference_method)
    cv = ShuffleSplit(n_splits=args.nb_tests, test_size=0.4, random_state=42)
    dataset_id = 0
    spl_wout_replicates = list({getSplFromLibName(spl["name"]): spl for spl in samples}.values())  # All replicates of one sample will be managed in same content (train or test)
    for train_idx, test_idx in cv.split(spl_wout_replicates, groups=[spl["status"][args.reference_method]["sample"] for spl in spl_wout_replicates]):
        dataset_md5 = hashlib.md5(",".join(map(str, train_idx)).encode('utf-8')).hexdigest()
        if args.start_dataset_id > dataset_id:
            log.info("Skip already processed dataset {}/{} ({}).".format(dataset_id, args.nb_tests - 1, dataset_md5))
        else:
            log.info("Start processing dataset {}/{} ({}).".format(dataset_id, args.nb_tests - 1, dataset_md5))
            # Temp file
            baseline_path = os.path.join(args.work_folder, "baseline_dataset-{}.tsv".format(dataset_id))
            models_path = os.path.join(args.work_folder, "models_dataset-{}.tsv".format(dataset_id))
            learn_log_path = os.path.join(args.work_folder, "log_dataset-{}.tsv".format(dataset_id))
            out_folder = os.path.join(args.work_folder, "out_dataset-{}".format(dataset_id))
            out_reports_path = os.path.join(args.work_folder, "out_reports_dataset-{}.json".format(dataset_id))
            # Create datasets
            train_names = {getSplFromLibName(spl["name"]): 0 for idx, spl in enumerate(spl_wout_replicates) if idx in train_idx}
            test_names = {getSplFromLibName(spl["name"]): 0 for idx, spl in enumerate(spl_wout_replicates) if idx in test_idx}
            train_samples = [spl for spl in samples if getSplFromLibName(spl["name"]) in train_names]
            test_samples = [spl for spl in samples if getSplFromLibName(spl["name"]) in test_names]
            # Process learn and tag
            train(train_samples, annotations_path, design_folder, baseline_path, models_path, learn_log_path, args)
            predict(test_samples, design_folder, baseline_path, models_path, out_folder, args)
            models = MSIReport.parse(models_path)
            reports = getMSISamples(os.path.join(out_folder, "data"))
            if len(args.add_classifiers) > 0:
                MSIReport.write(reports, out_reports_path)
                launchAddClf(out_reports_path, args)
                reports = MSIReport.parse(out_reports_path)
            # Write results and dataset
            use_header = False
            out_mode = "a"
            if dataset_id == 0:
                use_header = True
                out_mode = "w"
            datasets_df_rows = [
                getDatasetsInfo(
                    dataset_id,
                    dataset_md5,
                    loci_id_by_name,
                    models,
                    reports,
                    getLogInfo(learn_log_path),
                    getLogInfo(os.path.join(out_folder, "MIAmSTag_log.txt")),
                    samples_by_name
                )
            ]
            datasets_df = pd.DataFrame.from_records(datasets_df_rows, columns=getDatasetsInfoTitles(loci_id_by_name))
            with open(args.datasets_path, out_mode) as FH_out:
                datasets_df.to_csv(FH_out, header=use_header, sep='\t')
            res_df_rows = getResInfo(dataset_id, loci_id_by_name, reports, samples_by_name, ["MSINGS", args.default_classifier] + args.add_classifiers)
            res_df = pd.DataFrame.from_records(res_df_rows, columns=getResInfoTitles(loci_id_by_name))
            with open(args.results_path, out_mode) as FH_out:
                res_df.to_csv(FH_out, header=use_header, sep='\t')
            # Clean tmp
            for tmp_file in [baseline_path, models_path, learn_log_path, out_folder, out_reports_path]:
                if os.path.isdir(tmp_file):
                    shutil.rmtree(tmp_file)
                else:
                    os.remove(tmp_file)
        # Next dataset
        dataset_id += 1
