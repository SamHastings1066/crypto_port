import streamlit as st
import json
import plotly.express as px
import pandas as pd
from datetime import date, timedelta, datetime
from risk_metrics import annual_return, absolute_return, annual_vol, max_drawdown
import numpy as np
from data_creator import (
    create_assets,
    gen_symbols,
    create_histories_df,
    create_unix_dates,
    create_returns_df,
    create_rebased_df,
    date_range,
)
from plot_creator import create_rebase_chart
from port_creator import uniform, create_port_rtns, markowitz_weights, create_weights_df
from risk_metrics import max_drawdown


# load start and end dates for investment analysis
lookback_years = 5
start_date = date.today() - timedelta(365)
end_date = date.today()


with st.sidebar:
    investment_set = st.number_input(
        "How many coins to would you like in your investment set?",
        min_value=1,
        max_value=50,
        value=10,
        help="Coins will be added to your investment set in order of largest market cap"
        # ("Top 5 coins", "Top 10 coins")
    )
    portfolio_type = st.selectbox(
        "Select portfolio strategy",
        ("Uniform", "Markowitz"),
        help="""
    Uniform: An equal propotion of your initial investment is allocated to each
    asset in the investment set (provided the asset existed at the start date of
     your investment period). \n
    Markowitz: Your initial investment is allocated to each asset in the
    investment set to achieve the "market portfolio"  using a risk-variance
    analysis (provided the asset existed at the start date of your investment
    period).
    """,
    )


# Pull down histories from coincap, and create dataframes for historic prices,
# returns and rebased cumulative price; histories_df, returns_df, and
# rebased_df, respectively.
# All fo the functions in the block below have been decorated with st.cache()
# and so will only be re-run if their arguments, or their underlying code, are
# changed
assets_json = create_assets(total_coins=100)
symbols, names, coin_ids = gen_symbols(assets_json)
start_unix, end_unix = create_unix_dates(
    today=date.today(), lookback_years=lookback_years
)
histories_df = create_histories_df(coin_ids, start_unix, end_unix)
returns_df = create_returns_df(histories_df)
rebased_df = create_rebased_df(returns_df, start_date=start_date, end_date=end_date)

if "rebased_df" not in st.session_state:
    st.session_state.rebased_df = rebased_df

# def adjust_rebased(returns_df, start_date, end_date):
def adjust_rebased():
    st.session_state.rebased_df = create_rebased_df(
        returns_df,
        start_date=st.session_state.myslider[0],
        end_date=st.session_state.myslider[1],
    )


# Draw rebased graph
melt_df = create_rebase_chart(st.session_state.rebased_df, num_coins=investment_set)
fig = px.line(melt_df, x=melt_df.index, y="price (USD)", color="coin")

with st.expander("Quick explantion", expanded=True):
    st.subheader("What's this all about then, eh?")
    st.write(
        """
  The app allows you to construct portfolios of crypto currencies and to
  backtest their historic performance.

  You can select how many coins you would like in your investment set using the
  dropdown box in the sidebar.

  You can select from two different portfolio constructions
  strategies using the dropdown box in the sidebar:

  - Uniform - An equal propotion of your initial investment is allocated to each coin.
  - Markowitz - Your initial investment is allocated to each coin to achieve the portfolio with the highest sharpe ratio in the 365 day period prior to the investment start date.

  You can adjust the date range for the portfolio backtest using the slider widget below.

  If you would like to see the performance of the individual coins in your investment set
  over the backtest period click the + icon in the Coin view expander.

  To collapse this expander click the - icon at the top right.

  """
    )

# Add select slider to allow
date_list = date_range(end_date, lookback_years - 1)
start_port_date, end_port_date = st.select_slider(
    "Select date range for portolio backtest",
    key="myslider",
    options=date_list,
    value=(date.today() - timedelta(365), date.today()),
    on_change=adjust_rebased,
)

with st.expander("Coin view", expanded=False):
    st.subheader("Individual coin performance")
    st.write(fig)

uniform_weights, investment_cols = uniform(
    returns_df,
    num_coins=investment_set,
    start_date=start_port_date,
    end_date=end_port_date,
)

uniform_weights_dict = {}
for i, coin in enumerate(investment_cols):
    uniform_weights_dict[coin] = uniform_weights[i]
markowitz_weights_dict = markowitz_weights(
    histories_df, start_port_date, investment_cols, analysis_days=365
)

uniform_returns = create_port_rtns(
    returns_df, uniform_weights, investment_cols, start_port_date, end_port_date
)
markotwitz_returns = create_port_rtns(
    returns_df,
    list(markowitz_weights_dict.values()),
    investment_cols,
    start_port_date,
    end_port_date,
)
returns_dict = {"Uniform": uniform_returns, "Markowitz": markotwitz_returns}
strategy_dict = {"Uniform": uniform_weights_dict, "Markowitz": markowitz_weights_dict}
port_return = returns_dict[portfolio_type]

# calculate max drawdown
max_dd, start_idx, end_idx = max_drawdown(port_return)
start_dd = port_return.index[start_idx]
end_dd = port_return.index[end_idx]


port_fig = px.line(port_return, x=port_return.index, y="price (USD)")
port_fig.add_vline(x=start_dd, line_width=1, line_color="red")
port_fig.add_vline(x=end_dd, line_width=1, line_color="red")
port_fig.add_vrect(
    x0=start_dd,
    x1=end_dd,
    line_width=0,
    fillcolor="red",
    opacity=0.05,
    annotation_text="max drawdown ",
)
st.subheader("{} portfolio performance".format(portfolio_type))

weights_df = create_weights_df(strategy_dict[portfolio_type], portfolio_type)

bar_fig = px.bar(weights_df, x="strategy", y="weights", color="assets", width=200)
bar_fig.update_layout(
    showlegend=False,
    xaxis={"visible": False},
)


cols = st.columns([8, 1])
cols[0].write(port_fig)
cols[1].write(bar_fig)

cols = st.columns([1, 3])
outlay = cols[0].number_input("Initial $ amount", min_value=0, value=1000, step=1)
final_amount = outlay * port_return[-1]
max_loss = outlay * max_dd

cols[1].write(
    """For an initial investment of **${:,}**\n

  You would have ended up with **${:,}** \n

  You would have suffered a maximum loss of **{:.0f}%** of your portfolio value
  between **{}** and **{}**""".format(
        outlay, int(final_amount), max_dd * 100, start_dd, end_dd
    )
)
