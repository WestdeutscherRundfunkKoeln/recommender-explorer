from dataclasses import dataclass
from typing import Optional, Any


class ModelValidationError(Exception):
    def __init__(self, errors: list[str], model_name: str = "unknown"):
        self.errors = errors
        self.model_name = model_name
        error_message = f"Validation failed for model '{model_name}':\n" + "\n".join(f"- {error}" for error in errors)
        super().__init__(error_message)


@dataclass
class ModelDetails:
    display_name: str
    handler: str
    endpoint: str
    content_type: str
    display_in_reco_explorer: bool
    default: Optional[bool] = False
    model_name: Optional[str] = None
    model_path: Optional[str] = None
    start_color: Optional[str] = None
    reco_color: Optional[str] = None
    properties: Optional[dict[str, str]] = None
    role_arn: Optional[str] = None
    user_type: Optional[str] = None
    field_mapping: Optional[dict[str, str]] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ModelDetails':
        errors = []

        required_fields = [
            'display_name',
            'handler',
            'endpoint',
            'content_type',
        ]

        for field in required_fields:
            value = data.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                errors.append(f"Required field '{field}' is missing or empty")

        if errors:
            raise ModelValidationError(
                errors=errors,
                model_name=data.get('display_name', 'unknown')
            )

        def get_optional_str(key: str) -> Optional[str]:
            value = data.get(key)
            return value if value and value.strip() else None

        return cls(
            display_name=data.get('display_name', 'Unknown Model Name'),
            handler=data.get('handler', ''),
            endpoint=data.get('endpoint', ''),
            content_type=data.get('content_type', ''),
            default=data.get('default', False),
            model_name=get_optional_str('model_name'),
            model_path=get_optional_str('model_path'),
            display_in_reco_explorer=data.get('display_in_reco_explorer', True),
            start_color=get_optional_str('start_color'),
            reco_color=get_optional_str('reco_color'),
            properties=data.get('properties'),
            role_arn=get_optional_str('role_arn'),
            user_type=get_optional_str('user_type'),
            field_mapping=data.get('field_mapping')
        )


@dataclass
class C2CConfig:
    c2c_models: dict[str, ModelDetails]
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'C2CConfig':
        c2c_models = {}
        if 'c2c_models' in data:
            for model_key, model_data in data['c2c_models'].items():
                c2c_models[model_key] = ModelDetails.from_dict(model_data)
        return cls(c2c_models=c2c_models)

    def to_dict(self) -> dict[str, Any]:
        return {
            'c2c_models': {
                key: vars(model) for key, model in self.c2c_models.items()
            }
        }

@dataclass
class S2CConfig:
    s2c_models: dict[str, ModelDetails]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'S2CConfig':
        s2c_models = {}
        if 's2c_models' in data:
            for model_key, model_data in data['s2c_models'].items():
                s2c_models[model_key] = ModelDetails.from_dict(model_data)
        return cls(s2c_models=s2c_models)
    def to_dict(self) -> dict[str, Any]:
        return {
            's2c_models': {
                key: vars(model) for key, model in self.s2c_models.items()
            }
        }


@dataclass
class U2CConfig:
    u2c_models: dict[str, ModelDetails]
    clustering_models: Optional[dict[str, ModelDetails]] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'U2CConfig':
        u2c_models = {}
        clustering_models = {}

        if 'u2c_models' in data:
            for model_key, model_data in data['u2c_models'].items():
                u2c_models[model_key] = ModelDetails.from_dict(model_data)

        if 'clustering_models' in data:
            for model_key, model_data in data['clustering_models'].items():
                clustering_models[model_key] = ModelDetails.from_dict(model_data)

        return cls(
            u2c_models=u2c_models,
            clustering_models=clustering_models if clustering_models else None
        )

    def to_dict(self) -> dict[str, Any]:
        result = {
            'u2c_models': {
                key: vars(model) for key, model in self.u2c_models.items()
            }
        }
        if self.clustering_models:
            result['clustering_models'] = {
                key: vars(model) for key, model in self.clustering_models.items()
            }
        return result


@dataclass
class S2CConfig:
    s2c_models: dict[str, ModelDetails]
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'S2CConfig':
        s2c_models = {}
        if 's2c_models' in data:
            for model_key, model_data in data['s2c_models'].items():
                s2c_models[model_key] = ModelDetails.from_dict(model_data)
        return cls(s2c_models=s2c_models)

    def to_dict(self) -> dict[str, Any]:
        return {
            's2c_models': {
                key: vars(model) for key, model in self.s2c_models.items()
            }
        }



@dataclass
class ModelConfiguration:
    c2c_config: Optional[C2CConfig] = None
    u2c_config: Optional[U2CConfig] = None
    s2c_config: Optional[S2CConfig] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ModelConfiguration':
        config = cls()

        if 'c2c_config' in data:
            config.c2c_config = C2CConfig.from_dict(data['c2c_config'])

        if 's2c_config' in data:
            config.s2c_config = S2CConfig.from_dict(data['s2c_config'])

        if 'u2c_config' in data:
            config.u2c_config = U2CConfig.from_dict(data['u2c_config'])

        if 'clustering_models' in data:
            config.clustering_config = U2CConfig.from_dict({'models': data['clustering_models']})

        if 's2c_config' in data:
            config.s2c_config = S2CConfig.from_dict(data['s2c_config'])

        return config

    def to_dict(self) -> dict[str, Any]:
        result = {}

        if self.c2c_config:
            result['c2c_config'] = {
                'c2c_models': {
                    key: {key: value for key, value in vars(model).items() if value is not None}
                    for key, model in self.c2c_config.c2c_models.items()
                }
            }

        if self.s2c_config:
            result['s2c_config'] = {
                's2c_models': {
                    key: {key: value for key, value in vars(model).items() if value is not None}
                    for key, model in self.s2c_config.s2c_models.items()
                }
            }


        if self.u2c_config:
            result['u2c_config'] = {
                'u2c_models': {
                    key: {key: value for key, value in vars(model).items() if value is not None}
                    for key, model in self.u2c_config.u2c_models.items()
                }
            }
            if self.u2c_config.clustering_models:
                result['u2c_config']['clustering_models'] = {
                    key: {key: value for key, value in vars(model).items() if value is not None}
                    for key, model in self.u2c_config.clustering_models.items()
                }

        if self.s2c_config:
            result['s2c_config'] = {
                's2c_models': {
                    key: {key: value for key, value in vars(model).items() if value is not None}
                    for key, model in self.s2c_config.s2c_models.items()
                }
            }

        return result
