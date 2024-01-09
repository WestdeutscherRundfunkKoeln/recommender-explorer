import logging

#import s3fs
from s3fs.core import S3FileSystem
import json
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class FileDataLoader(object):
    
    def __init__(self, config):
        ### S3 config
        self.use_s3_download = config['filebackend.use_s3_download']
        self.s3_bucket = config['filebackend.s3_bucket']
        self.s3_base_data_filename = config['filebackend.s3_base_file']
        self.s3_neighbours_data_filename = config['filebackend.s3_nn_file']

        self.base_data_filename = config['filebackend.local_base_file']
        self.neighbours_data_filename = config['filebackend.local_nn_file']

    def load_base_data( self ):
        # load base data
        base_data = None
        if self.use_s3_download:
            logger.info(f'Loading base data from s3 bucket {self.s3_bucket} key {self.s3_base_data_filename}')
            s3fs = S3FileSystem()
            res = "s3://{}/{}".format(self.s3_bucket, self.s3_base_data_filename)
            
            with s3fs.open(res, mode='rb', fill_cachebool=True) as s3_file:
                base_data  = json.load(s3_file)
        else:
            logger.info(f'Loading base data from local file {self.base_data_filename}')
            with open(self.base_data_filename) as json_file:
                base_data  = json.load(json_file)

        base_data_df = self.__enrich_base_df(base_data)
        return base_data_df

    def __enrich_base_df(self, base_data):
        base_data_df = pd.DataFrame.from_dict(base_data['embeddings'], orient='index')
        base_data_df['created'] = pd.to_datetime(base_data_df['created'])
        base_data_df['createdFormatted'] = base_data_df['created'].dt.strftime('%d-%B-%Y %X')
        # Or
        # base_data_df['createdFormatted'] = base_data_df['created'].dt.strftime('%d-%m-%Y %X')
        return base_data_df


    def load_nn_matrix( self ):
        # load nn matrix
        if self.use_s3_download:
            s3fs = S3FileSystem()
            res = "s3://{}/{}".format(self.s3_bucket, self.s3_neighbours_data_filename)
            with s3fs.open(res, mode='rb', fill_cachebool=True) as s3_file:
                labels, nn, dists = np.load(s3_file, allow_pickle=True).values()
                labels = labels.tolist()

        else:
            data = np.load(self.neighbours_data_filename, mmap_mode="r")
            nn = data['nn']
            dists =  data['dists']
            labels = data['labels'].tolist()

        return labels,nn,dists
