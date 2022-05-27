import streamlit as st
import plotly.express as px
from datetime import date, timedelta
from data_creator import create_market_cap_dict, gen_rebased_df, ids2names_dict, names2ids_dict, create_assets, gen_symbols, create_histories_df, create_unix_dates, create_returns_df, create_rebased_df, date_range
from plot_creator import write_coins, create_chart_df, load_images, gen_performance_df, add_drawdown
from port_creator import gen_all_returns, markowitz_weights_dict, uniform_weights_dict, ids_with_histories, uniform, create_port_rtns, markowitz_weights, create_weights_df
from risk_metrics import max_drawdown


st.markdown(
  """
  <style>

.css-1xsoh1l {
    font-size: 0px;
}
.css-1xsoh1l{
  color: rgb(120 190 33);
}
.css-jhf39w {
  color: rgba(120, 190, 33, 1);
}
.css-jv3mmh {
  background-color: rgb(120, 190, 33);
}
  </style>
  """,
  unsafe_allow_html = True
)

# load start and end dates for investment analysis
lookback_years = 5 # max date range for backtest will be: lookback_years - 1
start_date = date.today() - timedelta(365)
end_date = date.today()

if 'start_date' not in st.session_state:
  st.session_state.start_date = start_date
  st.session_state.end_date = end_date


# Pull down histories from coincap, and create dataframes for historic prices,
# returns and rebased cumulative price; histories_df, returns_df, and
# rebased_df, respectively.
assets_json = create_assets(total_coins=50)
symbols, names, coin_ids = gen_symbols(assets_json)
ids2symbols = ids2names_dict(coin_ids, symbols)
ids2names_dict=ids2names_dict(coin_ids, names)
names2ids_dict = names2ids_dict(names, coin_ids)
market_cap_dict = create_market_cap_dict(assets_json)
start_unix, end_unix = create_unix_dates(today=date.today(), lookback_years=lookback_years)
histories_df = create_histories_df(coin_ids, start_unix, end_unix)

# Create list of coin ids with full hisoties over the backtest period
ids_with_histories = ids_with_histories(histories_df,
  st.session_state.start_date, st.session_state.end_date)
names_with_histories = list(map(ids2names_dict.get, ids_with_histories))

def change_date_range():
  st.session_state.start_date = st.session_state.myslider[0]
  st.session_state.end_date = st.session_state.myslider[1]


with st.sidebar:
  st.subheader("Select a portfolio and a coin to compare on the graph")
  portfolio_type = st.selectbox(
  'Select portfolio strategy',
  ('Uniform', 'Markowitz')
  )
  max_coins = st.number_input(
    "Maximum number of coins in portfolio",
    min_value=1,
    max_value=50,
    value=10,
    help='''
    Coins will be added to your "investment set" in order of largest market cap.

    The "investment set" is the group of assets from which your portfolio is
    constructed. Depending on the portfolio strategy you choose, not all of the
    assets in your investment set will be included in your portfolio.

    '''
  )
  selected_coin = st.selectbox(
  'Select coin',
  names_with_histories
  )


# Add select slider to allow
date_list = date_range(end_date,lookback_years-1)
start_port_date, end_port_date = st.select_slider(
     'Select date range for backtest (max 4 years)',
     key="myslider",
     options=date_list,
     #value=(date.today() - timedelta(365), date.today()),
     value = (st.session_state.start_date, st.session_state.end_date),
     on_change=change_date_range
     )

# calculate weghts for the uniform and markowitz pfs
uniform_weights_dict = uniform_weights_dict(ids_with_histories[:max_coins])
markowitz_weights_dict = markowitz_weights_dict(histories_df,
  st.session_state.start_date ,ids_with_histories[:max_coins], analysis_days=365)
strategy_dict = {'Uniform': uniform_weights_dict, 'Markowitz':markowitz_weights_dict}

# calculate returns for the portfolios and add to it the  rebased df for assets
# with hisories. This is the new returns_df
rebased_df = gen_rebased_df(histories_df, ids_with_histories,
  st.session_state.start_date, st.session_state.end_date)

all_returns_df = gen_all_returns(rebased_df, ids_with_histories, strategy_dict)

chart_df = create_chart_df(all_returns_df, portfolio_type, names2ids_dict[selected_coin])

fig = px.line(chart_df, x=chart_df.index, y='value', color='variable')
fig, port_dd, port_dd_start, port_dd_end = add_drawdown(fig, all_returns_df, portfolio_type)
#fig, coin_dd, coin_dd_start, coin_dd_end = add_drawdown(fig, all_returns_df, names2ids_dict[selected_coin])
st.write(fig)


st.subheader("{} portfolio performance".format(portfolio_type))

cols = st.columns([1,3])
outlay = cols[0].number_input('Initial $ amount', min_value=0, value=1000,
  step=1)
final_amount = outlay*all_returns_df[portfolio_type][-1]
max_loss=outlay*port_dd

cols[1].markdown('''For an initial investment of **${:,}**\n

  You would have ended up with **${:,}** \n

  You would have suffered a maximum loss of **{:.0f}%** of your portfolio value
  between **{}** and **{}**'''.format(
    outlay, int(final_amount), port_dd*100, port_dd_start, port_dd_end ),
    unsafe_allow_html = True)

non_zero_coins = [key for key in strategy_dict[portfolio_type].keys() if strategy_dict[portfolio_type][key]>0]

with st.sidebar:
  st.markdown(portfolio_type + " portfolio weights:" , unsafe_allow_html=False)
  write_coins(non_zero_coins, strategy_dict[portfolio_type], ids2names_dict)

performance_df = gen_performance_df(all_returns_df, market_cap_dict)


st.subheader("Overview of performance of all available strategies")
st.dataframe(performance_df.style.background_gradient(cmap='Greens',
  subset=['Risk adjusted return %', 'Return over period %'])
  .background_gradient(cmap='Reds',
  subset=['Annual volatility', 'Max loss %']).format("{:,.2f}",
  subset=['Risk adjusted return %', 'Return over period %', 'Annual volatility',
  'Max loss %']).format("{:,.0f}", subset=['Market cap $M']))


