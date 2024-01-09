from abc import ABC, abstractmethod
from dto.item import ItemDto
import panel as pn

#
# Tobias - base viewer not currently in use - use it!
#
class BaseViewer(ABC):

    @abstractmethod
    def draw(self, dto: ItemDto, card: pn.Card):
        pass