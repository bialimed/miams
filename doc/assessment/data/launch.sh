#!/bin/bash


################################################################################
#
# Process assessment
#
################################################################################
# ../processAssessment.py \
#     --data-folder . \
#     --work-folder tmp_work \
#     --results-path results/results.tsv \
#     --datasets-path results/datasets.tsv \
#     --add-classifiers DecisionTree KNeighbors LogisticRegression RandomForest RandomForest:50 RandomForest:500 \
#     --tag-min-support-reads 100 \
#     --learn-min-support-reads 400 \
#     --consensus-method count \
#     --instability-count 3 \
#     --start-dataset-id 0 \
#     --nb-tests 50


################################################################################
#
# Process accuracy
#
################################################################################
# MIAmS classifiers
grep -v "DecisionTree" results/results.tsv | grep -v "KNeighbors" - | grep -v "LogisticRegression" - | grep -v "RandomForest" - > results/results_miams.tsv

../processAccuracy.py \
    --add-algorithm-consensus \
    --min-reads-support 300 \
    --consensus-method count \
    --min-voting-loci 3 \
    --instability-count 3 \
    --input-datasets results/datasets.tsv \
    --input-results results/results_miams.tsv \
    --output-folder results/miamsClf_cCount_s300

../processAccuracy.py \
    --add-algorithm-consensus \
    --min-reads-support 300 \
    --consensus-method count \
    --min-voting-loci 3 \
    --instability-count 3 \
    --undetermined-weight 0.5 \
    --input-datasets results/datasets.tsv \
    --input-results results/results_miams.tsv \
    --output-folder results/miamsClf_cCount_s300_2

../processAccuracy.py \
    --add-algorithm-consensus \
    --min-reads-support 300 \
    --consensus-method count \
    --min-voting-loci 3 \
    --instability-count 3 \
    --locus-weight-is-score \
    --input-datasets results/datasets.tsv \
    --input-results results/results_miams.tsv \
    --output-folder results/miamsClf_cCount_s300_3

# ../processAccuracy.py \
#     --add-algorithm-consensus \
#     --min-reads-support 100 \
#     --consensus-method count \
#     --min-voting-loci 3 \
#     --instability-count 3 \
#     --input-datasets results/datasets.tsv \
#     --input-results results/results_miams.tsv \
#     --output-folder results/miamsClf_cCount_s100
#
# ../processAccuracy.py \
#     --add-algorithm-consensus \
#     --min-reads-support 300 \
#     --consensus-method majority \
#     --min-voting-loci 3 \
#     --input-datasets results/datasets.tsv \
#     --input-results results/results_miams.tsv \
#     --output-folder results/miamsClf_cMajority_s300

rm results/results_miams.tsv


# Sklearn classifiers
grep -v "MSINGS" results/results.tsv > results/results_sklearnClf.tsv

sed -i 's/SVCPairs/SVC/' results/results_sklearnClf.tsv

# ../processAccuracy.py \
#     --min-reads-support 300 \
#     --consensus-method count \
#     --min-voting-loci 3 \
#     --instability-count 3 \
#     --input-datasets results/datasets.tsv \
#     --input-results results/results_sklearnClf.tsv \
#     --output-folder results/sklearnClf_cCount_s300

# ../processAccuracy.py \
#     --min-reads-support 100 \
#     --consensus-method count \
#     --min-voting-loci 3 \
#     --instability-count 3 \
#     --input-datasets results/datasets.tsv \
#     --input-results results/results_sklearnClf.tsv \
#     --output-folder results/sklearnClf_cCount_s100

rm results/results_sklearnClf.tsv
