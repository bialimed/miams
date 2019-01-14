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
__version__ = '1.2.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import os
import re
import random
import argparse
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
sns.set_style("whitegrid")


########################################################################
#
# FUNCTIONS
#
########################################################################
def getLoci(dataset_df):
    loci = []
    for col_name in dataset_df.columns:
        if col_name != "train_nb_spl_stable":
            match = re.match("^train_nb_(.+)_stable$", col_name)
            if match is not None:
                loci.append(match.group(1))
    return sorted(loci)

def execTime(dataset_df, out_path):
    # Exec time
    time_rows = []
    for time in dataset_df["learn_exec_time"]:
        time_rows.append([time / 60, "learn"])
    for time in dataset_df["tag_exec_time"]:
        time_rows.append([time / 60, "tag"])
    time_df = pd.DataFrame.from_records(time_rows, columns=["exec_time", "workflow"])
    # Plot
    ax = sns.boxplot(x="workflow", y="exec_time", data=time_df, medianprops=dict(linewidth=2, color='firebrick'))
    ax.set(ylabel='execution time (min)')
    plt.subplots_adjust(top=0.95)
    plt.gcf().suptitle("MIAmS execution time ({} executions)".format(len(dataset_df)))
    plt.savefig(out_path)
    plt.close()

def datasetsComposition(dataset_df, out_path, mode="rate"):
    # Datasets descriptions
    desc_rows = []
    for idx, row in dataset_df.iterrows():
        for dataset_type in ["train", "test"]:
            for locus in ["spl", "BAT25", "BAT26", "HT17", "NR21", "NR22", "NR27"]:
                nb_determined = row["{}_nb_{}_unstable".format(dataset_type, locus)] + row["{}_nb_{}_stable".format(dataset_type, locus)]
                if nb_determined != 0:
                    ratio_unstable = row["{}_nb_{}_unstable".format(dataset_type, locus)] / nb_determined
                    desc_rows.append([
                        dataset_type,
                        locus,
                        ratio_unstable,
                        row["{}_nb_{}_stable".format(dataset_type, locus)],
                        row["{}_nb_{}_unstable".format(dataset_type, locus)]
                    ])
    desc_df = pd.DataFrame.from_records(desc_rows, columns=["dataset_type", "locus", "unstable_ratio", "nb_stable", "nb_unstable"])
    # Plot
    if mode == "rate":
        sns.boxplot(x="locus", y="unstable_ratio", hue="dataset_type", data=desc_df, medianprops=dict(linewidth=2, color='firebrick'))
        plt.subplots_adjust(top=0.95)
        plt.gcf().suptitle("Rate of unstable ({} datasets)".format(len(dataset_df)))
    else:
        sns.boxplot(x="locus", y="nb_unstable", hue="dataset_type", data=desc_df, medianprops=dict(linewidth=2, color='firebrick'))
        plt.subplots_adjust(top=0.95)
        plt.gcf().suptitle("Number of unstable ({} datasets)".format(len(dataset_df)))
    plt.savefig(out_path)
    plt.close()

def getSplConsensusScore(row, loci, undetermined_weight=0.5, locus_weight_is_score=True):
    eval_status = row["spl_expected_status"]
    undetermined_weight = 0 if row["method_name"] == "MSINGS" else undetermined_weight
    scores = list()
    nb_loci_undetermined = 0
    for locus in loci:
        if row["{}_observed_status".format(locus)] == "Undetermined":
            nb_loci_undetermined += 1
        else:
            if row["{}_observed_status".format(locus)] == eval_status:
                if locus_weight_is_score and not pd.isnull(row["{}_pred_score".format(locus)]):
                    scores.append(row["{}_pred_score".format(locus)])
                else:
                    scores.append(1)
            elif row["{}_observed_status".format(locus)] != "Undetermined":
                if locus_weight_is_score and not pd.isnull(row["{}_pred_score".format(locus)]):
                    scores.append(1 - row["{}_pred_score".format(locus)])
                else:
                    scores.append(0)
    score = None
    if len(scores) != 0:
        score = sum(scores) / (len(scores) + nb_loci_undetermined * undetermined_weight)
        score = round(score, 5)
    return score

