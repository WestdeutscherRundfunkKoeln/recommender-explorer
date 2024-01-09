import logging
import pandas as pd

from ..base_data_accessor import BaseDataAccessor
from .dataloader import FileDataLoader
from . import data_access

log = logging.getLogger(__name__)

class BaseDataAccessorFileBased(BaseDataAccessor):    

    def __init__( self, config ):
        dataloader = FileDataLoader(config)
        self.base_data_df = dataloader.load_base_data()
        self.base_data_df['created'] = pd.to_datetime(self.base_data_df['created'])


    def get_items_by_ids( self, ids ):
        return self.base_data_df.loc[ids]

    def get_item_by_crid( self, crid ):
         return self.base_data_df.loc[self.base_data_df['crid'].eq(crid)]

    def get_items_by_date( self, start_date, end_date):
        return self.base_data_df.loc[(start_date <= self.base_data_df['created'].dt.date) & (end_date >= self.base_data_df['created'].dt.date)]


    def get_items_date_range_limits( self ):
        newest_item_in_base = self.base_data_df.created.max()
        newest_item_in_base_ts = newest_item_in_base.timestamp()
        oldest_item_in_base = self.base_data_df.created.min()
        oldest_item_in_base_ts = oldest_item_in_base.timestamp()
        return newest_item_in_base_ts, oldest_item_in_base_ts


    def get_top_k_vals_for_column( self, column, k):
        if column not in self.base_data_df.columns:
            return None

        col_lists = self.base_data_df[column].values[:]
        top_col_vals = data_access.getTopN(50, col_lists)

        return top_col_vals

    def get_unique_vals_for_column( self, column, sort=True):
        if column not in self.base_data_df.columns:
            log.warn(f'column with name {column} is not contained in dataframe.')
            return None

        uniq_vals = self.base_data_df[column].unique()
        if sort:
            uniq_vals = sorted(uniq_vals) 

        return uniq_vals