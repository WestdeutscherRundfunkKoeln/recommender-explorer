import logging
from .dataloader import FileDataLoader
from .nn_seeker import NnSeeker


logger = logging.getLogger(__name__)

class NnSeekerFileBased(NnSeeker):
    
    def __init__(self, config):
        dataloader = FileDataLoader(config)
        self.labels,self.nn,self.dists = dataloader.load_nn_matrix()

    def get_k_NN( self, content_id, k ):
        content_idx = self.__getIndexForContentId(content_id)
        kidxs, nn_dists = self.__get_k_NN_by_idx(content_idx, k)
        recomm_content_ids = [self.__getUrnForInd(ind) for ind in kidxs]
        
        return recomm_content_ids, nn_dists
    
    def get_max_num_neighbours(self, content_idx ):
        return self.nn[content_idx].shape[0]
        
    def __get_k_NN_by_idx( self, ref_id, k ):
        nn_dists = self.dists[ref_id]
        neighb_idxs = self.nn[ref_id]
        nnk_idxs = neighb_idxs[0:k]
        return nnk_idxs, self.dists[ref_id][0:k]

    def __getUrnForInd(self, ind):
        return self.labels[ind]

    def __getIndexForContentId(self, content_id):
        return self.labels.index(content_id)