def getSplConsensusStatus(row, args):
    fct_by_method = {
        "count": getSplConsensusStatusCount,
        "ratio": getSplConsensusStatusRatio,
        "majority": getSplConsensusStatusMajority,
        "odd": getSplConsensusStatusOdd
    }
    nb_by_status = {"MSI": 0, "MSS": 0, "Undetermined": 0}
    for col in row.keys():
        if col.endswith("observed_status") and col != "spl_observed_status":
            nb_by_status[row[col]] += 1
    spl_status = "Undetermined"
    if nb_by_status["MSS"] + nb_by_status["MSI"] >= args.min_voting_loci:
        spl_status = fct_by_method[args.consensus_method](nb_by_status, args)
    return spl_status

def getSplConsensusStatusOdd(nb_by_status, args):
    spl_status = "Undetermined"
    if nb_by_status["MSI"] >= 3:
        spl_status = "MSI"
    elif nb_by_status["MSS"] >= 3:
        spl_status = "MSS"
    return spl_status

def getSplConsensusStatusCount(nb_by_status, args):
    spl_status = "Undetermined"
    if nb_by_status["MSI"] >= args.instability_count:
        spl_status = "MSI"
    else:
        spl_status = "MSS"
    return spl_status

def getSplConsensusStatusRatio(nb_by_status, args):
    spl_status = "Undetermined"
    if nb_by_status["MSI"] / (nb_by_status["MSI"] + nb_by_status["MSS"]) >= args.instability_ratio:
        spl_status = "MSI"
    else:
        spl_status = "MSS"
    return spl_status

def getSplConsensusStatusMajority(nb_by_status, args):
    spl_status = "Undetermined"
    if nb_by_status["MSI"] > nb_by_status["MSS"]:
        spl_status = "MSI"
    elif nb_by_status["MSI"] < nb_by_status["MSS"]:
        spl_status = "MSS"
    # else nb_by_status["MSI"] == nb_by_status["MSS"]
    return spl_status

def getFilteredObservation(row, locus, min_nb_support=None, min_score=None):
    status = "Undetermined"
    if min_nb_support is None or row["{}_pred_support".format(locus)] >= min_nb_support:
        if min_score is None or row["{}_pred_score".format(locus)] >= min_score:
            status = row["{}_observed_status".format(locus)]
    return status

def getPredStatusEval(row, locus):
    status = "Undetermined"
    if row["{}_observed_status".format(locus)] != "Undetermined":
        if row["{}_expected_status".format(locus)] == row["{}_observed_status".format(locus)]:
            status = "concordant"
        else:
            status = "discordant"
    return status

def getAccuracyDf(loci, results_df):
    accuracy_rows = []
    datasets_ids = list(set(results_df["dataset_id"]))
    methods = sorted(list(set(results_df["method_name"])))
    for dataset_id in datasets_ids:
        for method_name in methods:
            dataset = results_df[
                (results_df["dataset_id"] == dataset_id) &
                (results_df["method_name"] == method_name)
            ]
            ct_status_by_locus = {
                locus: {"concordant": 0, "discordant": 0, "Undetermined": 0} for locus in loci
            }
            for idx, row in dataset.iterrows():
                for locus in loci:
                    if row["{}_expected_status".format(locus)] != "Undetermined":
                        status = getPredStatusEval(row, locus)
                        ct_status_by_locus[locus][status] += 1
            for locus in loci:
                nb_determined = ct_status_by_locus[locus]["concordant"] + ct_status_by_locus[locus]["discordant"]
                accuracy_rows.append([
                    dataset_id,
                    locus,
                    method_name,
                    (None if nb_determined == 0 else ct_status_by_locus[locus]["concordant"] / nb_determined),
                    ct_status_by_locus[locus]["concordant"],
                    ct_status_by_locus[locus]["discordant"],
                    ct_status_by_locus[locus]["Undetermined"]
                ])
    accuracy_df = pd.DataFrame.from_records(accuracy_rows, columns=["dataset_id", "locus", "method", "accuracy", "nb_concordant_prediction", "nb_discordant_prediction", "nb_without_prediction"])
    return accuracy_df

