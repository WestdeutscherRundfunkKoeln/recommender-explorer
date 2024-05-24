import copy
import logging
from dataclasses import fields
from typing import cast

import pytest

from src import constants
from src.dto.content_item import ContentItemDto
from src.util.dto_utils import content_fields, dto_from_classname, dto_from_model

logger = logging.getLogger(__name__)


@pytest.fixture
def config() -> dict:
    return {
        constants.MODEL_CONFIG_C2C: {
            constants.MODEL_TYPE_C2C: {
                "test-model": {
                    "content_type": "ContentItemDto",
                }
            }
        },
        constants.MODEL_CONFIG_U2C: {
            constants.MODEL_TYPE_U2C: {
                "test-model": {
                    "user_type": "UserItemDto",
                }
            }
        },
    }


def test_init_content_dto_from_classname_succeeds() -> None:
    i = dto_from_classname(
        class_name="ContentItemDto",
        position=constants.ITEM_POSITION_START,
        item_type=constants.ITEM_TYPE_CONTENT,
        provenance=constants.ITEM_PROVENANCE_C2C,
    )
    assert i.viewer == "ContentStartCard@view.cards.content_start_card"


def test_init_history_dto_from_classname_succeeds() -> None:
    i = dto_from_classname(
        class_name="HistoryItemDto",
        position=constants.ITEM_POSITION_START,
        item_type=constants.ITEM_TYPE_CONTENT,
        provenance=constants.ITEM_PROVENANCE_C2C,
    )
    assert i.viewer == "ContentHistoryCard@view.cards.floatpanel_history_card"


def test_init_content_dto_from_model_succeeds(config) -> None:
    first_c2c_model = list(
        config[constants.MODEL_CONFIG_C2C][constants.MODEL_TYPE_C2C].values()
    )[0]
    i = dto_from_model(
        model=first_c2c_model,
        position=constants.ITEM_POSITION_START,
        item_type=constants.ITEM_TYPE_CONTENT,
        provenance=constants.ITEM_PROVENANCE_C2C,
    )
    assert i.viewer == "ContentStartCard@view.cards.content_start_card"
    i.provenance = "mediathek"
    assert i.provenance == "mediathek"


def test_init_user_dto_from_model_succeeds(config) -> None:
    first_u2c_model = list(
        config[constants.MODEL_CONFIG_U2C][constants.MODEL_TYPE_U2C].values()
    )[0]
    u = dto_from_model(
        model=first_u2c_model,
        position=constants.ITEM_POSITION_START,
        item_type=constants.ITEM_TYPE_USER,
        provenance=constants.ITEM_PROVENANCE_U2C,
    )
    assert u.viewer == "UserCard@view.cards.user_card"


def test_init_user_dto_in_bad_position_throws(config) -> None:
    first_u2c_model = list(
        config[constants.MODEL_CONFIG_U2C][constants.MODEL_TYPE_U2C].values()
    )[0]
    with pytest.raises(TypeError):
        dto_from_model(
            model=first_u2c_model,
            position=constants.ITEM_POSITION_RECO,
            item_type=constants.ITEM_TYPE_USER,
            provenance=constants.ITEM_PROVENANCE_U2C,
        )


def test_init_and_copy_content_dto_succeeds() -> None:
    i = cast(
        ContentItemDto,
        dto_from_classname(
            class_name="ContentItemDto",
            position=constants.ITEM_POSITION_START,
            item_type=constants.ITEM_TYPE_CONTENT,
            provenance=constants.ITEM_PROVENANCE_C2C,
        ),
    )
    assert i.viewer == "ContentStartCard@view.cards.content_start_card"
    j = copy.copy(i)
    j.genreCategory = "Ard Retro"
    assert j.genreCategory != i.genreCategory


def test_dto_fields_list_succeeds() -> None:
    i = dto_from_classname(
        class_name="ContentItemDto",
        position=constants.ITEM_POSITION_START,
        item_type=constants.ITEM_TYPE_CONTENT,
        provenance=constants.ITEM_PROVENANCE_C2C,
    )
    all_item_props = {f.name for f in fields(i) if f.init}
    content_only_props = content_fields(i)
    assert content_only_props < all_item_props
