import os

import numpy as np
import pandas as pd

__all__ = ["load_cube", "load_etf", "load_hist", "load_smi"]


def _load_file(fn: str):
    return os.path.join(os.path.dirname(__file__), 'data', fn)


def load_cube() -> np.ndarray:
    """
    Loads a sample Monte Carlo simulation of 9 asset classes.

    The dimension of the cube is 80 * 1000 * 9. The first axis represents the time, the second
    represents the number of trials (simulations) and the third represents each asset class.

    Returns
    -------
    ndarray
        A data cube of simulated returns
    """
    return np.load(_load_file('cube.npy'))


def load_etf(date_as_index: bool = True) -> pd.DataFrame:
    """
    Dataset contains prices of 4 ETF ranging from 2001-06-15 to 2019-03-01.

    Parameters
    ----------
    date_as_index:
        If True, sets the first column as the index of the DataFrame

    Returns
    -------
    DataFrame
        A data frame containing the prices of 4 ETF
    """
    fp = _load_file('etf.csv')

    if date_as_index:
        df = pd.read_csv(fp, index_col=0, parse_dates=[0])
        df.index.name = df.index.name.strip()
    else:
        df = pd.read_csv(fp, parse_dates=[0])

    df.columns = df.columns.str.strip()
    for c in 'VBK', 'BND':
        df[c] = pd.to_numeric(df[c].str.strip())

    return df


def load_hist(date_as_index: bool = True) -> pd.DataFrame:
    """
    Dataset containing 20-years returns data from different asset classes spanning from 1988 to 2019.

    Parameters
    ----------
    date_as_index:
        If True, sets the first column as the index of the DataFrame

    Returns
    -------
    DataFrame
        A data frame containing the prices of 4 ETF
    """
    fp = _load_file('hist.csv')

    if date_as_index:
        df = pd.read_csv(fp, index_col=0, parse_dates=[0])
        df.index.name = df.index.name.strip()
    else:
        df = pd.read_csv(fp, parse_dates=[0])

    df.columns = df.columns.str.strip()
    return df


def load_smi(as_returns=False) -> pd.DataFrame:
    """
    Dataset contains the close prices of all 20 constituents of the Swiss Market Index (SMI) from
    2011-09-09 to 2012-03-28.

    Parameters
    ----------
    as_returns: bool
        If true, transforms the price data to returns data

    Returns
    -------
    DataFrame
        A data frame of the closing prices of all 20 constituents of the Swiss Market Index
    """

    df = pd.read_csv(_load_file('smi.csv'), index_col=0, parse_dates=[0])
    if as_returns:
        df = df.pct_change().dropna()
    return df
