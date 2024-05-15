import logging
import sys
from dataclasses import fields

from dto.content_item import ContentItemDto  # noqa
from dto.history_item import HistoryItemDto  # noqa
from dto.item import ItemDto
from dto.model_params_item import ModelParametersDto  # noqa
from dto.not_found_item import NotFoundDto  # noqa
from dto.user_item import UserItemDto  # noqa

logger = logging.getLogger(__name__)


def content_fields(item: ItemDto) -> set[str]:
    item_props = {f.name for f in fields(item) if f.init and not f.name.startswith("_")}
    return item_props


def update_from_props(
    item: ItemDto, database_props: dict, field_mapping: dict
) -> ItemDto:
    item_props = content_fields(item)
    for prop in item_props:
        mapped_key = field_mapping.get(prop, prop)
        if database_props.get(mapped_key):
            item.__setattr__(prop, database_props[mapped_key])
        else:
            logger.info(
                "Could not find a value for mapped dto property [" + mapped_key + "]"
            )
    return item


def dto_from_classname(
    class_name: str, position: str, item_type: str, provenance: str
) -> ItemDto:
    class_ = getattr(sys.modules[__name__], class_name)
    return class_(_position=position, _item_type=item_type, _provenance=provenance)


def dto_from_model(
    model: dict, position: str, item_type: str, provenance: str
) -> ItemDto:
    i_type = item_type + "_type"
    class_ = getattr(sys.modules[__name__], model[i_type])
    return class_(position, item_type, provenance)


def get_primary_idents(config: dict) -> tuple[str, str]:
    primary_field = config["opensearch"]["primary_field"]
    return primary_field, config["opensearch"]["field_mapping"][primary_field]
