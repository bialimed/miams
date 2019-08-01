# Add supplementary scikit-learn classifiers

This page describes how you can add your own scikit-learn classifier in MIAmS_tag.

**Prerequisite**: the classifier must implement the method predict_proba.

## 1. Add import 

Add your scikit-learn library in imports section of `${APP_DIR}/jflow/workflows/MIAmS_tag/bin/miamsClassify.py`.
	
## 2. Add your classifier class name in argparse choices

  * The script executing the classification: `${APP_DIR}/jflow/workflows/MIAmS_tag/bin/miamsClassify.py`


        self.add_parameter("classifier", "The classifier used to predict loci status.", choices=["DecisionTree", "KNeighbors", "LogisticRegression", "RandomForest", "SVC"], default="SVC", group="Locus classification parameters")
                                                                                                                                                                          ^
                                                                                                                                                                          |
                                                                                                                                                                          Your new classifier class name here
		
  * The wrapper for the previous script: `${APP_DIR}/jflow/workflows/MIAmS_tag/components/miamsClassify.py`

        self.add_parameter("classifier", "The classifier used to predict loci status.", choices=["DecisionTree", "KNeighbors", "LogisticRegression", "RandomForest", "SVC"], default=classifier)
                                                                                                                                                                          ^
                                                                                                                                                                          |
                                                                                                                                                                          Your new classifier class name here

  * The workflow script: `${APP_DIR}/jflow/workflows/MIAmS_tag/__init__.py`

        self.add_parameter("classifier", "The classifier used to predict loci status.", choices=["DecisionTree", "KNeighbors", "LogisticRegression", "RandomForest", "SVC"], default="SVC", group="Locus classification parameters")
                                                                                                                                                                          ^
                                                                                                                                                                          |
                                                                                                                                                                          Your new classifier class name here

## 3. Manage specific behaviour (optional)

This step is only necessary if your classifier has a particularity to use predict_proba or if it does not accept random_state argument.

Add your class instanciation and arguments management in `${APP_DIR}/jflow/workflows/MIAmS_tag/bin/miamsClassify.py`. See SVC and KNeighbors in following example:

    def _getClassifier(self, clf, clf_params):
        clf_obj = None
        if clf == "SVC":  # The argument "probability"" must be set to True for use predict_proba()
            clf_params["probability"] = True
            clf_obj = SVC(**clf_params)
        elif clf == "KNeighbors":  # The KNeighbors does not accept the argument "random_state"
            if "random_state" in clf_params:
	            del clf_params["random_state"]
            clf_obj = KNeighborsClassifier(**clf_params)
        else:
            try:
                clf_obj = globals()[clf](**clf_params)
            except:
                raise Exception('The classifier "{}" is not implemented in MIAmSClassifier.'.format(clf))
        return clf_obj