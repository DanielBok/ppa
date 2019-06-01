from typing import Optional, Union

import pandas as pd

from perfana.conversions import to_time_series
from perfana.core.utils import freq_to_scale
from perfana.exceptions import TimeIndexError, TimeIndexMismatchError
from perfana.types import TimeSeriesData

__all__ = ['active_premium', 'annualized_returns', 'excess_returns', 'relative_returns']


def active_premium(ra: TimeSeriesData, rb: TimeSeriesData, freq: Optional[str] = None, geometric=True,
                   prefixes=('AST', 'BMK')):
    """
    The return on an investment's annualized return minus the benchmark's annualized return.

    :param ra: iterable data
        The assets returns vector or matrix
    :param rb: iterable data
        The benchmark returns
    :param freq: str, optional
        frequency of the data. Use one of [daily, weekly, monthly, quarterly, semi-annually, yearly]
    :param geometric: boolean, default True
        If True, calculates the geometric returns. Otherwise, calculates the arithmetic returns
    :param prefixes: Tuple[str, str], default ('AST', 'BMK')
        Prefix to apply to overlapping column names in the left and right side, respectively. This is also applied
        when the column name is an integer (i.e. 0 -> AST_0). It is the default name of the Series data if there
        are no name to the Series

    :return: DataFrame.
        Active premium of each strategy against benchmark
    """
    ra = to_time_series(ra)
    rb = to_time_series(rb)

    if isinstance(ra, pd.Series):
        ra = pd.DataFrame(ra.rename(ra.name or prefixes[0]))

    if isinstance(rb, pd.Series):
        rb = pd.DataFrame(rb.rename(rb.name or prefixes[1]))

    freq = _determine_frequency(ra, rb, freq)

    res = pd.DataFrame()
    for ca, a in ra.iteritems():
        premium = {}
        if isinstance(ca, int):
            ca = f'{prefixes[0]}_{ca}'

        for cb, b in rb.iteritems():
            if isinstance(cb, int):
                cb = f'{prefixes[1]}_{cb}'

            premium[cb] = annualized_returns(a, freq, geometric) - annualized_returns(b, freq, geometric)
        res[ca] = pd.Series(premium)

    return res


def annualized_returns(r: TimeSeriesData, freq: Optional[str] = None, geometric=True) -> Union[float, pd.Series]:
    """
    Calculates the annualized returns from the data

    The formula for annualized geometric returns is formulated by raising the compound return to the number of
    periods in a year, and taking the root to the number of total observations:

        prod(1 + R)^(scale/n) - 1

    where scale is the number of observations in a year, and n is the total number of observations.

    For simple returns (geometric=FALSE), the formula is:

        mean(R)*scale

    :param r: iterable data
        numeric returns series or data frame
    :param freq: str, optional
        frequency of the data. Use one of [daily, weekly, monthly, quarterly, semi-annually, yearly]
    :param geometric: boolean, default True
        If True, calculates the geometric returns. Otherwise, calculates the arithmetic returns

    :return: float, pd.Series
        annualized returns
    """
    r = to_time_series(r).dropna()
    if freq is None:
        freq = r.ppa.frequency

    scale = freq_to_scale(freq)

    if geometric:
        return (r + 1).prod() ** (scale / len(r)) - 1
    else:  # arithmetic mean
        return r.mean() * scale


def excess_returns(ra: TimeSeriesData, rb: TimeSeriesData, freq: Optional[str] = None, geometric=True):
    """
    An average annualized excess return is convenient for comparing excess returns

    Excess returns is calculated by first annualizing the asset returns and benchmark returns stream. See the docs for
    `annualized_returns()` for more details. The geometric returns formula is:

        r_g = (ra - rb) / (1 + rb)

    The arithmetic excess returns formula is:

        r_g = ra - rb

    Returns calculation will be truncated by the one with the shorter length. Also, annualized returns are calculated
    by the geometric annualized returns in both cases

    :param ra: iterable data
        The assets returns vector or matrix
    :param rb: iterable data
        The benchmark returns. If this is a vector and the asset returns is a matrix, then all assets returns (columns)
        will be compared against this single benchmark. Otherwise, if this is a matrix, then assets will be compared
        to each individual benchmark (i.e. column for column)
    :param freq: str, optional
        frequency of the data. Use one of [daily, weekly, monthly, quarterly, semi-annually, yearly]
    :param geometric: boolean, default True
        If True, calculates the geometric excess returns. Otherwise, calculates the arithmetic excess returns
    :return:
    """
    ra = to_time_series(ra).dropna()
    rb = to_time_series(rb).dropna()

    n = min(len(ra), len(rb))
    ra, rb = ra.iloc[:n], rb.iloc[:n]

    if ra.ndim == rb.ndim and ra.shape != rb.shape:
        raise ValueError('The shapes of the asset and benchmark returns do not match!')

    freq = _determine_frequency(ra, rb, freq)

    ra = annualized_returns(ra, freq)
    rb = annualized_returns(rb, freq)

    return (ra - rb) / (1 + rb) if geometric else ra - rb


def relative_returns(ra: TimeSeriesData, rb: TimeSeriesData, prefixes=('AST', 'BMK')):
    """
    Calculates the ratio of the cumulative performance for two assets through time

    :param ra: iterable data
        The assets returns vector or matrix
    :param rb: iterable data
        The benchmark returns
    :param prefixes: Tuple[str, str], default ('AST', 'BMK')
        Prefix to apply to overlapping column names in the left and right side, respectively. This is also applied
        when the column name is an integer (i.e. 0 -> AST_0). It is the default name of the Series data if there
        are no name to the Series
    :return: Series, DataFrame.
        Returns a DataFrame of the cumulative returns ratio between 2 asset classes.
        Returns a Series if there is only 2 compared classes.
    """
    ra = to_time_series(ra)
    rb = to_time_series(rb)

    if isinstance(ra, pd.Series):
        ra = pd.DataFrame(ra.rename(ra.name or prefixes[0]))

    if isinstance(rb, pd.Series):
        rb = pd.DataFrame(rb.rename(rb.name or prefixes[1]))

    res = pd.DataFrame()
    for ca, a in ra.iteritems():
        for cb, b in rb.iteritems():
            df = (pd.merge(a, b, 'outer', left_index=True, right_index=True).dropna() + 1).cumprod()
            rel = df.iloc[:, 0] / df.iloc[:, 1]

            if isinstance(ca, int):
                ca = f'{prefixes[0]}_{ca}'
            if isinstance(cb, int):
                cb = f'{prefixes[1]}_{cb}'

            res = pd.merge(res, rel.rename(f'{ca}/{cb}'), 'outer', left_index=True, right_index=True)

    if res.shape[1] == 1:
        return res.iloc[:, 0]
    return res


def _determine_frequency(ra, rb, freq):
    if freq is None:
        fa, fb = ra.ppa.frequency, rb.ppa.frequency
        if fa is None and fb is None:
            raise TimeIndexError
        elif fa is None:
            freq = fb
        elif fb is None:
            freq = fa
        elif fa != fb:
            raise TimeIndexMismatchError(fa, fb)
        else:
            freq = fa

    return freq