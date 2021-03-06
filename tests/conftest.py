from os import path

import pandas as pd
import pytest

from perfana.conversions import to_time_series
from perfana.datasets import load_etf

TEST_DATA_DIR = path.join(path.dirname(__file__), 'data')


@pytest.fixture
def etf_raw():
    return load_etf(False).dropna()


@pytest.fixture
def etf(etf_raw: pd.DataFrame):
    return to_time_series(etf_raw)


@pytest.fixture
def expected_returns():
    return pd.read_csv(path.join(TEST_DATA_DIR, 'simple_returns.csv'), index_col=0, parse_dates=[0])


@pytest.fixture
def expected_log_returns():
    return pd.read_csv(path.join(TEST_DATA_DIR, 'log_returns.csv'), index_col=0, parse_dates=[0])


@pytest.fixture
def expected_rel_returns():
    return pd.read_csv(path.join(TEST_DATA_DIR, 'relative_returns.csv'), index_col=0, parse_dates=[0])
