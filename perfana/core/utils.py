import pandas as pd

from perfana.types import TimeSeriesData

__all__ = ['freq_to_scale', 'infer_frequency']


def freq_to_scale(freq: str):
    """Converts frequency to scale"""
    freq = str(freq).lower()
    if freq in ('d', 'day', 'daily'):
        return 252
    elif freq in ('w', 'week', 'weekly'):
        return 52
    elif freq in ('m', 'month', 'monthly'):
        return 12
    elif freq in ('s', 'semi-annual', 'semi-annually'):
        return 6
    elif freq in ('q', 'quarter', 'quarterly'):
        return 4
    elif freq in ('y', 'year', 'yearly', 'annual'):
        return 1
    else:
        raise ValueError(f"Unknown frequency: {freq}")


def infer_frequency(data: TimeSeriesData, fail_policy='raise'):
    """
    Infers the frequency (periodicity) of the time series

    :param data: DataFrame, Series.
        time series pandas data object
    :param fail_policy: str, default 'raise'.
        Action to do when frequency cannot be inferred. If set to 'raise', a TypeError will be raised. If set to
        'ignore', a NoneType will be returned on failure.
    :returns:
        Frequency of data. If <fail_policy> is ignore, returns None.
    """
    if not isinstance(data, (pd.DataFrame, pd.Series)):
        raise ValueError('<data> must be a pandas DataFrame or Series')

    fail_policy = fail_policy.lower()
    if fail_policy not in ('ignore', 'raise'):
        raise ValueError(f"Unknown <fail_policy>: {fail_policy}. Use one of [ignore, raise]")

    # custom inference
    n = len(data)
    time_delta = (data.index[1:] - data.index[:-1]).value_counts()

    delta = {
        'daily': sum(time_delta.get(f'{day} days', 0) for day in range(1, 6)),  # 1 to 5 days - daily data
        'weekly': time_delta.get('7 days', 0),
        'monthly': sum(time_delta.get(f'{day} days', 0) for day in (28, 29, 30, 31)),
        'quarterly': sum(time_delta.get(f'{day} days', 0) for day in range(89, 93)),
        'semi-annually': sum(time_delta.get(f'{day} days', 0) for day in range(180, 185)),  # 180-184 days - semi-annual
        'yearly': sum(time_delta.get(f'{day} days', 0) for day in range(360, 367))  # 360-366 - considered annual
    }

    if n < 30:  # less than 30 observations, just take key with max value
        return max(delta, key=lambda k: delta[k])

    for freq, count in delta.items():
        if count > 0.85 * n:
            # if over 85% of the data belongs to frequency category, select frequency
            return freq

    if fail_policy == 'raise':
        raise TypeError('could not infer periodicity of time series index')
    else:
        return None