# v1.1.0 [2019-08-08]

### New functions:
  * Add possibility to use scikit-learn parameters of the selected MIAmSClassifier.
  * Add check on number of samples supporting each class (MSI/MSS) of loci after model creation in MIAmS_learn.
  * Add buttons "select all" and "unselect all" loci in lengths distribution graph in HTML report.

### Changes:
  * The default value for the parameter `--instability-ratio` of MIAmS_tag has been changed from 0.5 to 0.4.
  * The default value for the parameter `--min-support-reads` of MIAmS_learn has been changed from 400 to 300.
  * The parameter `--annotations` of MIAmS_learn has changed his input format. New format example below:

        sample	B25	B26	N21
        splA	MSI	MSI	Undetermined
        splB	MSS	MSS	MSI


# v1.0.0 [2019-02-24]

  First version usable in production.
