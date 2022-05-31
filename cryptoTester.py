import streamlit as st
import plotly.express as px
from datetime import date, timedelta
from data_creator import create_market_cap_dict, gen_rebased_df, ids2names_dict, names2ids_dict, create_assets, gen_symbols, create_histories_df, create_unix_dates, create_returns_df, create_rebased_df, date_range
from plot_creator import write_coins, write_coins_custom, create_chart_df, load_images, gen_performance_df, add_drawdown
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

if 'max_coins' not in st.session_state:
  st.session_state.max_coins = 8

if 'start_id' not in st.session_state:
  st.session_state.start_id = 1 # this is the id of the selected portfolio.

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

st.write('''
N.B. This app is in Beta, it will be buggy and some of the calculation may be
  erroneous. **It is deeeeeefinitely not investment advice**.
''', unsafe_allow_html = True)
with st.expander("Explain this app 🤔"):
  st.subheader("What's this all about then, eh?")
  st.write('''

  This app allows you to graph the historic performance of a portfolio of
  your choosing against an individual coin of your choosing. You can
  compare the hisoric performance of all available assets (portfolios and coins)
  in the overview table at the bottom of the page.

  The 'Pofolio vs coin' chart displays the historic performance of the selected
  portfolio and coin for the selected date range, rebased to $1 at the start
  date.

  To switch focus between the selected portfolio and coin, use the radio buttons
  above the graph. For the asset under focus the "maximum drawdown" is drawn
  on the graph (this is the maximum loss the asset suffered over the selected
  period). A high level view of the performance of the asset under focus is also
  given inside the 'Asset performance' expander.

  The 'Overview of performance section' sets out performance metrics for all of
  the portfolios and coins, over the selected investment period. The table can
  be sorted based on the metric of interest.

  There are two pre-defined portfolio construction strategies, but you can also
  define your own allocation using the 'Create your own' option in the 'Select
  portfolio strategy' dropdown box in the sidebar.

  Pre-defined portfolios:
  - Uniform - An equal propotion of your initial investment is allocated to each coin in the 'investment set' (i.e. the total number of coins available for investment).
  - Markowitz - Your initial investment is allocated to each coin to achieve the portfolio with the highest sharpe ratio in the 365 day period prior to the investment start date.

  To select how many coins you would like in your investment set using the
  'Maximum number of coins in portfolio' inside the 'Portfolio construction
  settings' expander.

  To adjust the date range for the portfolio backtest using the slider
  widget.

  To create your own portfolio:

  1. Select 'Create your own' in the 'select portfolio strategy' dropdown;
  2. Select the maximum number of coins in your portfolio;
  3. Select the relative weights for each of these assets;
  4. Choose a name for your portfolio and click add portfolio;
  5. Click update viewer;

  ''')

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

with st.sidebar:
  st.subheader("Select a coin and a portfolio to compare on the graph")
  with st.expander("Portfolio construction settings", expanded = False):
    st.session_state.max_coins = st.number_input(
      "Maximum number of coins in portfolio",
      min_value=1,
      max_value=50,
      value=8,
      key='max_coin_selector',
      help='''
      Coins will be added to your "investment set" in order of largest market cap.

      The "investment set" is the group of assets from which your portfolio is
      constructed. Depending on the portfolio strategy you choose, not all of the
      assets in your investment set will be included in your portfolio.

      '''
    )

# calculate weghts for the uniform and markowitz pfs
uniform_weights = uniform_weights_dict(ids_with_histories[:int(st.session_state.max_coins)])
update_Markowitz = True
try:
  markowitz_weights = markowitz_weights_dict(histories_df,
    st.session_state.start_date ,ids_with_histories[:int(st.session_state.max_coins)], analysis_days=365)
except:
  update_Markowitz = False
  st.warning('Markowitz weights could not be updated for this date range')

if 'strategy_dict' not in st.session_state:
  st.session_state.strategy_dict = {'Uniform': uniform_weights, 'Markowitz':markowitz_weights}
else:
  st.session_state.strategy_dict['Uniform'] = uniform_weights
  if update_Markowitz == True:
    st.session_state.strategy_dict['Markowitz'] = markowitz_weights

#if "strategy_dict" not in st.session_state:
#  st.session_state.strategy_dict=strategy_dict

with st.sidebar:
  selected_coin = st.selectbox(
  'Select coin',
  names_with_histories
  )
  portfolio_type = st.selectbox(
  'Select portfolio strategy',
  ['Create your own'] + (list(st.session_state.strategy_dict.keys())),
  index = st.session_state.start_id
  )






