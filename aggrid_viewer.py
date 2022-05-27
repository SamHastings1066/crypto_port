import streamlit as st
import plotly.express as px
from datetime import date, timedelta
from data_creator import create_market_cap_dict, gen_rebased_df, ids2names_dict, names2ids_dict, create_assets, gen_symbols, create_histories_df, create_unix_dates, create_returns_df, create_rebased_df, date_range
from plot_creator import get_pre_selected_idx, write_coins, write_bespoke_coins, create_comparison_df, load_images, gen_performance_ag_df, add_drawdown
from port_creator import gen_all_returns, markowitz_weights_dict, uniform_weights_dict, ids_with_histories, uniform, create_port_rtns, markowitz_weights, create_weights_df
from risk_metrics import max_drawdown
from st_aggrid import AgGrid, GridOptionsBuilder

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

if 'max_coins' not in st.session_state:
  st.session_state.max_coins = 10

if 'start_id' not in st.session_state:
  st.session_state.start_id = 1

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

# calculate weghts for the uniform and markowitz pfs
uniform_weights_dict = uniform_weights_dict(ids_with_histories[:st.session_state.max_coins])
#markowitz_weights_dict = markowitz_weights_dict(histories_df,
#  st.session_state.start_date ,ids_with_histories[:max_coins], analysis_days=365)
strategy_dict = {'Uniform': uniform_weights_dict}#, 'Markowitz':markowitz_weights_dict}

if "strategy_dict" not in st.session_state:
  st.session_state.strategy_dict=strategy_dict

with st.sidebar:
  st.subheader("Portfolio weights viewer")
  portfolio_type = st.selectbox(
  'Select portfolio strategy',
  ['Create your own'] + (list(st.session_state.strategy_dict.keys())),
  index = st.session_state.start_id
  )


if st.checkbox("Explain this"):
  st.subheader("What's this all about then, eh?")
  st.write('''
  The app allows you to construct your own portfolios of crypto currencies and view their
  historic performance alongside the performance of individual crypto
  currencies over an investment period of your choosing.

  To view the assets and weights comprising a partciclar portfolio select the
  portfolio of interest in the 'Select portfolio strategy' dropdown (a uniform
  portfolio fo the top ten lagest coins has been automatically created for you
  to start with).

  To create your own portfolio:

  1. Select 'Create your own' in the 'select portfolio strategy' dropdown;
  2. Select the maximum number of coins in your portfolio;
  3. Select the relative weights for each of these assets;
  4. Choose a name for your portfolio and click add portfolio;
  5. Click update viewer;

  You can sort and filter the performance metrics table on each of the columns.

  To add an asset to the performance chart, select the corresponding select box.
  ''')

# Add select slider to allow
date_list = date_range(end_date,lookback_years-1)
start_port_date, end_port_date = st.select_slider(
     'Select backtest date range',
     key="myslider",
     options=date_list,
     #value=(date.today() - timedelta(365), date.today()),
     value = (st.session_state.start_date, st.session_state.end_date),
     on_change=change_date_range
     )

# Move the definition of strategy_dict to about the potfolio_type selectbox
# This will require that you define max_coins in session state,a dn the
# have the max_coins number_input update the max coins session state.
#  = 10 and let it be


# calculate returns for the portfolios and add to it the  rebased df for assets
# with hisories. This is the new returns_df
rebased_df = gen_rebased_df(histories_df, ids_with_histories,
  st.session_state.start_date, st.session_state.end_date)

all_returns_df = gen_all_returns(rebased_df, ids_with_histories,st.session_state.strategy_dict)



if portfolio_type == 'Create your own':
  with st.sidebar:
    st.session_state.max_coins = st.number_input(
    "Maximum number of coins in portfolio",
    min_value=1,
    max_value=20,
    value=10,
    help='''
    Coins will be added to your "investment set" in order of largest market cap.

    The "investment set" is the group of assets from which your portfolio is
    constructed. Depending on the portfolio strategy you choose, not all of the
    assets in your investment set will be included in your portfolio.

    '''
    )
    st.markdown("Bespoke portfolio weights (relative):" , unsafe_allow_html=False)
    bespoke_weights = write_bespoke_coins(names_with_histories[:st.session_state.max_coins])
    bespoke_cols = st.columns(2)
    bespoke_cols[0].write(" ")
    bespoke_cols[0].write(" ")
    add_bespoke = bespoke_cols[0].button("Add portfolio", key='bespoke_button')
    bespoke_name = bespoke_cols[1].text_input("Choose portfolio name")
    if add_bespoke:
      if bespoke_name=="" or bespoke_name in all_returns_df.columns:
        st.warning("Please give your portfolio a unique name")
      else:
        beskpoke_weights_dict={}
        for i, wt in enumerate(bespoke_weights):
          beskpoke_weights_dict[coin_ids[i]] = wt
        st.session_state.strategy_dict[bespoke_name] = beskpoke_weights_dict
        st.session_state.start_id = len(st.session_state.strategy_dict)
        st.success("Porfolio added, update viewer to see results")
        st.button('Update viewer', on_click = change_date_range)
    #st.write(st.session_state.strategy_dict)
else:
  non_zero_coins = [key for key in st.session_state.strategy_dict[portfolio_type].keys() if st.session_state.strategy_dict[portfolio_type][key]>0]
  with st.sidebar:
    st.markdown(portfolio_type + " portfolio weights (%):" , unsafe_allow_html=False)
    write_coins(non_zero_coins, st.session_state.strategy_dict[portfolio_type], ids2names_dict)

performance_ag_df = gen_performance_ag_df(all_returns_df, market_cap_dict,
  st.session_state.strategy_dict)

gb = GridOptionsBuilder.from_dataframe(performance_ag_df)
gb.configure_selection('multiple', use_checkbox=True, pre_selected_rows = [0])
gridOptions = gb.build()

st.subheader("Performance metrics")
grid_response = AgGrid(performance_ag_df, gridOptions=gridOptions,
  data_return_mode = 'FILTERED', allow_unsafe_jscode=True, height = 200,
  update_mode='MODEL_CHANGED') # MANUAL SELECTION_CHANGED

selected_assets = []
for row in grid_response['selected_rows']:
  selected_assets.append(row['Asset'])

chart_df = create_comparison_df(all_returns_df, selected_assets)

fig = px.line(chart_df, x=chart_df.index, y='Value (USD)', color='Asset')

st.subheader("Performance chart")
st.write(fig)
