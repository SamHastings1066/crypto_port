import pandas as pd
import streamlit as st
from pypfopt import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from datetime import date, timedelta

@st.cache(persist=True, show_spinner=False)
def uniform(returns_df, num_coins, start_date, end_date):
  # THERE IS AN ERROR
  # Need to change this from num_coins being a number to investment_set being
  # a list of assets available. otherwise there could be assets in your
  # portfolio that are not included in your investment set graph
  '''
  A function to return a uniform distribution of weights across all assets with
  a full returns history (no NaN values) between start_date and end_date.

  Returns:
    weights: a vector of weights of dimension num_coins.
    investment_cols: a vector of column names for coins with full histories.
  '''
  investment_df = returns_df[start_date:end_date]
  investment_df.dropna(axis=1, inplace=True) # drop cols with any NaN values
  investment_cols = investment_df.columns[0:num_coins]
  weights = [1/num_coins for _ in range(num_coins)]
  return weights, investment_cols

@st.cache(persist=True, show_spinner=False)
def markowitz(returns_df):
  pass

@st.cache(persist=True, show_spinner=False, allow_output_mutation=True)
def create_port_rtns(returns_df, weights, investment_cols, start_date, end_date):
  investment_df = returns_df[investment_cols]
  investment_df[start_date:start_date]=0
  rebased_df = (1 + investment_df[start_date:end_date]).cumprod()
  port_returns = rebased_df.dot(weights)
  port_returns.index.name = 'date'
  port_returns.name = 'price (USD)'
  return port_returns

@st.cache(persist=True, show_spinner=False)
def markowitz_weights(histories_df,start_port_date,investment_cols, analysis_days=365):
  start_analysis_date = start_port_date - timedelta(analysis_days)
  analysis_df = histories_df[start_analysis_date:start_port_date][investment_cols]

  # Calculate expected returns and sample covariance
  mu = expected_returns.mean_historical_return(analysis_df)
  S = risk_models.sample_cov(analysis_df)
  # Optimize for maximal Sharpe ratio
  attempts=0
  while attempts < 50:
    try:
      ef = EfficientFrontier(mu, S, weight_bounds=(0, 1))
      ef.max_sharpe()
      break
    except Exception as e:
      attempts += 1
  try:
    cleaned_weights = ef.clean_weights()
  except Exception as e:
    print("Could not find optimal solution, try changing optimisation constraints or investment set")
  return cleaned_weights

@st.cache(persist=True, show_spinner=False)
def create_weights_df(weights_dict, strategy):
  return pd.DataFrame({
    'strategy': strategy,
    'assets': list(weights_dict.keys()),
    'weights': list(weights_dict.values())
  })

@st.cache(persist=True, show_spinner=False)
def ids_with_histories(histories_df, start_date, end_date):
  investment_df = histories_df[start_date:end_date]
  investment_df.dropna(axis=1, inplace=True) # drop cols with any NaN values
  return investment_df.columns

@st.cache(persist=True, show_spinner=False)
def uniform_weights_dict(ids_with_histories):
  weight = 1/len(ids_with_histories)
  uniform_weights_dict = {}
  for id in ids_with_histories:
    uniform_weights_dict[id] = weight
  return uniform_weights_dict

@st.cache(persist=True, show_spinner=False)
def markowitz_weights_dict(histories_df,start_port_date,ids_with_histories, analysis_days=365):
  start_analysis_date = start_port_date - timedelta(analysis_days)
  analysis_df = histories_df[start_analysis_date:start_port_date][ids_with_histories]

  # Calculate expected returns and sample covariance
  mu = expected_returns.mean_historical_return(analysis_df)
  S = risk_models.sample_cov(analysis_df)
  # Optimize for maximal Sharpe ratio
  attempts=0
  while attempts < 10:
    try:
      ef = EfficientFrontier(mu, S, weight_bounds=(0, 1))
      ef.max_sharpe()
      break
    except Exception as e:
      attempts += 1
  try:
    cleaned_weights = ef.clean_weights()
  except Exception as e:
    print("Could not find optimal solution, try changing optimisation constraints or investment set")
  return {k: v for k, v in sorted(cleaned_weights.items(), key=lambda item: item[1], reverse=True)}
  #return cleaned_weights

@st.cache(persist=True, show_spinner=False)
def gen_port_rtns(rebased_df, weights_dict):
  new_weights_dict = {k: v for k, v in weights_dict.items() if k in rebased_df.columns}
  new_weights_dict = {k: v/sum(new_weights_dict.values()) for k, v in new_weights_dict.items()}
  return rebased_df[list(new_weights_dict.keys())].dot(list(new_weights_dict.values()))
  #return rebased_df[list(weights_dict.keys())].dot(list(weights_dict.values()))

@st.cache(persist=True, show_spinner=False)
def gen_all_returns(rebased_df, ids_with_histories, strategy_dict):
  '''
  A function to generate returns for all portfolios and all coins with full
  histories over the backtest period, rebased to the start of the backtest
  period.
  '''
  port_returns = gen_port_rtns(rebased_df, strategy_dict['Uniform'])
  port_returns = pd.DataFrame({'Uniform': port_returns})
  temp_dict = {k: v for k, v in strategy_dict.items() if k != 'Uniform'}
  if len(temp_dict)!=0:
    for name, weights in temp_dict.items():
      temp_returns = gen_port_rtns(rebased_df, weights)
      temp_returns.name = name
      port_returns = port_returns.join(temp_returns)
  return port_returns.join(rebased_df[ids_with_histories])

  #uniform_returns = gen_port_rtns(rebased_df, uniform_weights_dict)
  #uniform_returns.name = "Uniform"
  #markowitz_returns = gen_port_rtns(rebased_df, markowitz_weights_dict)
  #markowitz_returns.name = "Markowitz"
  #port_returns = uniform_returns.to_frame().join(markowitz_returns)
  #return port_returns.join(rebased_df[ids_with_histories])

