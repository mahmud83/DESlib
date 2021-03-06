import pytest
from sklearn.linear_model import Perceptron

from deslib.des.des_p import DESP
from deslib.tests.examples_test import *
from sklearn.utils.estimator_checks import check_estimator


def test_check_estimator():
    check_estimator(DESP)


# Test the estimate competence method receiving n samples as input
def test_estimate_competence_batch():
    query = np.ones((3, 2))
    expected = np.array([[0.57142857, 0.4285714, 0.57142857],
                         [0.71428571, 0.2857142, 0.71428571],
                         [0.2857142, 0.71428571, 0.2857142]])

    des_p_test = DESP(create_pool_classifiers())
    des_p_test.fit(X_dsel_ex1, y_dsel_ex1)
    neighbors = neighbors_ex1
    distances = distances_ex1
    competences = des_p_test.estimate_competence(query, neighbors, distances)
    assert np.allclose(competences, expected, atol=0.01)


@pytest.mark.parametrize('index, expected', [(0, [[True, False, True]]),
                                             (1, [[True, False, True]]),
                                             (2, [[False, True, False]])])
def test_select_two_classes(index, expected):
    query = np.atleast_2d([1, 1])

    des_p_test = DESP(create_pool_classifiers())
    des_p_test.fit(X_dsel_ex1, y_dsel_ex1)

    neighbors = neighbors_ex1[index, :].reshape(1, -1)
    distances = distances_ex1[index, :].reshape(1, -1)

    competences = des_p_test.estimate_competence(query, neighbors, distances)
    selected = des_p_test.select(competences)

    assert np.array_equal(selected, expected)


# In this example, since the number of classes is 3, the competence level
# expected to be selected is > 0.33
@pytest.mark.parametrize('index, expected', [(0, [[True, True, True]]),
                                             (1, [[True, False, True]]),
                                             (2, [[False, True, False]])])
def test_select_three_classes(index, expected):
    query = np.atleast_2d([1, 1])

    des_p_test = DESP(create_pool_classifiers())
    des_p_test.fit(X_dsel_ex1, y_dsel_ex1)

    des_p_test.n_classes_ = 3
    neighbors = neighbors_ex1[index, :].reshape(1, -1)
    distances = distances_ex1[index, :].reshape(1, -1)

    competences = des_p_test.estimate_competence(query, neighbors, distances)
    selected = des_p_test.select(competences)

    assert np.array_equal(selected, expected)


def test_select_none_competent():
    n_classifiers = 3
    des_p_test = DESP(create_pool_classifiers())
    des_p_test.n_classes_ = 2
    competences = np.ones(n_classifiers) * 0.49
    indices = des_p_test.select(competences)
    expected = np.array([[True, True, True]])
    assert np.array_equal(expected, indices)


# Test if the class is raising an error when the base classifiers do not
# implements the predict_proba method.
# In this case the test should not raise an error since this class does not
# require base classifiers that can estimate probabilities
def test_predict_proba():
    X = X_dsel_ex1
    y = y_dsel_ex1
    clf1 = Perceptron()
    clf1.fit(X, y)
    DESP([clf1, clf1]).fit(X, y)
