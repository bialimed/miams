# v1.1.0 [dev]

### New functions:
  * Add possibility to use scikit-learn parameters of the selected MIAmSClassifier.
  * Add check on number of samples supporting each class (MSI/MSS) of loci after model creation in MIAmS_learn.
  * Add buttons "select all" and "unselect all" loci in lengths distribution graph in HTML report.

### Changes:
  * The default value for the parameter `--instability-ratio` of MIAmS_tag has been changed from 0.5 to 0.4.
  * The parameter `--annotations` of MIAmS_learn has changed his input format. New format example below:

        sample	B25	B26	N21
        splA	MSI	MSI	Undetermined
        splB	MSS	MSS	MSI


# v1.0.0 [2019-07-16]

  First version usable in production.
