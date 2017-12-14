# coding=utf-8

# Author: Rafael Menelau Oliveira e Cruz <rafaelmenelau@gmail.com>
#
# License: BSD 3 clause

import numpy as np

from pythonds.dcs.base import DCS


class APosteriori(DCS):
    """A Posteriori Dynamic classifier selection.
    
    This method works similarly to the LCA technique. The only difference is that it uses
    the scores obtained by the base classifiers as well as the distance between the test sample
    and each pattern in the region of competence are also considered in the competence estimation.

    Parameters
    ----------
    pool_classifiers : list of classifiers
                       The generated_pool of classifiers trained for the corresponding classification problem.
                       The classifiers should support methods "predict" and "predict_proba".

    k : int (Default = 7)
        Number of neighbors used to estimate the competence of the base classifiers.

    DFP : Boolean (Default = False)
          Determines if the dynamic frienemy pruning is applied.

    with_IH : Boolean (Default = False)
              Whether the hardness level of the region of competence is used to decide
              between using the DS algorithm or the KNN for classification of a given query sample.

    safe_k : int (default = None)
             The size of the indecision region.

    IH_rate : float (default = 0.3)
              Hardness threshold. If the hardness level of the competence region is lower than
              the IH_rate the KNN classifier is used. Otherwise, the DS algorithm is used for classification.

    aknn : Boolean (Default = False)
           Determines the type of KNN algorithm that is used. Set to true for the A-KNN method.

    selection_method : String (Default = "best")
                       Determines which method is used to select the base classifier
                       after the competences are estimated.

    diff_thresh : float (Default = 0.1)
                  Threshold to measure the difference between the competence level of the base
                  classifiers for the random and diff selection schemes. If the difference is lower than the
                  threshold, their performance are considered equivalent.

    References
    ----------
    G. Giacinto and F. Roli, Methods for Dynamic Classifier Selection
    10th Int. Conf. on Image Anal. and Proc., Venice, Italy (1999), 659-664.

    Ko, Albert HR, Robert Sabourin, and Alceu Souza Britto Jr. "From dynamic classifier selection to dynamic ensemble
    selection." Pattern Recognition 41.5 (2008): 1718-1731.

    Britto, Alceu S., Robert Sabourin, and Luiz ES Oliveira. "Dynamic selection of classifiers—a comprehensive review."
    Pattern Recognition 47.11 (2014): 3665-3680.

    R. M. O. Cruz, R. Sabourin, and G. D. Cavalcanti, “Dynamic classifier selection: Recent advances and perspectives,”
    Information Fusion, vol. 41, pp. 195 – 216, 2018.

    """
    def __init__(self, pool_classifiers, k=7, DFP=False, with_IH=False, safe_k=None, IH_rate=0.30,
                 aknn=False, selection_method='diff', diff_thresh=0.1):

        super(APosteriori, self).__init__(pool_classifiers, k, DFP=DFP, with_IH=with_IH, safe_k=safe_k, IH_rate=IH_rate,
                                          aknn=aknn,
                                          selection_method=selection_method,
                                          diff_thresh=diff_thresh)
        self.name = 'A Posteriori'

    def fit(self, X, y):
        super(APosteriori, self).fit(X, y)
        self.dsel_scores = self._preprocess_dsel_scores()
        return self

    def estimate_competence(self, query):
        """estimate the competence of each base classifier ci
        the classification of the query sample using the A Posteriori method.

        The A Posteriori method considers the probability of correct classification of the base classifier
        ci, taking into account the supports obtained by the base classifier ci for the samples belonging to the
        region of competence. The probability of correct classification for a base classifier ci is calculated taking
        into account only the samples in the region of competence from a specific class wl. In this case, wl is the
        predict class of the base classifier ci for the query sample.

        This method also weights the influence of each training sample according to its Euclidean distance to the
        query instance. The closest samples have a higher influence in the computation of the competence level.


        Returns an array containing the level of competence estimated using the LCA method
        for each base classifier. The size of the array is equals to the size of the pool of classifiers.

        Parameters
        ----------
        query : array containing the test sample = [n_features]

        Returns
        -------
        competences : array = [n_classifiers] containing the competence level estimated
        for each base classifier
        """
        dists, idx_neighbors = self._get_region_competence(query, k=self.n_samples)
        competences = np.zeros(self.n_classifiers)

        for clf_index, clf in enumerate(self.pool_classifiers):

            # Check if the dynamic frienemy pruning (DFP) should be used used
            if self.mask[clf_index]:
                result = []
                predicted_label = clf.predict(query)
                counter = 0
                dists_temp = np.zeros(self.k)
                for index_neighbor in idx_neighbors:
                    # Get only neighbors from the same class as predicted by the
                    # classifier (clf) to form the region of competence
                    target = self.DSEL_target[index_neighbor]
                    if target == predicted_label[0]:
                        # weight by distance
                        post_prob = self._get_scores_dsel(clf_index, index_neighbor)[target]
                        result.append(post_prob * dists[index_neighbor])
                        dists_temp[counter] = dists[index_neighbor]
                        counter += 1
                    if counter >= self.k:
                        break
                competences[clf_index] = sum(result)/sum(dists_temp)

        return competences