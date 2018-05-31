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

    @staticmethod
    def fromDict(data):
        cleaned_data = deepcopy(data)
        if "results" in data:
            for method, result in data["results"].items():
                if method == "PairsCombi":
                    cleaned_data["results"][method] = LocusResPairsCombi.fromDict(result)
                else:
                    cleaned_data["results"][method] = LocusRes.fromDict(result)
        return MSILocus(**cleaned_data)


class LocusRes:
    """Manage the stability status for an anlysis of a locus."""

    def __init__(self, status, score=None, data=None):
        self.status = status
        self.score = score
        self.data = {} if data is None else data

    @staticmethod
    def fromDict(data):
        cleaned_data = deepcopy(data)
        return LocusRes(**cleaned_data)


class LocusResPairsCombi(LocusRes):
    """Manage the stability status for an anlysis PairsCombi of a locus."""

    def getNbPairs(self):
        return sum(list(self.data["nb_by_length"].values()))

    def getMinLength(self):
        return min([int(elt) for elt in self.data["nb_by_length"]])

    def getMaxLength(self):
        return max([int(elt) for elt in self.data["nb_by_length"]])

    def getDensePrct(self, start=None, end=None):
        nb_pairs = self.getNbPairs()
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


class PairsCombiProcessor:
    def __init__(self, locus_id, models, evaluated, min_pairs=300, dist_method="euclidean", link_method="ward", dendro_valid_ratio=(2 / 3)):
        self.version = "1.0.0"
        self.models = models
        self.evaluated = evaluated
        self.locus_id = locus_id
        self.param = {
            'min_pairs': min_pairs,
            'dist_method': dist_method,
            'link_method': link_method,
            'dendro_valid_ratio': dendro_valid_ratio
        }
        self._used_samples = None
        self._distance_matrix = None

    def getLengthsMatrix(self):
        prct_matrix = []  # rows are sample and columns are length
        self._used_samples = list()
        min_length = math.inf
        max_length = -1
        for curr_spl in self.models + self.evaluated:
            if curr_spl.loci[self.locus_id].results["PairsCombi"].getNbPairs() >= self.param["min_pairs"]:
                min_length = min(
                    min_length,
                    curr_spl.loci[self.locus_id].results["PairsCombi"].getMinLength()
                )
                max_length = max(
                    min_length,
                    curr_spl.loci[self.locus_id].results["PairsCombi"].getMaxLength()
                )
        for curr_spl in self.models + self.evaluated:
            if curr_spl.loci[self.locus_id].results["PairsCombi"].getNbPairs() >= self.param["min_pairs"]:
                self._used_samples.append(curr_spl.name)
                prct_matrix.append(
                    curr_spl.loci[self.locus_id].results["PairsCombi"].getDensePrct(min_length, max_length)
                )
        return np.matrix(prct_matrix)

    def getDistanceMatrix(self):
        return pdist(
            self.getLengthsMatrix(),
            self.param['dist_method']
        )

    def getHierarchicalClustering(self):
        return linkage(
            self.getDistanceMatrix(),
            self.param['link_method']
        )

    def getClusters(self, nb_clusters=2):
        clusters = [[] for elt in range(nb_clusters)]
        hc_data = self.getHierarchicalClustering()
        for spl_idx, clstr_indices in enumerate(cut_tree(hc_data, nb_clusters)):
            clstr_idx = clstr_indices[0]
            clusters[clstr_idx].append(self._used_samples[spl_idx])
        return clusters

    def getDendroPlot(self, color_by_spl=None, graph_orientation="left"):
        import matplotlib.pyplot as plt
        # Build dendrogram
        hc_data = self.getHierarchicalClustering()
        dendro = dendrogram(hc_data, labels=self._used_samples, orientation=graph_orientation)
        axis = plt.gca()
        # Assignment of colors to labels
        if color_by_spl is not None:
            y_labels = axis.get_ymajorticklabels()
            for curr_label in y_labels:
                curr_label.set_color(color_by_spl[curr_label.get_text()])
        return axis

    def get2dPCAPlot(self, color_by_spl=None):
        import matplotlib.pyplot as plt
        pca = PCA(n_components=2)
        projected = pca.fit_transform(self.getLengthsMatrix())
        colors = None
        if color_by_spl is not None:
            colors = [color_by_spl[spl] for spl in self._used_samples]
        plt.scatter(projected[:, 0], projected[:, 1], color=colors)
        plt.xlabel('Component 1')
        plt.ylabel('Component 2')
        return plt

    def setLocusStatus(self):
        res_by_spl = self.getSplRes()
        for spl in self.evaluated:
            if spl.name not in res_by_spl:
                spl.loci[self.locus_id].results["PairsCombi"].status = Status.undetermined
                spl.loci[self.locus_id].results["PairsCombi"].score = None
            else:
                spl.loci[self.locus_id].results["PairsCombi"].status = res_by_spl[spl.name].status
                spl.loci[self.locus_id].results["PairsCombi"].score = res_by_spl[spl.name].score

    def getSplRes(self):
        # Get status by model spl
        status_by_model_spl = dict()
        for spl in self.models:
            status_by_model_spl[spl.name] = spl.loci[self.locus_id].results["Expected"].status
        # Get clusters fro dendrogram
        clusters = self.getClusters()
        cluster_by_spl = {spl: 0 for spl in clusters[0]}
        for spl in clusters[1]:
            cluster_by_spl[spl] = 1
        count_status_by_clstr = {
            0: {Status.instable: 0, Status.stable: 0},
            1: {Status.instable: 0, Status.stable: 0}
        }
        for spl_name, spl_status in status_by_model_spl.items():
            if spl_name in cluster_by_spl:
                clstr_id = cluster_by_spl[spl_name]
                count_status_by_clstr[clstr_id][spl_status] += 1
        # Select MSI and MSS clusters
        count_clstr_0 = count_status_by_clstr[0]
        count_clstr_1 = count_status_by_clstr[1]
        clstr_MSS_id = 0 if count_clstr_0[Status.stable] >= count_clstr_1[Status.stable] else 1
        clstr_MSI_id = 0 if count_clstr_0[Status.instable] >= count_clstr_1[Status.instable] else 1
        clstr_MSS = count_status_by_clstr[clstr_MSS_id]
        clstr_MSI = count_status_by_clstr[clstr_MSI_id]
        # Tag evaluated samples
        nb_expected_MSS = sum([1 for spl, status in status_by_model_spl.items() if status == Status.stable and spl in cluster_by_spl])
        nb_expected_MSI = sum([1 for spl, status in status_by_model_spl.items() if status == Status.instable and spl in cluster_by_spl])
        res_by_spl = {}
        if clstr_MSS_id == clstr_MSI_id or \
           clstr_MSS[Status.stable] + clstr_MSI[Status.stable] < 2 or \
           clstr_MSS[Status.instable] + clstr_MSI[Status.instable] < 2 or \
           clstr_MSS[Status.stable] / nb_expected_MSS < self.param["dendro_valid_ratio"] or \
           clstr_MSI[Status.instable] / nb_expected_MSI < self.param["dendro_valid_ratio"]:
            for spl, clstr_id in cluster_by_spl.items():
                res_by_spl[spl] = LocusRes.fromDict({
                    "status": Status.undetermined,
                    "score": None
                })
        else:
            for spl, clstr_id in cluster_by_spl.items():
                res_by_spl[spl] = LocusRes.fromDict({
                    "status": Status.stable if clstr_id == clstr_MSS_id else Status.instable,
                    "score": round(
                        (clstr_MSS[Status.stable] / nb_expected_MSS + clstr_MSI[Status.instable] / nb_expected_MSI) / 2,  # ######################## Manque la prise en compte de la distance
                        5
                    )
                })
        return res_by_spl


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
