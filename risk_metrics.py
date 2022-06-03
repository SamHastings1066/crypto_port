import numpy as np
import pandas as pd
import streamlit as st


@st.cache(persist=True, show_spinner=False)
def absolute_return(prices):
    "a function to calculate the absolute return given a daily price series"
    abs_rtn = (prices.iloc[-1] / prices[0]) - 1
    return abs_rtn


@st.cache(persist=True, show_spinner=False)
def annual_return(prices):
    "a function to calculate the annualised return given a daily price series"
    abs_rtn = absolute_return(prices)
    annual_rnt = (pow((abs_rtn / 100) + 1, 365 / len(prices)) - 1) * 100
    return annual_rnt


@st.cache(persist=True, show_spinner=False)
def max_drawdown(prices):
    """
    A function to calculate the max drawdown for a given price series "prices"
    as well as the index of the start of the max drawdown period, "start_idx"
    and the index of end of the max drawdwon period, "end index"
    """
    if type(prices) == type(pd.Series(dtype="object")):
        prices = prices.values
    end_idx = np.argmax(np.maximum.accumulate(prices) - prices)  # end of the period
    start_idx = np.argmax(prices[:end_idx])  # start of period
    max_dd = (prices[start_idx] - prices[end_idx]) / prices[start_idx]
    return max_dd, start_idx, end_idx


@st.cache(persist=True, show_spinner=False)
def annual_vol(prices):
    """
    A function to calculate the annuaised volatility of a price series assuming
    cryptos trade 365 days a year
    """
    return prices.pct_change().std() * (365**0.5)
