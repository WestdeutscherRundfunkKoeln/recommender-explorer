import constants
from dataclasses import dataclass
from dto.item import ItemDto
from dto.content_item import ContentItemDto

@dataclass
class UserItemDto(ItemDto):
    id: str = ''
    source: str = ''
    source_value: str = ''
    avatar: str = 'assets/img/user-dummy-pic.png'
    last_active: str = ''
    history: list[ContentItemDto] = ()
    last_genres: list = ()
    _viewer: str = ''

    @property
    def viewer(self) -> str:
        if self._position == constants.ITEM_POSITION_START:
            self._viewer = 'UserCard@view.cards.user_card'
        return self._viewer

    def __post_init__(self):
        if self._position is not constants.ITEM_POSITION_START:
            raise TypeError('Unsupported UserItem position [' + self._position + ']')
