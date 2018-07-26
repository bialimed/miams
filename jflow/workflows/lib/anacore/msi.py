import math
import json
import numpy as np
from copy import deepcopy
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import linkage, dendrogram, cut_tree
from sklearn.decomposition import PCA


def toDict(msi_object):
    """
    Retuns a dictionary representing the object. This method is used in json.dump in argument named "default" for recursively convert an object to json.

    :param msi_object: The object to convert.
    :type msi_object: a class of anacore.msi library.
    :return: The dictionary representing the object.
    :rtype: dict
    """
    return msi_object.__dict__


class Status:
    """Status for samples (MSISplRes) and loci (LocusRes) in anacore.msi library."""
    stable = "MSS"
    instable = "MSI"
    undetermined = "Undetermined"
    none = None

    @staticmethod
    def authorizedValues():
        """Return the values authorized for stability status."""
        return [attr_value for attr_name, attr_value in Status.__dict__.items() if attr_name != "authorizedValues" and not attr_name.startswith("__")]


class MSILocus:
    """Manage a locus of a microsatellite (name, position and stability status)."""

    def __init__(self, position, name=None, results=None):
        self.position = position
        self.name = name
        self.results = {} if results is None else results

    def addMethods(self, method):
        method_name = method.__class__.__name__
        if not method_name.startswith("LocusRes"):
            raise Exception('The class "{}" cannot be used as an method for MSILocus.'.format(method_name))
        method_name = method_name[6:]
        if method_name in self.results:
            raise Exception('The result with method "{}" already exist for MSILocus "{}".'.format(method_name, self.position))
        self.results[method_name] = method

    def delMethod(self, method_id):
        self.results.pop(method_id, None)

    @staticmethod
    def fromDict(data):
        cleaned_data = deepcopy(data)
        if "results" in data:
            for method, result in data["results"].items():
                if "_class" in result and result["_class"] == "LocusResPairsCombi":
                    cleaned_data["results"][method] = LocusResPairsCombi.fromDict(result)
                elif "_class" in result and result["_class"] == "LocusResDistrib":
                    cleaned_data["results"][method] = LocusResDistrib.fromDict(result)
                else:
                    cleaned_data["results"][method] = LocusRes.fromDict(result)
        return MSILocus(**cleaned_data)


class LocusRes:
    """Manage the stability status for an anlysis of a locus."""

    def __init__(self, status, score=None, data=None):
        self._class = "LocusRes"
        self.status = status
        self.score = score
        self.data = {} if data is None else data

    @staticmethod
    def fromDict(data):
        cleaned_data = deepcopy(data)
        if "_class" in cleaned_data:
            cleaned_data.pop("_class", None)
        return LocusRes(**cleaned_data)


class LocusResDistrib(LocusRes):
    """Manage the stability status for an anlysis of a locus containing the count by length."""

    def __init__(self, status, score=None, data=None):
        super().__init__(status, score, data)
        self._class = "LocusResDistrib"

    def getCount(self):
        return sum(list(self.data["nb_by_length"].values()))

    def getMinLength(self):
        return min([int(elt) for elt in self.data["nb_by_length"]])

    def getMaxLength(self):
        return max([int(elt) for elt in self.data["nb_by_length"]])

    def getDensePrct(self, start=None, end=None):
        nb_pairs = self.getCount()
        dense_prct = list()
        for curr_count in self.getDenseCount(start, end):
            prct = None
            if nb_pairs != 0:
                prct = (curr_count * 100) / nb_pairs
            dense_prct.append(prct)
        return dense_prct

    def getDenseCount(self, start=None, end=None):
        if start is None:
            start = self.getMinLength()
        if end is None:
            end = self.getMaxLength()
        dense_count = list()
        for curr_length in range(start, end + 1):
            count = 0
            if str(curr_length) in self.data["nb_by_length"]:
                count = self.data["nb_by_length"][str(curr_length)]
            dense_count.append(count)
        return dense_count

    @staticmethod
    def fromDict(data):
        cleaned_data = deepcopy(data)
        if "_class" in cleaned_data:
            cleaned_data.pop("_class", None)
        return LocusResDistrib(**cleaned_data)


class LocusResPairsCombi(LocusResDistrib):
    """Manage the stability status for an anlysis after reads pair combination of a locus."""

    def __init__(self, status, score=None, data=None):
        super().__init__(status, score, data)
        self._class = "LocusResPairsCombi"

    def getNbFrag(self):
        return self.getCount()

    @staticmethod
    def fromDict(data):
        cleaned_data = deepcopy(data)
        if "_class" in cleaned_data:
            cleaned_data.pop("_class", None)
        return LocusResPairsCombi(**cleaned_data)


