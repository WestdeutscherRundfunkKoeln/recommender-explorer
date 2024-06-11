import collections
import pytest
from opensearchpy import OpenSearch
from src.model.opensearch.nn_seeker_opensearch import NnSeekerOpenSearch
from src.dto.content_item import ContentItemDto


@pytest.fixture
def mock_opensearch(mocker):
    def mock_search(*args, **kwargs):
        if "bool" in kwargs["body"]["query"]:
            return {
                "hits": {
                    "hits": [
                        {
                            "_source": {
                                "embedding_01": [1, 2],
                            }
                        }
                    ]
                }
            }
        return {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "id": "test",
                        },
                        "_score": 0.5,
                    }
                ]
            }
        }

    mock_os = mocker.Mock(OpenSearch)
    mock_os.search.side_effect = mock_search
    return mock_os


@pytest.fixture
def nn_seeker(mock_opensearch):
    return NnSeekerOpenSearch(
        client=mock_opensearch,
        target_idx_name="test",
        field_mapping={"created": "created"},
        base_url_embedding="test",
        api_key="test",
    )


def test_get_k_nn__by_id__no_filter(nn_seeker):
    item = ContentItemDto(
        _position="1",
        _item_type="test",
        _provenance="test",
        id="test",
    )

    nn_seeker.get_k_NN(item=item, k=1, nn_filter={})

    assert nn_seeker.client.search.call_count == 2
    assert nn_seeker.client.search.call_args_list[1].kwargs == {
        "body": {
            "size": 1,
            "_source": {"include": "id"},
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "knn_score",
                        "lang": "knn",
                        "params": {
                            "field": "embedding_01",
                            "query_value": [1, 2],
                            "space_type": "cosinesimil",
                        },
                    },
                }
            },
        },
        "index": "test",
    }


def test_get_k_nn__by_id__neutral_element_filter_values(nn_seeker):
    item = ContentItemDto(
        _position="1",
        _item_type="test",
        _provenance="test",
        id="test",
    )

    nn_seeker.get_k_NN(
        item=item,
        k=1,
        nn_filter={
            "test_filter_null": None,
            "test_filter_empty": "",
            "test_filter_false": False,
            "test_filter_zero": 0,
            "test_filter_empty_list": [],
            "test_filter_empty_dict": {},
            "test_filter_empty_set": set(),
            "test_filter_empty_tuple": tuple(),
        },
    )

    assert nn_seeker.client.search.call_count == 2
    assert nn_seeker.client.search.call_args_list[1].kwargs == {
        "body": {
            "size": 1,
            "_source": {"include": "id"},
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "knn_score",
                        "lang": "knn",
                        "params": {
                            "field": "embedding_01",
                            "query_value": [1, 2],
                            "space_type": "cosinesimil",
                        },
                    },
                }
            },
        },
        "index": "test",
    }


def test_get_k_nn__by_id__multiple_filter(nn_seeker):
    item = ContentItemDto(
        _position="1",
        _item_type="test",
        _provenance="test",
        id="test",
        duration=1337,
    )

    nn_seeker.get_k_NN(
        item=item,
        k=1,
        nn_filter={
            "sort_test": "test",
            "clean_test": "clean_test",
            "termfilter_genre": "same_genre",
            "termfilter_show": "different_show",
            "termfilter_subgenre": "mixed_subgenre",
            "termfilter_theme": "same_theme",
            "termfilter_subgenrecoose": "choose_subgenre",
            "value_subgenreCategories": ["testSubCat1", "testSubCat2"],
            "termfilter_inhalt": "choose_inhalt",
            "value_inhaltCategory": ["categories_live"],
            "termfilter_erzählweise": "choose_erzählweise",
            "value_erzaehlweiseCategory": ["categories_live"],
            "value_genreCategory": None,
            "rangefilter_test": {"duration": {"gte": 60}},
            "relativerangefilter_duration": 0.5,
            "blacklist_id": "test_id1, test_id2",
        },
    )

    assert nn_seeker.client.search.call_count == 2
    assert nn_seeker.client.search.call_args_list[1].kwargs == {
        "body": {
            "size": 1,
            "sort": [{"created": {"order": "test"}}],
            "track_scores": True,
            "_source": {"include": "id"},
            "query": {
                "script_score": {
                    "query": {
                        "bool": {
                            "filter": {
                                "script": {
                                    "script": {
                                        "source": "doc['clean_test.keyword'].length > 0"
                                    }
                                }
                            },
                            "": [{"terms": {"subgenreCategories.keyword": [""]}}],
                            "must_not": [
                                {"terms": {"showId.keyword": [""]}},
                                {"terms": {"id.keyword": ["test_id1", "test_id2"]}},
                            ],
                            "must": [
                                {"terms": {"genreCategory.keyword": [""]}},
                                {"terms": {"thematicCategories.keyword": [""]}},
                                {
                                    "terms": {
                                        "subgenreCategories.keyword": [
                                            "testSubCat1",
                                            "testSubCat2",
                                        ]
                                    }
                                },
                                {
                                    "terms": {
                                        "subgenreCategories.keyword": [
                                            "Live-Festakt",
                                            "Live-Gottesdienst",
                                            "Live-Interview",
                                            "Live-Konzert",
                                            "Live-Sport",
                                            "Live-Theater",
                                            "Live-Lesung",
                                        ]
                                    }
                                },
                                {
                                    "terms": {
                                        "genreCategory.keyword": [
                                            "Live",
                                            "ReLive",
                                        ]
                                    }
                                },
                                {"range": {"duration": {"gte": 60}}},
                                {"range": {"duration": {"lte": 668.5}}},
                            ],
                        }
                    },
                    "script": {
                        "source": "knn_score",
                        "lang": "knn",
                        "params": {
                            "field": "embedding_01",
                            "query_value": [1, 2],
                            "space_type": "cosinesimil",
                        },
                    },
                }
            },
        },
        "index": "test",
    }
