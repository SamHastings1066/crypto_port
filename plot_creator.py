import pandas as pd
import plotly.express as px
import streamlit as st

@st.cache(persist=True, show_spinner=False)
def create_rebase_chart(rebased_df, num_coins):
  melt_df = pd.melt(rebased_df.iloc[:,:num_coins], ignore_index=False)
  melt_df.columns=['coin','price (USD)']
  return melt_df



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