def writeAccuracy(loci, results_df, out_path, label_margin=0.01):
    accuracy_df = getAccuracyDf(loci, results_df)
    plt.figure(figsize=(8,5))
    g = sns.boxplot(x="locus", y="accuracy", hue="method", data=accuracy_df, medianprops=dict(linewidth=2, color='firebrick'))
    methods = sorted(list(set(accuracy_df["method"])))
    box_width = 0.8 / len(methods)
    for locus_idx, label in enumerate(g.axes.get_xticklabels()):
        locus_start = locus_idx - 0.4
        curr_locus = loci[locus_idx]
        for idx_method, curr_method in enumerate(methods):
            x_pos = locus_start + idx_method * box_width
            median = np.median(accuracy_df[
                (accuracy_df['locus'] == curr_locus) &
                (accuracy_df['method'] == curr_method)
            ]["accuracy"])
            max = np.max(accuracy_df[
                (accuracy_df['locus'] == curr_locus) &
                (accuracy_df['method'] == curr_method)
            ]["accuracy"])
            g.axes.text(x_pos + box_width / 2, max + label_margin, '{:.1f}'.format(median * 100), rotation='vertical', horizontalalignment='center', size='x-small', color='gray', weight='semibold')
    plt.subplots_adjust(top=0.9)
    plt.gcf().suptitle("Classification accuracy")
    plt.savefig(out_path)
    plt.close()

def writePredStatus(loci, results_df, out_path, nb_col=1, subplots_adjust=0.9, offset=1):
    # Agglomerate dataset info
    accuracy_df = getAccuracyDf(loci, results_df)
    status_rows = []
    for idx, row in accuracy_df.iterrows():
        nb_evaluated = row["nb_concordant_prediction"] + row["nb_discordant_prediction"] + row["nb_without_prediction"]
        for status in ["nb_concordant_prediction", "nb_discordant_prediction", "nb_without_prediction"]:
            status_rows.append([
                row["dataset_id"],
                row["locus"],
                row["method"],
                status.split("_")[1],
                row[status] * 100 / nb_evaluated
            ])
    status_df = pd.DataFrame.from_records(status_rows, columns=["dataset_id", "locus", "method", "prediction_status", "% of samples"])

    # Plot status
    prediction_status_order = ["discordant", "without"]
    status_df = status_df[status_df["prediction_status"] != "concordant"]
    g = sns.catplot(y="% of samples", x="prediction_status", hue="method", col="locus", col_wrap=nb_col, data=status_df, kind="box", order=prediction_status_order)
    for ax in g.axes.flat:
        _ = plt.setp(ax.get_xticklabels(), visible=True)
        locus_name = ax.get_title().split(" ")[-1]
        locus_df = status_df[status_df["locus"] == locus_name]
        methods = sorted(list(set(status_df["method"])))
        box_width = 0.8 / len(methods)
        for status_idx, label in enumerate(ax.get_xticklabels()):
            status_start = status_idx - 0.4
            curr_pred_status = prediction_status_order[status_idx]
            for idx_method, curr_method in enumerate(methods):
                x_pos = status_start + idx_method * box_width
                median = np.median(locus_df[
                    (locus_df['prediction_status'] == curr_pred_status) &
                    (locus_df['method'] == curr_method)
                ]["% of samples"])
                max = np.max(locus_df[
                    (locus_df['prediction_status'] == curr_pred_status) &
                    (locus_df['method'] == curr_method)
                ]["% of samples"])
                ax.text(x_pos + box_width / 2, max + offset, '{:.1f}'.format(median), horizontalalignment='center', size='x-small', color='gray', weight='semibold')
    plt.subplots_adjust(top=subplots_adjust, hspace=0.2)
    plt.gcf().suptitle("Classification accuracy")
    plt.savefig(out_path)
    plt.close()

def getBalancedDf(locus, results_df, random_seed):
    balanced_results_df = pd.DataFrame(columns=results_df.columns)
    datasets_ids = set(results_df["dataset_id"])
    for curr_dataset in datasets_ids:
        curr_dataset_df = results_df[results_df["dataset_id"] == curr_dataset]
        expected_stable = curr_dataset_df[
            curr_dataset_df["{}_expected_status".format(locus)] == "MSS"
        ]
        stable_ids = sorted(list(set(expected_stable["spl_name"])))
        expected_unstable = curr_dataset_df[
            curr_dataset_df["{}_expected_status".format(locus)] == "MSI"
        ]
        unstable_ids = sorted(list(set(expected_unstable["spl_name"])))
        sampling_size = min(len(stable_ids), len(unstable_ids))
        random.seed(random_seed)
        selected_spl = random.sample(stable_ids, sampling_size) + random.sample(unstable_ids, sampling_size)
        balanced_results_df = balanced_results_df.append(
            curr_dataset_df[curr_dataset_df["spl_name"].isin(selected_spl)],
            sort=False,
            ignore_index=True
        )
    return balanced_results_df

