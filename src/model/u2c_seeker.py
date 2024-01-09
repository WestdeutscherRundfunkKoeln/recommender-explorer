from abc import ABC, abstractmethod

class U2CSeeker(ABC):

    @abstractmethod
    def get_recos_user( self, user, num_recos ):
        pass

    @abstractmethod
    def set_endpoint( self, endpoint ):
        pass

    @abstractmethod
    def get_model_params(self):
        pass