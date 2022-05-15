import streamlit as st

id_symbol_map = {'bitcoin': 'BTC',
 'ethereum': 'ETH',
 'tether': 'USDT',
 'binance-coin': 'BNB',
 'usd-coin': 'USDC',
 'xrp': 'XRP',
 'solana': 'SOL',
 'cardano': 'ADA',
 'terra-luna': 'LUNA',
 'terrausd': 'UST'}


def write_coins(id_symbol_map, n_cols=5):
  n_coins = len(id_symbol_map)
  n_rows = 1 + n_coins // int(n_cols)

  rows = [st.container() for _ in range(n_rows)]
  cols_per_row = [r.columns(n_cols) for r in rows]
  cols = [column for row in cols_per_row for column in row]

  #cols = st.columns(n_coins)
  #checkboxes=[]
  for i, id in enumerate(id_symbol_map):
    cols[i].image('logos/{}.png'.format(id_symbol_map[id]),width=40)
    cols[i].checkbox("include", value=1, key=id)
    cols[i].slider(id, min_value=0, max_value=100, value=50, key=id)

write_coins(id_symbol_map)

  #col = cols[i]
  #col.image(f'logos/{symbol}.png',width=40)
  #globals()[st.session_state.names[i]] = col.checkbox(symbol, value = 0)
  #checkboxes.append(globals()[st.session_state.names[i]])
