import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image
import glob
from risk_metrics import absolute_return, annual_vol, max_drawdown

@st.cache(persist=True, show_spinner=False)
def create_rebase_chart(rebased_df, num_coins):
  melt_df = pd.melt(rebased_df.iloc[:,:num_coins], ignore_index=False)
  melt_df.columns=['coin','price (USD)']
  return melt_df

@st.cache(persist=True, show_spinner=False)
def create_chart_df(all_returns_df, portfolio, coin):
  melt_df = pd.melt(all_returns_df, value_vars=[portfolio, coin], ignore_index=False)
  melt_df.columns=['Asset','Value (USD)']
  return melt_df

@st.cache(persist=True, show_spinner=False)
def create_comparison_df(all_returns_df, selected_assets):
  melt_df = pd.melt(all_returns_df, value_vars=selected_assets, ignore_index=False)
  melt_df.columns=['Asset','Value (USD)']
  return melt_df

@st.cache(persist=True, show_spinner=False)
def ordered_dict(dictionary):
  return {k: v for k, v in sorted(dictionary.items(), key=lambda item: item[1], reverse=True)}

# allow output mutation in this function because I'm not worried about mutation
# and i want to reduce the time it takes streamlit to check it hasn't mutated.
@st.cache(persist=True, show_spinner=False, allow_output_mutation=True)
def load_images():
  image_dict = {}
  for filename in glob.glob('logos/*.jpg'): #assuming all logos are png format
    im=Image.open(filename)
    image_dict[filename[6:][:-4]]=im
  return image_dict

@st.cache(persist=True, show_spinner=False)
def gen_performance_df(all_returns_df, market_cap_dict):
  assets = all_returns_df.columns
  performance_df = pd.DataFrame(index = assets)
  performance_df['Type'] = ["Portfolio" if x in ['Uniform', 'Markowitz'] else "Coin" for x in assets]
  abs_return = all_returns_df.apply(absolute_return)
  ann_vol = all_returns_df.apply(annual_vol)
  drawdown_triples = all_returns_df.apply(max_drawdown)
  sharpe = abs_return.divide(ann_vol)
  market_caps=[]
  for asset in assets:
      try:
          market_caps.append(int(market_cap_dict[asset]))
      except:
          market_caps.append(0)
  performance_df['Risk adjusted return %'] =  sharpe *100
  performance_df['Return over period %'] = abs_return * 100
  performance_df['Annual volatility'] = ann_vol *100
  performance_df['Max loss %'] = drawdown_triples.iloc[0] *100
  performance_df['Market cap $M'] = [cap/1000000 for cap in market_caps]
  return performance_df

@st.cache(persist=True, show_spinner=False)
def gen_performance_ag_df(all_returns_df, market_cap_dict, strategy_dict):
  assets = all_returns_df.columns
  performance_df = pd.DataFrame(index=assets)
  performance_df['Asset'] = assets
  performance_df['Type'] = ["Portfolio" if x in list(strategy_dict.keys()) else "Coin" for x in assets]
  abs_return = all_returns_df.apply(absolute_return)
  ann_vol = all_returns_df.apply(annual_vol)
  drawdown_triples = all_returns_df.apply(max_drawdown)
  sharpe = abs_return.divide(ann_vol)
  market_caps=[]
  for asset in assets:
      try:
          market_caps.append(int(market_cap_dict[asset]))
      except:
          market_caps.append(0)
  performance_df['Risk adjusted return %'] =  sharpe *100
  performance_df['Return over period %'] = abs_return * 100
  performance_df['Annual volatility'] = ann_vol *100
  performance_df['Max loss %'] = drawdown_triples.iloc[0] *100
  performance_df['Market cap $M'] = [cap/1000000 for cap in market_caps]
  return performance_df

@st.cache(persist=True, show_spinner=False)
def add_drawdown(fig, all_returns_df, selected_asset):
  #calculate max drawdown
  max_dd, start_idx, end_idx = max_drawdown(all_returns_df[selected_asset])
  start_dd = all_returns_df.index[start_idx]
  end_dd = all_returns_df.index[end_idx]
  fig.add_vline(x=start_dd, line_width=1, line_color="red")
  fig.add_vline(x=end_dd, line_width=1, line_color="red")
  fig.add_vrect(x0=start_dd, x1=end_dd, line_width=0, fillcolor="red", opacity=0.05, annotation_text=selected_asset + " maxdd")
  return fig, max_dd, start_dd, end_dd

def write_coins(non_zero_coins, weights_dict, ids2names_dict, n_cols=2):
  n_coins = len(non_zero_coins)
  n_rows = 1 + n_coins // int(n_cols)

  rows = [st.container() for _ in range(n_rows)]
  cols_per_row = [r.columns(n_cols) for r in rows]
  cols = [column for row in cols_per_row for column in row]

  #cols = st.columns(n_coins)
  #checkboxes=[]
  for i, coin_id in enumerate(non_zero_coins):
    cols[i].slider(ids2names_dict[coin_id], min_value=0, max_value=100,
      value=int(weights_dict[coin_id]*100), key=coin_id,
      disabled=True)

def write_bespoke_coins(coin_names, n_cols=2):
  n_coins = len(coin_names)
  n_rows = 1 + n_coins // int(n_cols)

  rows = [st.container() for _ in range(n_rows)]
  cols_per_row = [r.columns(n_cols) for r in rows]
  cols = [column for row in cols_per_row for column in row]

  #cols = st.columns(n_coins)
  #checkboxes=[]
  weights_list = []
  for i, coin_name in enumerate(coin_names):
    weight = cols[i].slider(coin_name, min_value=0, max_value=100,
      value=50, key=coin_name,
      disabled=False)
    weights_list.append(weight)
  weights_list = [weight/sum(weights_list) for weight in weights_list]
  return weights_list


@st.cache(persist=True, show_spinner=False)
def get_pre_selected_idx(assets, pre_selected):
  return [i for i in range(len(assets)) if assets[i] in pre_selected]