def writeBalancedPredStatus(loci, results_df, out_path, nb_col=1, subplots_adjust=0.9, random_seed=None):
    # Create accuracy dataframe with expected status balanced by locus and dataset
    accuracy_df = None
    for locus in loci:
        balanced_df = getBalancedDf(locus, results_df, random_seed)
        locus_accuracy_df = getAccuracyDf([locus], balanced_df)  # One locus the others are not balanced
        if accuracy_df is None:
            accuracy_df = pd.DataFrame(columns=locus_accuracy_df.columns)
        accuracy_df = accuracy_df.append(locus_accuracy_df, sort=False, ignore_index=True)

    # Agglomerate dataset info
    status_rows = []
    for idx, row in accuracy_df.iterrows():
        nb_evaluated = row["nb_concordant_prediction"] + row["nb_discordant_prediction"] + row["nb_without_prediction"]
        for status in ["nb_concordant_prediction", "nb_discordant_prediction", "nb_without_prediction"]:
            status_rows.append([
                row["dataset_id"],
                row["locus"],
                row["method"],
                status.split("_")[1],
                row[status] * 100 / nb_evaluated
            ])
    status_df = pd.DataFrame.from_records(status_rows, columns=["dataset_id", "locus", "method", "prediction_status", "% of samples"])

    # Plot status
    prediction_status_order = ["discordant", "without"]
    status_df = status_df[status_df["prediction_status"] != "concordant"]
    g = sns.catplot(y="% of samples", x="prediction_status", hue="method", col="locus", col_wrap=nb_col, data=status_df, kind="box", order=prediction_status_order)
    for ax in g.axes.flat:
        _ = plt.setp(ax.get_xticklabels(), visible=True)
        locus_name = ax.get_title().split(" ")[-1]
        locus_df = status_df[status_df["locus"] == locus_name]
        methods = sorted(list(set(status_df["method"])))
        box_width = 0.8 / len(methods)
        for status_idx, label in enumerate(ax.get_xticklabels()):
            status_start = status_idx - 0.4
            curr_pred_status = prediction_status_order[status_idx]
            for idx_method, curr_method in enumerate(methods):
                x_pos = status_start + idx_method * box_width
                median = np.median(locus_df[
                    (locus_df['prediction_status'] == curr_pred_status) &
                    (locus_df['method'] == curr_method)
                ]["% of samples"])
                max = np.max(locus_df[
                    (locus_df['prediction_status'] == curr_pred_status) &
                    (locus_df['method'] == curr_method)
                ]["% of samples"])
                ax.text(x_pos + box_width / 2, max + 2, '{:.1f}'.format(median * 100), horizontalalignment='center', size='x-small', color='gray', weight='semibold')
    plt.subplots_adjust(top=subplots_adjust, hspace=0.2)
    plt.gcf().suptitle("Classification accuracy")
    plt.savefig(out_path)
    plt.close()

def getMajority(status):
    consensus = "Undetermined"
    nb_by_status = {"MSI": 0, "MSS": 0, "Undetermined": 0}
    for curr_status in status:
        nb_by_status[curr_status] += 1
    if nb_by_status["MSI"] > nb_by_status["MSS"]:
        consensus = "MSI"
    elif nb_by_status["MSI"] < nb_by_status["MSS"]:
        consensus = "MSS"
    return consensus

def getAgreement(status):
    agreement = "Undetermined"
    list_of_pred = [curr_status for curr_status in status]
    if len(set(list_of_pred)) == 1:
        agreement = list_of_pred[0]
    return agreement

