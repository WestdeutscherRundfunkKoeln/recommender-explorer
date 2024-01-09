from abc import ABC, abstractmethod

class NnSeeker(ABC):

    @property
    def ITEM_IDENTIFIER_PROP(cls):
        pass

    @abstractmethod
    def get_k_NN( self, item, k, nn_filter ):
        pass

    @abstractmethod
    def get_max_num_neighbours( self, content_idx ):
        pass

    @abstractmethod
    def set_endpoint( self, endpoint ):
        pass