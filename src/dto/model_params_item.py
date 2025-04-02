import constants
from dataclasses import dataclass
from dto.item import ItemDto

@dataclass
class ModelParametersDto(ItemDto):

    @property
    def viewer(self) -> str:
        self._viewer = 'ModelParametersCard@view.cards.floatpanel_model_params_card'
        return self._viewer