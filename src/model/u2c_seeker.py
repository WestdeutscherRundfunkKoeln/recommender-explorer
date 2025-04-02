from typing import Any
from abc import ABC, abstractmethod
from dto.user_item import UserItemDto

class U2CSeeker(ABC):

    @abstractmethod
    def get_recos_user( self, user: UserItemDto, num_recos: int, nn_filter: dict[str, Any] = False
    ) -> tuple[list, list, str]:
        pass

    @abstractmethod
    def get_model_params(self):
        pass

    @abstractmethod
    def set_model_config( self, model_config ):
        pass
