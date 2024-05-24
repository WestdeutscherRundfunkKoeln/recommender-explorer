from abc import ABC, abstractmethod

import panel as pn
from dto.item import ItemDto


#
# TODO - base viewer not currently in use - use it!
#
class BaseViewer(ABC):
    @abstractmethod
    def draw(self, dto: ItemDto, card: pn.Card):
        pass