# calculate returns for the portfolios and add to it the  rebased df for assets
# with hisories. This is the new returns_df
rebased_df = gen_rebased_df(histories_df, ids_with_histories,
  st.session_state.start_date, st.session_state.end_date)

all_returns_df = gen_all_returns(rebased_df, ids_with_histories, st.session_state.strategy_dict)

if portfolio_type != 'Create your own':
  st.session_state.portfolio_type = portfolio_type

st.subheader("Portfolio vs coin")
focus=st.radio("Focus on",("Portfolio 📉","Coin 📈"))

chart_df = create_chart_df(all_returns_df, st.session_state.portfolio_type, names2ids_dict[selected_coin])

fig = px.line(chart_df, x=chart_df.index, y='Value (USD)', color='Asset')
if focus == "Portfolio 📉":
  fig, port_dd, port_dd_start, port_dd_end = add_drawdown(fig, all_returns_df, st.session_state.portfolio_type)
else:
  fig, coin_dd, coin_dd_start, coin_dd_end = add_drawdown(fig, all_returns_df, names2ids_dict[selected_coin])

st.write(fig)

with st.expander("Asset performance"):
  if focus == "Portfolio 📉":
    st.subheader("{} portfolio performance".format(st.session_state.portfolio_type))

    cols = st.columns([1,3])
    outlay = cols[0].number_input('Initial $ amount', min_value=0, value=1000,
      step=1)
    final_amount = outlay*all_returns_df[st.session_state.portfolio_type][-1]
    max_loss=outlay*port_dd

    with cols[1]:
      st.markdown('''For an initial investment of **${:,}**'''.format(int(outlay)), unsafe_allow_html = True)
      st.markdown('''You would have ended up with **${:,}**'''.format(int(final_amount)), unsafe_allow_html = True)
      st.markdown('''You would have suffered a maximum loss of **{:.0f}%** of your portfolio value
      between **{}** and **{}**'''.format(port_dd*100, port_dd_start, port_dd_end), unsafe_allow_html = True)
  else:
    st.subheader("{} coin performance".format(selected_coin))

    cols = st.columns([1,3])
    outlay = cols[0].number_input('Initial $ amount', min_value=0, value=1000,
      step=1)
    final_amount = outlay*all_returns_df[names2ids_dict[selected_coin]][-1]
    max_loss=outlay*coin_dd

    with cols[1]:
      st.markdown('''For an initial investment of **${:,}**'''.format(int(outlay)), unsafe_allow_html = True)
      st.markdown('''You would have ended up with **${:,}**'''.format(int(final_amount)), unsafe_allow_html = True)
      st.markdown('''You would have suffered a maximum loss of **{:.0f}%** of your investment value
      between **{}** and **{}**'''.format(coin_dd*100, coin_dd_start, coin_dd_end), unsafe_allow_html = True)

non_zero_coins = [key for key in st.session_state.strategy_dict[st.session_state.portfolio_type].keys() if st.session_state.strategy_dict[st.session_state.portfolio_type][key]>0]

with st.sidebar:
  if portfolio_type == 'Create your own':
    st.markdown("Bespoke portfolio weights (relative):" , unsafe_allow_html=False)
    bespoke_weights = write_coins_custom(names_with_histories[:int(st.session_state.max_coins)])
    #bespoke_weights = write_bespoke_coins(names_with_histories[:st.session_state.max_coins])
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
        #st.session_state.selected_assets.append(bespoke_name)
        st.success("Porfolio added, update viewer to see results")
        st.button('Update viewer', on_click = change_date_range)
        #st.button('Update viewer', on_click = change_date_range)
  else:
    st.markdown(st.session_state.portfolio_type + " portfolio weights (%):" , unsafe_allow_html=False)
    write_coins(non_zero_coins, st.session_state.strategy_dict[st.session_state.portfolio_type], ids2names_dict)

performance_df = gen_performance_df(all_returns_df, market_cap_dict, st.session_state.strategy_dict)


st.subheader("Overview of performance of all available assets")
st.dataframe(performance_df.style.background_gradient(cmap='Greens',
  subset=['Risk / return', 'Total return %'])
  .background_gradient(cmap='Reds',
  subset=['Annual vol', 'Max loss %']).format("{:,.2f}",
  subset=['Risk / return', 'Total return %', 'Annual vol',
  'Max loss %']).format("{:,.0f}", subset=['Market cap $M']))


