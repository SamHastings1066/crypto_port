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
  #melt_df.columns=['Strategy','price (USD)']
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
  performance_df['Type'] = ["Portfolio" if x in ['Uniform','Markowitz'] else "Coin" for x in assets]
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
#if "start_date" in st.session_state:
#  start_date = st.session_state.start_date
#else:
#  start_date = date.today() - timedelta(365)
#if "end_date" in st.session_state:
#  end_date = st.session_state.end_date
#else:
#  end_date = date.today()

#cols = st.columns(2)
#start_date = cols[0].date_input("select start date", value= date.today()
#- timedelta(365), min_value=date.today() - timedelta(365 * 5), max_value=end_date)
#end_date = cols[1].date_input("select end date", value= date.today(),
#min_value=start_date, max_value=date.today())
#st.write(start_date)
