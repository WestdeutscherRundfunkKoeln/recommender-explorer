import logging
from test.test_util import mock_start_and_reco_items_with_duplicates

from src.util.postprocessing import FilterPostproc

logger = logging.getLogger(__name__)


def test_filter_duplicates() -> None:
    parameters = ["crid"]
    start_item, reco_items = mock_start_and_reco_items_with_duplicates()
    filter_postproc = FilterPostproc()
    nn_items = filter_postproc.filterDuplicates(start_item, reco_items, parameters)
    assert len(nn_items) < len(reco_items)
