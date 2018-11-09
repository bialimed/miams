#!/usr/bin/env python3

__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2018 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '2.0.1'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import json
import argparse
from anacore.msi import LocusClassifier, MSIReport, Status
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier


########################################################################
#
# FUNCTIONS
#
########################################################################
class MIAmSClassifier(LocusClassifier):
    def __init__(self, locus_id, method_name="MIAmS", model_method_name="model", clf="SVC", clf_params=None):
        if clf_params is None:
            clf_params = {}
        clf_obj = self._getClassifier(clf, clf_params)
        super().__init__(locus_id, method_name, clf_obj, model_method_name)

    def _getClassifier(self, clf, clf_params):
        clf_obj = None
        if clf == "SVC":
            clf_params["probability"] = True
            clf_obj = SVC(**clf_params)
        elif clf == "LogisticRegression":
            clf_obj = LogisticRegression(**clf_params)
        elif clf == "DecisionTreeClassifier":
            clf_obj = DecisionTreeClassifier(**clf_params)
        elif clf == "KNeighborsClassifier":
            if "n_neighbors" in clf_params:
                clf_params["n_neighbors"] = 2
            if "random_state" in clf_params:
                del clf_params["random_state"]
            clf_obj = KNeighborsClassifier(**clf_params)
        elif clf == "RandomForestClassifier":
            clf_obj = RandomForestClassifier(**clf_params)
        else:
            raise Exception('The classifier "{}" is not implemented in MIAmSClassifier.'.format(clf))
        return clf_obj

def process(args):
    """
    Predict classification (status and score) for all samples loci.

    :param args: The namespace extracted from the script arguments.
    :type args: Namespace
    """
    train_dataset = MSIReport.parse(args.input_references)
    test_dataset = MSIReport.parse(args.input_evaluated)

    # Classification by locus
    loci_ids = sorted(train_dataset[0].loci.keys())
    for locus_id in loci_ids:
        # Select the samples with a sufficient number of fragment for classify the distribution
        evaluated_test_dataset = []
        for spl in test_dataset:
            if spl.loci[locus_id].results[args.method_name].getNbFrag() < args.min_support_fragments:
                spl.loci[locus_id].results[args.method_name].status = Status.undetermined
                spl.loci[locus_id].results[args.method_name].score = None
            else:
                evaluated_test_dataset.append(spl)
        # Classify
        if len(evaluated_test_dataset) != 0:
            clf = MIAmSClassifier(locus_id, args.method_name, "model", args.classifier, args.classifier_params)
            clf.fit(train_dataset)
            clf.set_status(evaluated_test_dataset)

    # Classification by sample
    for spl in test_dataset:
        if args.consensus_method == "majority":
            spl.setStatusByMajority(args.method_name, args.min_voting_loci)
        elif args.consensus_method == "ratio":
            spl.setStatusByInstabilityRatio(args.method_name, args.min_voting_loci, args.instability_ratio)
        elif args.consensus_method == "count":
            spl.setStatusByInstabilityCount(args.method_name, args.min_voting_loci, args.instability_count)
        spl.setScore(args.method_name, args.undetermined_weight)

    MSIReport.write(test_dataset, args.output_report)


class ClassifierParamsAction(argparse.Action):
    """Manages classifier-params parameters."""

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, json.loads(values))


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description='Predict classification (status and score) for all samples loci.')
    parser.add_argument('-m', '--method-name', default="MIAmS_combi", help='The name of the method storing locus metrics and where the status will be set. [Default: %(default)s]')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_locus = parser.add_argument_group('Locus classifier')  # Locus status
    group_locus.add_argument('-k', '--classifier', default="SVC", choices=["DecisionTreeClassifier", "KNeighborsClassifier", "LogisticRegression", "RandomForestClassifier", "SVC"], help='The classifier used to predict loci status.')
    group_locus.add_argument('-p', '--classifier-params', action=ClassifierParamsAction, default={}, help='Additional parameters provided to classifier in json string (example: {"n_estimators": 1000} for RandmForest).')
    group_locus.add_argument('-f', '--min-support-fragments', default=150, type=int, help='The minimum numbers of fragment (reads pairs) for determine the status. [Default: %(default)s]')
    group_locus.add_argument('-s', '--random-seed', default=None, type=int, help='The seed used by the random number generator in the classifier.')
    group_status = parser.add_argument_group('Sample consensus status')  # Sample status
    group_status.add_argument('-c', '--consensus-method', default='ratio', choices=['count', 'majority', 'ratio'], help='Method used to determine the sample status from the loci status. Count: if the number of unstable is upper or equal than instability-count the sample will be unstable otherwise it will be stable ; Ratio: if the ratio of unstable/determined loci is upper or equal than instability-ratio the sample will be unstable otherwise it will be stable ; Majority: if the ratio of unstable/determined loci is upper than 0.5 the sample will be unstable, if it is lower than stable the sample will be stable. [Default: %(default)s]')
    group_status.add_argument('-l', '--min-voting-loci', default=3, type=int, help='Minimum number of voting loci (stable + unstable) to determine the sample status. If the number of voting loci is lower than this value the status for the sample will be undetermined. [Default: %(default)s]')
    group_status.add_argument('-i', '--instability-ratio', default=0.2, type=float, help='[Only with consensus-method = ratio] If the ratio unstable/(stable + unstable) is superior than this value the status of the sample will be unstable otherwise it will be stable. [Default: %(default)s]')
    group_status.add_argument('-u', '--instability-count', default=3, type=int, help='[Only with consensus-method = count] If the number of unstable loci is upper or equal than this value the sample will be unstable otherwise it will be stable. [Default: %(default)s]')
    group_status.add_argument('-w', '--undetermined-weight', default=0.5, type=float, help='The weight of the undetermined loci in sample score calculation. [Default: %(default)s]')
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-r', '--input-references', required=True, help='Path to the file containing the references samples used in learn step (format: MSIReport).')
    group_input.add_argument('-e', '--input-evaluated', required=True, help='Path to the file containing the samples with loci to classify (format: MSIReport).')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output-report', required=True, help='The path to the output file (format: MSIReport).')
    args = parser.parse_args()

    if args.consensus_method != "ratio" and args.instability_ratio != parser.get_default('instability_ratio'):
        raise Exception('The parameter "instability-ratio" can only used with consensus-ratio set to "ratio".')
    if args.consensus_method != "count" and args.instability_count != parser.get_default('instability_count'):
        raise Exception('The parameter "instability-count" can only used with consensus-ratio set to "count".')
    args.classifier_params["random_state"] = args.random_seed

    # Process
    process(args)
