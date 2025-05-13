from src.util.dataclasses.opensearch_configuration_data_class import OpenSearchConfiguration

def test_opensearch_configuration_init():
    config = OpenSearchConfiguration()
    assert config.index is None

    config = OpenSearchConfiguration(index="test_index")
    assert config.index == "test_index"

def test_opensearch_configuration_from_dict():
    config = OpenSearchConfiguration.from_dict({})
    assert config.index is None

    config = OpenSearchConfiguration.from_dict({"opensearch": {}})
    assert config.index is None

    config = OpenSearchConfiguration.from_dict({
        "opensearch": {"index": "test_index"}
    })
    assert config.index == "test_index"

    config = OpenSearchConfiguration.from_dict({
        "opensearch": "not_a_dict"
    })
    assert config.index is None

def test_opensearch_configuration_to_dict():
    config = OpenSearchConfiguration()
    assert config.to_dict() == {}

    config = OpenSearchConfiguration(index="test_index")
    expected = {"opensearch": {"index": "test_index"}}
    assert config.to_dict() == expected
