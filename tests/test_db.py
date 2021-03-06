import logging

from src.db import extract_db_config
from tests.helpers.helpers import dict_assert


def test_get_config(snapshot):
    logger = logging.getLogger()
    actual = extract_db_config(logger, './tests/fixtures/extract_db_config.php')
    
    dict_assert(snapshot, actual.to_dict(), "test_basic.json")
    
    actual = extract_db_config(logger, './tests/fixtures/extract_db_config_mysql_fn.php')
    
    dict_assert(snapshot, actual.to_dict(), "test_mysql_fn.json")
