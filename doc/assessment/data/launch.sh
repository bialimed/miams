../processAccuracy.py \
    --min-reads-support 100 \
    --consensus-method count \
    --min-voting-loci 3 \
    --instability-count 3 \
    --input-datasets datasets.tsv \
    --input-results results.tsv \
    --output-folder results_cCount_s100

../processAccuracy.py \
    --min-reads-support 300 \
    --consensus-method count \
    --min-voting-loci 3 \
    --instability-count 3 \
    --input-datasets datasets.tsv \
    --input-results results.tsv \
    --output-folder results_cCount_s300

../processAccuracy.py \
    --min-reads-support 300 \
    --consensus-method majority \
    --min-voting-loci 3 \
    --input-datasets datasets.tsv \
    --input-results results.tsv \
    --output-folder results_cMajority_s300

../processAccuracy.py \
    --min-reads-support 300 \
    --consensus-method odd \
    --min-voting-loci 3 \
    --input-datasets datasets.tsv \
    --input-results results.tsv \
    --output-folder results_cOdd_s300
