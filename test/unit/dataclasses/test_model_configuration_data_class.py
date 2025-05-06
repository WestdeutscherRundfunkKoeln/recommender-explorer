import pytest
from src.util.dataclasses.model_configuration_data_class import (
    ModelConfiguration,
    C2CConfig,
    U2CConfig,
    ModelDetails,
    ModelValidationError,
)

@pytest.fixture
def valid_model_data():
    return {
        "display_name": "Test Model",
        "handler": "test_handler",
        "endpoint": "test_endpoint",
        "content_type": "test_type",
    }

def test_model_configuration_init():
    config = ModelConfiguration()
    assert config.c2c_config is None
    assert config.u2c_config is None

def test_model_configuration_from_dict(valid_model_data):
    data = {
        "c2c_config": {
            "c2c_models": {
                "model1": valid_model_data
            }
        },
        "u2c_config": {
            "u2c_models": {
                "model2": valid_model_data
            }
        }
    }
    config = ModelConfiguration.from_dict(data)
    assert config.c2c_config is not None
    assert config.u2c_config is not None

def test_model_configuration_to_dict(valid_model_data):
    data = {
        "c2c_config": {
            "c2c_models": {
                "model1": valid_model_data
            }
        }
    }
    config = ModelConfiguration.from_dict(data)
    result = config.to_dict()
    assert "c2c_config" in result
    assert "c2c_models" in result["c2c_config"]

def test_c2c_config_init():
    model = ModelDetails(
        display_name="Test Model",
        handler="test_handler",
        endpoint="test_endpoint",
        content_type="test_type",
        display_in_reco_explorer=True
    )
    config = C2CConfig(c2c_models={"model1": model})
    assert len(config.c2c_models) == 1
    assert "model1" in config.c2c_models

def test_c2c_config_from_dict(valid_model_data):
    data = {
        "c2c_models": {
            "model1": valid_model_data
        }
    }
    config = C2CConfig.from_dict(data)
    assert len(config.c2c_models) == 1
    assert isinstance(config.c2c_models["model1"], ModelDetails)

def test_c2c_config_to_dict(valid_model_data):
    data = {
        "c2c_models": {
            "model1": valid_model_data
        }
    }
    config = C2CConfig.from_dict(data)
    result = config.to_dict()
    assert "c2c_models" in result
    assert "model1" in result["c2c_models"]
    assert result["c2c_models"]["model1"]["display_name"] == "Test Model"

def test_u2c_config_init():
    model = ModelDetails(
        display_name="Test Model",
        handler="test_handler",
        endpoint="test_endpoint",
        content_type="test_type",
        display_in_reco_explorer=True
    )
    config = U2CConfig(u2c_models={"model1": model})
    assert len(config.u2c_models) == 1
    assert config.clustering_models is None

def test_u2c_config_from_dict(valid_model_data):
    data = {
        "u2c_models": {
            "model1": valid_model_data
        },
        "clustering_models": {
            "cluster1": valid_model_data
        }
    }
    config = U2CConfig.from_dict(data)
    assert len(config.u2c_models) == 1
    assert len(config.clustering_models) == 1

def test_u2c_config_to_dict(valid_model_data):
    data = {
        "u2c_models": {
            "model1": valid_model_data
        },
        "clustering_models": {
            "cluster1": valid_model_data
        }
    }
    config = U2CConfig.from_dict(data)
    result = config.to_dict()
    assert "u2c_models" in result
    assert "clustering_models" in result

def test_model_details_init():
    model = ModelDetails(
        display_name="Test Model",
        handler="test_handler",
        endpoint="test_endpoint",
        content_type="test_type",
        display_in_reco_explorer=True
    )
    assert model.display_name == "Test Model"
    assert model.handler == "test_handler"
    assert model.endpoint == "test_endpoint"
    assert model.content_type == "test_type"
    assert model.display_in_reco_explorer is True
    assert model.default is False
    assert model.model_name is None

def test_model_details_from_dict_required_fields():
    # Test with all required fields
    data = {
        "display_name": "Test Model",
        "handler": "test_handler",
        "endpoint": "test_endpoint",
        "content_type": "test_type",
    }
    model = ModelDetails.from_dict(data)
    assert model.display_name == "Test Model"
    assert model.display_in_reco_explorer is True

def test_model_details_from_dict_missing_required():
    data = {
        "display_name": "Test Model",
        "handler": "",
        "endpoint": "test_endpoint",
        "content_type": "test_type",
    }
    with pytest.raises(ModelValidationError) as exc_info:
        ModelDetails.from_dict(data)
    assert "handler" in str(exc_info.value)

def test_model_details_from_dict_optional_fields():
    data = {
        "display_name": "Test Model",
        "handler": "test_handler",
        "endpoint": "test_endpoint",
        "content_type": "test_type",
        "model_name": "test_model",
        "start_color": "#FFFFFF",
        "properties": {"key": "value"}
    }
    model = ModelDetails.from_dict(data)
    assert model.model_name == "test_model"
    assert model.start_color == "#FFFFFF"
    assert model.properties == {"key": "value"}

def test_model_details_empty_optional_strings():
    data = {
        "display_name": "Test Model",
        "handler": "test_handler",
        "endpoint": "test_endpoint",
        "content_type": "test_type",
        "model_name": "",
        "start_color": "  ",
    }
    model = ModelDetails.from_dict(data)
    assert model.model_name is None
    assert model.start_color is None