def getMethodsConsensusDf(res_df, loci, used_methods=None, consensus_method="majority"):
    if used_methods is None:
        used_methods = sorted(list(set(res_df["method_name"])))
    nb_used_methods = len(used_methods)
    consensus_data = {}
    consensus_rows = []
    for idx_row, curr_row in res_df.iterrows():
        res_id = "{}_{}".format(curr_row["dataset_id"], curr_row["lib_name"])
        if curr_row["method_name"] in used_methods:
            if res_id not in consensus_data:
                consensus_data[res_id] = {
                    "dataset_id": curr_row["dataset_id"],
                    "lib_name": curr_row["lib_name"],
                    "spl_name": curr_row["spl_name"]
                }
                for elt in ["spl"] + loci:
                    consensus_data[res_id][elt + "_expected_status"] = curr_row[elt + "_expected_status"]
                    consensus_data[res_id][elt + "_observed_status"] = [curr_row[elt + "_observed_status"]]
            else:
                for elt in ["spl"] + loci:
                    consensus_data[res_id][elt + "_observed_status"].append(curr_row[elt + "_observed_status"])
            if len(consensus_data[res_id]["spl_observed_status"]) == nb_used_methods:
                cons_row = {k: v for k, v in consensus_data[res_id].items()}
                cons_row["method_name"] = consensus_method
                for elt in ["spl"] + loci:
                    if consensus_method == "majority":
                        cons_row[elt + "_observed_status"] = getMajority(cons_row[elt + "_observed_status"])
                    else:
                        cons_row[elt + "_observed_status"] = getAgreement(cons_row[elt + "_observed_status"])
                    cons_row[elt + "_pred_score"] = None
                    cons_row[elt + "_pred_is_ok"] = None
                    if elt != "spl":
                        cons_row[elt + "_pred_support"] = None
                for elt in ["spl"] + loci:
                    cons_row[elt + "_pred_is_ok"] = getPredStatusEval(cons_row, elt)
                consensus_rows.append(cons_row)
                del(consensus_data[res_id])
    return pd.DataFrame(consensus_rows)

def getLociDf(loci, results_df):
    loci_rows = []
    for idx, row in results_df.iterrows():
        for locus in loci:
            if row["{}_expected_status".format(locus)] != "Undetermined":
                loci_rows.append([
                    row["dataset_id"],
                    locus,
                    row["method_name"],
                    row["{}_pred_score".format(locus)],
                    getPredStatusEval(row, locus)
                ])
    loci_df = pd.DataFrame.from_records(loci_rows, columns=["dataset_id", "locus", "method", "prediction_score", "prediction_status"])
    return loci_df

def addCount(df, graph, x_column, y_column, hue_column, x_order=None, hue_order=None, label_margin=0.05):
    if x_order is None:
        x_order = sorted(list(set(df[x_column])))
    if hue_order is None:
        hue_order = sorted(list(set(df[hue_column])))
    box_width = 0.8 / len(hue_order)
    for x_idx, label in enumerate(graph.axes.get_xticklabels()):
        tick_start = x_idx - 0.4
        curr_x = x_order[x_idx]
        for hue_idx, curr_hue in enumerate(hue_order):
            filtered_y = df[
                (df[x_column] == curr_x) &
                (df[hue_column] == curr_hue)
            ][y_column].dropna()
            x_pos = tick_start + hue_idx * box_width
            count = len(filtered_y)
            max = (0 if count == 0 else np.max(filtered_y))
            if count != 0:
                graph.axes.text(x_pos + box_width / 2, max + label_margin, 'n:{}'.format(count), horizontalalignment='center', size='x-small', color='gray', weight='semibold')

def writeScorePredStatus(loci, results_df, out_path, nb_col=1, subplots_adjust=0.9):
    loci_df = getLociDf(loci, results_df)
    loci_df = loci_df[loci_df["prediction_status"] != "Undetermined"]
    loci_df = loci_df[loci_df["method"] != "agreement"]
    prediction_status_order = ["concordant", "discordant"]
    graph = sns.catplot(
        x="method",
        y="prediction_score",
        hue="prediction_status",
        col="locus",
        col_wrap=nb_col,
        data=loci_df,
        kind="box",
        medianprops=dict(linewidth=2, color='firebrick'),
        order=sorted(list(set(loci_df["method"]))),
        hue_order=prediction_status_order
    )
    for ax in graph.axes.flat:
        _ = plt.setp(ax.get_xticklabels(), visible=True)
        locus_name = ax.get_title().split(" ")[-1]
        curr_locus_df = loci_df[loci_df["locus"] == locus_name]
        addCount(curr_locus_df, ax, "method", "prediction_score", "prediction_status", None, prediction_status_order, 2)
    plt.subplots_adjust(top=subplots_adjust, hspace=0.2)
    plt.gcf().suptitle("Confidence score evaluation")
    plt.savefig(out_path)
    plt.close()