class MSISplRes:
    """Manage the stability status for an anlysis of a sample."""

    def __init__(self, status, method=None, score=None, param=None, version=None):
        self.status = status
        self.method = method
        self.score = score
        self.param = param
        self.version = version

    @staticmethod
    def fromDict(data):
        cleaned_data = deepcopy(data)
        return MSISplRes(**cleaned_data)


class MSISample:
    def __init__(self, name, loci=None, results=None):
        self.name = name
        self.loci = {} if loci is None else loci
        self.results = {} if results is None else results

    def getLociMethods(self):
        methods = set()
        for curr_locus in self.loci:
            for curr_method in self.results.keys():
                methods.add(curr_method)
        return methods

    def addLocus(self, locus):
        if locus.__class__.__name__ != "MSILocus":
            raise Exception('The class "{}" cannot be used as locus for MSISample.'.format(locus.__class__.__name__))
        self.loci[locus.position] = locus

    def delLoci(self, locus_ids):
        for locus_id in locus_ids:
            self.delLocus(locus_id)

    def delLocus(self, locus_id):
        self.loci.pop(locus_id, None)

    def _getStatusByMethod(self, method):
        status = list()
        for locus_id, locus in self.loci.items():
            if method in locus.results:
                status.append(locus.results[method].status)
        return status

    def getNbUnstable(self, method):
        """
        @summary: Returns the number of instable loci for the sample.
        @return: [int] The number of instable loci.
        """
        nb_unstable = 0
        status = self._getStatusByMethod(method)
        for curr_status in status:
            if curr_status is not None and curr_status == Status.instable:
                nb_unstable += 1
        return nb_unstable

    def getNbStable(self, method):
        """
        @summary: Returns the number of stable loci for the sample.
        @return: [int] The number of stable loci.
        """
        nb_stable = 0
        status = self._getStatusByMethod(method)
        for curr_status in status:
            if curr_status is not None and curr_status == Status.stable:
                nb_stable += 1
        return nb_stable

    def getNbUndetermined(self, method):
        """
        @summary: Returns the number of where the status is undetermined after evaluation.
        @return: [int] The number of undetermined loci.
        """
        nb_undetermined = 0
        status = self._getStatusByMethod(method)
        for curr_status in status:
            if curr_status is not None and curr_status == Status.undetermined:
                nb_undetermined += 1
        return nb_undetermined

    def getNbUsable(self, method):
        """
        @summary: Returns the number of loci usable in MSI evaluation for the sample.
        @return: [int] The number of instable loci.
        """
        nb_usable = 0
        status = self._getStatusByMethod(method)
        for curr_status in status:
            if curr_status is not None and curr_status != Status.undetermined:
                nb_usable += 1
        return nb_usable

    def getNbProcessed(self, method):
        """
        @summary: Returns the number of loci where the status has been evaluated for the sample.
        @return: [int] The number of processed loci.
        """
        nb_processed = 0
        status = self._getStatusByMethod(method)
        for curr_status in status:
            if curr_status is not None:
                nb_processed += 1
        return nb_processed

    def getNbLoci(self):
        """
        @summary: Returns the number of loci in the sample.
        @return: [int] The number of loci.
        """
        return len(self.loci)

    @staticmethod
    def fromDict(data):
        cleaned_data = deepcopy(data)
        # Loci
        if "loci" in data:
            cleaned_data["loci"] = dict()
            for locus_id, locus in data["loci"].items():
                cleaned_data["loci"][locus_id] = MSILocus.fromDict(locus)
        # Results
        if "results" in data:
            for method, result in data["results"].items():
                cleaned_data["results"] = {
                    method: MSISplRes.fromDict(result)
                }
        # Name
        return MSISample(**cleaned_data)

    def _getScoreCalculation(self, eval_status, method, undetermined_ratio=(1 / 2)):
        scores = list()
        nb_loci_undetermined = 0
        for locus_id, locus in self.loci.items():
            if locus.results[method].status is not None:
                if locus.results[method].status == Status.undetermined:
                    nb_loci_undetermined += 1
                else:
                    if locus.results[method].status == eval_status:
                        if locus.results[method].score is not None:
                            scores.append(locus.results[method].score)
                        else:
                            scores.append(1)
                    elif locus.results[method].status != Status.undetermined:
                        if locus.results[method].score is not None:
                            scores.append(1 - locus.results[method].score)
                        else:
                            scores.append(0)
        score = None
        if len(scores) != 0:
            score = sum(scores) / (len(scores) + nb_loci_undetermined * undetermined_ratio)
        return round(score, 5)

    def setStatus(self, method):
        result = MSISplRes.fromDict({
            'status': Status.undetermined,
            'method': "majority",
            'score': None,
            'param': None,
            'version': "1.0.0"
        })
        nb_stable = self.getNbStable(method)
        nb_unstable = self.getNbUnstable(method)
        if nb_stable + nb_unstable > 0:
            if nb_stable > nb_unstable:
                result.status = Status.stable
                result.score = self._getScoreCalculation(Status.stable, method)
            elif nb_stable < nb_unstable:
                result.status = Status.instable
                result.score = self._getScoreCalculation(Status.instable, method)
            else:
                result.status = Status.undetermined
                result.score = None
        self.results[method] = result


class LocusClassifier:
    """
    clf = LocusClassifier(locus_id, method_name, classifier)
    clf.fit(train_dataset)
    clf.predict(test_dataset)
    clf.predict_proba(test_dataset)


    clf = LocusClassifier(locus_id, method_name, classifier)
    clf.fit(train_dataset)
    clf.set_status(test_dataset)
    """
    def __init__(self, locus_id, method_name, classifier, model_method_name="model"):
        self.locus_id = locus_id
        self.method_name = method_name
        self.model_method_name = model_method_name
        self.classifier = classifier
        self._train_dataset = []
        self._usable_train_dataset = []
        self._test_dataset = []
        self._min_len = None
        self._max_len = None

    def _get_min_max_len(self, dataset, method):
        min_len = math.inf
        max_len = -1
        for curr_spl in dataset:
            locus_res = curr_spl.loci[self.locus_id].results[method]
            min_len = min(min_len, locus_res.getMinLength())
            max_len = max(max_len, locus_res.getMaxLength())
        return min_len, max_len

    def _set_min_max_len(self):
        train_min, train_max = self._get_min_max_len(self._usable_train_dataset, self.model_method_name)
        test_min, test_max = self._get_min_max_len(self._test_dataset, self.method_name)
        self._min_len = min(train_min, test_min)
        self._max_len = max(train_max, test_max)

    def _get_data(self, dataset, method):
        prct_matrix = []  # rows are sample and columns are length
        if self._min_len is None and self._max_len is None:
            self._set_min_max_len()
        for curr_spl in dataset:
            locus_res = curr_spl.loci[self.locus_id].results[method]
            prct_matrix.append(
                locus_res.getDensePrct(self._min_len, self._max_len)
            )
        return np.matrix(prct_matrix)

    def _get_test_data(self):
        return self._get_data(self._test_dataset, self.method_name)

    def _get_train_data(self):
        return self._get_data(self._usable_train_dataset, self.model_method_name)

    def _get_train_labels(self):
        labels = []
        for curr_spl in self._usable_train_dataset:
            locus_res = curr_spl.loci[self.locus_id].results[self.model_method_name]
            labels.append(locus_res.status)
        return np.array(labels)

    def fit(self, train_dataset):
        self._train_dataset = train_dataset
        self._usable_train_dataset = [spl for spl in train_dataset if self.model_method_name in spl.loci[self.locus_id].results]
        self.classifier.fit(self._get_train_data(), self._get_train_labels())

    def predict(self, test_dataset):
         # ##################################################### must be filtered
        self._test_dataset = test_dataset
        test_min_len, test_max_len = self._get_min_max_len(self._test_dataset, self.method_name)
        if test_min_len < self._min_len or test_max_len > self._max_len:
            self.fit(self._train_dataset)
        return self.classifier.predict(self._get_test_data())

    def predict_proba(self, test_dataset):
         # ##################################################### must be filtered
        self._test_dataset = test_dataset
        return self.classifier.predict_proba(self._get_test_data())

    def _get_scores(self, pred_labels):
        scores = None
        proba_idx_by_label = {label: idx for idx, label in enumerate(self.classifier.classes_)}
        try:
            proba = self.predict_proba(self._test_dataset)
            scores = [spl_proba[proba_idx_by_label[spl_label]] for spl_proba, spl_label in zip(proba, pred_labels)]
        except Exception:
            scores = [None for spl in self._test_dataset]
        return scores

    def set_status(self, test_dataset):
         # ##################################################### must be filtered
        self._test_dataset = test_dataset
        pred_labels = self.predict(test_dataset)
        pred_scores = self._get_scores(pred_labels)
        for label, score, sample in zip(pred_labels, pred_scores, self._test_dataset):
            locus_res = sample.loci[self.locus_id].results[self.method_name]
            locus_res.status = label
            locus_res.score = score


class MSIReport:
    @staticmethod
    def parse(in_path):
        spl_data = []
        with open(in_path) as FH_in:
            spl_data = json.load(FH_in)
        return [MSISample.fromDict(curr_spl) for curr_spl in spl_data]

    @staticmethod
    def write(msi_samples, out_path):
        with open(out_path, "w") as FH_out:
            json.dump(msi_samples, FH_out, sort_keys=True, default=toDict)