def writeBalancedScorePredStatus(loci, results_df, out_path, nb_col=1, subplots_adjust=0.9, random_seed=None):
    loci_balanced_df = None
    for locus in loci:
        balanced_df = getBalancedDf(locus, results_df, random_seed)
        curr_locus_df = getLociDf([locus], balanced_df)  # One locus the others are not balanced
        if loci_balanced_df is None:
            loci_balanced_df = pd.DataFrame(columns=curr_locus_df.columns)
        loci_balanced_df = loci_balanced_df.append(curr_locus_df, sort=False, ignore_index=True)

    # Plot scores
    loci_balanced_df = loci_balanced_df[loci_balanced_df["prediction_status"] != "Undetermined"]
    loci_balanced_df = loci_balanced_df[loci_balanced_df["method"] != "agreement"]
    prediction_status_order = ["concordant", "discordant"]
    graph = sns.catplot(
        x="method",
        y="prediction_score",
        hue="prediction_status",
        col="locus",
        col_wrap=nb_col,
        data=loci_balanced_df,
        kind="box",
        medianprops=dict(linewidth=2, color='firebrick'),
        order=sorted(list(set(loci_balanced_df["method"]))),
        hue_order=prediction_status_order
    )
    for ax in graph.axes.flat:
        _ = plt.setp(ax.get_xticklabels(), visible=True)
        locus_name = ax.get_title().split(" ")[-1]
        curr_locus_df = loci_balanced_df[loci_balanced_df["locus"] == locus_name]
        addCount(curr_locus_df, ax, "method", "prediction_score", "prediction_status", None, prediction_status_order, 2)
    plt.subplots_adjust(top=subplots_adjust, hspace=0.2)
    plt.gcf().suptitle("Confidence score evaluation")
    plt.savefig(out_path)
    plt.close()


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description='Process assessment results to display information on MIAmS accuracy.')
    parser.add_argument('-s', '--random-seed', default=42, type=int, help='The random seed used to balance datasets. [Default: %(default)s]')
    parser.add_argument('-mr', '--min-reads-support', type=int, help='The prediction of all loci with a number of reads lower than this value are set to undetermined. [Default: no filter]')
    parser.add_argument('-ms', '--min-score', type=float, help='The prediction of all loci with a prediction score lower than this value are set to undetermined. [Default: no filter]')
    parser.add_argument('-k', '--default-classifier', default="SVCPairs", help='The classifier used in consensus between MSINGS and MIAmS default classifier. [Default: %(default)s]')
    parser.add_argument('-ac', '--add-algorithm-consensus', default=False, action='store_true', help='Add agreement and consensus on algorithms prediction.')
    parser.add_argument('-b', '--process-balanced-metrics', default=False, action='store_true', help='For each metrics the number of target expected MSI and MSS are balanced by random sampling.')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    # Sample classification score
    group_score = parser.add_argument_group('Sample prediction score')
    group_score.add_argument('--undetermined-weight', default=0.0, type=float, help='[Used for all the classifiers different from MSINGS] The weight of undetermined loci in sample prediction score calculation. [Default: %(default)s]')
    group_score.add_argument('--locus-weight-is-score', action='store_true', help='[Used for all the classifiers different from MSINGS] Use the prediction score of each locus as wheight of this locus in sample prediction score calculation. [Default: %(default)s]')
    # Sample classification
    group_spl = parser.add_argument_group('Sample classification')
    group_spl.add_argument('--consensus-method', default='ratio', choices=['count', 'majority', 'odd', 'ratio'], help='Method used to determine the sample status from the loci status. Count: if the number of unstable is upper or equal than instability-count the sample will be unstable otherwise it will be stable ; Ratio: if the ratio of unstable/determined loci is upper or equal than instability-ratio the sample will be unstable otherwise it will be stable ; Majority: if the ratio of unstable/determined loci is upper than 0.5 the sample will be unstable, if it is lower than stable the sample will be stable. [Default: %(default)s]')
    group_spl.add_argument('--min-voting-loci', default=3, type=int, help='Minimum number of voting loci (stable + unstable) to determine the sample status. If the number of voting loci is lower than this value the status for the sample will be undetermined. [Default: %(default)s]')
    group_spl.add_argument('--instability-ratio', default=0.2, type=float, help='[Only with consensus-method = ratio] If the ratio unstable/(stable + unstable) is superior than this value the status of the sample will be unstable otherwise it will be stable. [Default: %(default)s]')
    group_spl.add_argument('--instability-count', default=3, type=int, help='[Only with consensus-method = count] If the number of unstable loci is upper or equal than this value the sample will be unstable otherwise it will be stable. [Default: %(default)s]')
    # Inputs
    group_input = parser.add_argument_group('Inputs')
    group_input.add_argument('-d', '--input-datasets', required=True, help='The path to the file describing datasets used in assessment (format: TSV).')
    group_input.add_argument('-r', '--input-results', required=True, help='The path to the file describing predictions results produced by assessment (format: TSV).')
    # Outputs
    group_output = parser.add_argument_group('Outputs')
    group_output.add_argument('-f', '--output-folder', default=".", help='The path to the output folder. [Default: %(default)s]')
    args = parser.parse_args()

    # Init data
    dataset_df = pd.read_csv(args.input_datasets, sep='\t')
    results_df = pd.read_csv(args.input_results, sep='\t')
    loci = getLoci(dataset_df)
    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)

    # Preprocess and filter data
    results_df["spl_name"] = results_df["lib_name"].apply(lambda lib_name: lib_name.split("_")[0])
    for locus in loci:
        results_df["{}_observed_status".format(locus)] = results_df.apply(lambda row: getFilteredObservation(row, locus, args.min_reads_support, args.min_score), axis=1)
        results_df["{}_pred_is_ok".format(locus)] = results_df.apply(lambda row: getPredStatusEval(row, locus), axis=1)
    results_df["spl_observed_status"] = results_df.apply(lambda row: getSplConsensusStatus(row, args), axis=1)
    results_df["spl_pred_score"] = results_df.apply(lambda row: getSplConsensusScore(row, loci, args.undetermined_weight, args.locus_weight_is_score), axis=1)
    results_df["spl_pred_is_ok"] = results_df.apply(lambda row: getPredStatusEval(row, "spl"), axis=1)
    if args.add_algorithm_consensus:
        # results_df = pd.concat([results_df, getMethodsConsensusDf(results_df, loci, ["MSINGS", args.default_classifier], "majority")], sort=False)
        results_df = pd.concat([results_df, getMethodsConsensusDf(results_df, loci, ["MSINGS", args.default_classifier], "agreement")], sort=False)
    with open(os.path.join(args.output_folder, "cleaned_results.tsv"), "w") as FH_out:
        results_df.to_csv(FH_out, sep='\t')

    # Datasets information
    execTime(dataset_df, os.path.join(args.output_folder, "exectimes.svg"))
    datasetsComposition(dataset_df, os.path.join(args.output_folder, "datasets_composition_rate.svg"), "rate")
    datasetsComposition(dataset_df, os.path.join(args.output_folder, "datasets_composition_count.svg"), "count")

    # Predictions information
    writeAccuracy(loci, results_df, os.path.join(args.output_folder, "accuracy_loci.svg"), 0.01)
    writeAccuracy(["spl"], results_df, os.path.join(args.output_folder, "accuracy_spl.svg"), 0.01)
    writePredStatus(loci, results_df, os.path.join(args.output_folder, "pred_status_loci.svg"), 2, 0.92, 2)
    writePredStatus(["spl"], results_df, os.path.join(args.output_folder, "pred_status_spl.svg"), 1, 0.85, 0.5)
    writeScorePredStatus(["spl"] + loci, results_df, os.path.join(args.output_folder, "pred_score_all.svg"), 2, 0.92)
    writeScorePredStatus(["spl"], results_df, os.path.join(args.output_folder, "pred_score_spl.svg"), 1, 0.85)

    # Balanced predictions information
    if args.process_balanced_metrics:
        writeBalancedPredStatus(loci, results_df, os.path.join(args.output_folder, "pred_status_loci_balanced.svg"), 2, 0.92, args.random_seed)
        writeBalancedPredStatus(["spl"], results_df, os.path.join(args.output_folder, "pred_status_spl_balanced.svg"), 1, 0.85, args.random_seed)
        writeBalancedScorePredStatus(loci, results_df, os.path.join(args.output_folder, "pred_score_loci_balanced.svg"), 2, 0.92, args.random_seed)
        writeBalancedScorePredStatus(["spl"], results_df, os.path.join(args.output_folder, "pred_score_spl_balanced.svg"), 1, 0.85, args.random_seed)
