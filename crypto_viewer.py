import streamlit as st
import requests
import json
import plotly.express as px
import pandas as pd
import datetime as dt
from risk_metrics import annual_return, absolute_return, annual_vol, max_drawdown

try:
    from PIL import Image
except ImportError:
    import Image
import numpy as np

st.markdown(
    """
  <style>

.css-1inwz65 {
    font-size: 0px;
}
  </style>
  """,
    unsafe_allow_html=True,
)


def load_data(limit="10"):
    """
    Returns a dictionary with data for each of the top 'limit' cypto currencies
    ranked by market cap. The data is generated by querying the coincap API
    /assets endpoint. See coincap documentation for more info:
    https://docs.coincap.io/

    Parameters:
      limit (str): The number of crypto coins that you want to return data for.
        Ranked in order of market cap.

    Returns:
      (dict): A dictionary object of data.

    """
    url = "https://api.coincap.io/v2/assets"
    # N.B. here adampt the params dict to only request what you need
    payload = {"limit": limit}
    headers = {}
    return requests.request("GET", url, params=payload, headers=headers).json()


def load_histories(ids_list):
    url = "http://api.coincap.io/v2/assets/{}/history?interval=d1"

    payload = {}
    headers = {}

    histories_dict = {}
    for id in ids_list:
        response_histories = requests.request(
            "GET", url.format(id), headers=headers, data=payload
        )
        histories_json = response_histories.json()
        histories_dict[id] = histories_json["data"]
    return histories_dict


def gen_symbols(assets_json):
    symbols_list = []
    names_list = []
    ids_list = []
    for dict in assets_json["data"]:
        symbols_list.append(dict["symbol"])
        names_list.append(dict["name"])
        ids_list.append(dict["id"])
    return symbols_list, names_list, ids_list


def write_symbols(symbols_list):
    cols = st.columns(len(symbols_list))
    for i, symbol in enumerate(symbols_list):
        col = cols[i]
        col.image(f"logos/{symbol}.png", width=40)
        globals()[st.session_state.names[i]] = col.checkbox(symbol, value=0)
        # col.checkbox(symbol, st.image(f'logos/{symbol}.png',width=40))


if "assets_json" not in st.session_state:
    st.session_state.assets_json = load_data()
    symbols, names, ids = gen_symbols(st.session_state.assets_json)
    st.session_state.symbols = symbols
    st.session_state.names = names
    st.session_state.ids = ids
    st.session_state.histories = load_histories(ids)
    id_symbol_map = {}
    for i, id in enumerate(ids):
        id_symbol_map[id] = symbols[i]
    st.session_state.id_symbol_map = id_symbol_map


# write_symbols(st.session_state.symbols)
symbols_list = st.session_state.symbols
names_list = st.session_state.names
ids_list = st.session_state.ids
asset_json = st.session_state.assets_json
histories_dict = st.session_state.histories
id_symbol_map = st.session_state.id_symbol_map


def date_conv(date):
    return dt.datetime.strptime(date, "%Y-%m-%d")


price_histories_df = pd.DataFrame(columns=["coin", "date", "price"])
return_histories_df = pd.DataFrame(columns=["coin", "date", "price"])
for id in ids_list:
    price = []
    date = []
    for observation in histories_dict[id]:
        date.append(date_conv(observation["date"][0:10]))
        # date.append(observation['time'])
        price.append(float(observation["priceUsd"]))
    price_df = pd.DataFrame({"coin": id, "date": date, "price": price})
    price_histories_df = pd.concat([price_histories_df, price_df])
    returns = [float(b) / float(a) for b, a in zip(price[1:], price[:-1])]
    returns_df = pd.DataFrame({"coin": id, "date": date[1:], "price": returns})
    return_histories_df = pd.concat([return_histories_df, returns_df])


start_date = dt.date.today() - dt.timedelta(360)
rebased_prices_df = pd.DataFrame(columns=["coin", "date", "price", "rebased_price"])
for id in ids_list:
    temp_rebase_df = return_histories_df[
        (return_histories_df["date"] >= pd.Timestamp(start_date))
        & (return_histories_df["coin"] == id)
    ]
    rebased_price = [1]
    for i in range(1, len(temp_rebase_df)):
        rebased_price.append(temp_rebase_df["price"].iloc[i] * rebased_price[i - 1])
    temp_rebase_df["rebased_price"] = rebased_price
    rebased_prices_df = pd.concat([rebased_prices_df, temp_rebase_df])

fig2 = px.line(rebased_prices_df, x="date", y="rebased_price", color="coin")
st.write(fig2)
cols = st.columns(len(symbols_list))
checkboxes = []


def write_coins(id_symbol_map, n_cols=5):
    n_coins = len(id_symbol_map)
    n_rows = 1 + n_coins // int(n_cols)

    rows = [st.container() for _ in range(n_rows)]
    cols_per_row = [r.columns(n_cols) for r in rows]
    cols = [column for row in cols_per_row for column in row]

    # cols = st.columns(n_coins)
    # checkboxes=[]
    for i, id in enumerate(id_symbol_map):
        cols[i].image("logos/{}.png".format(id_symbol_map[id]), width=40)
        globals()[st.session_state.names[i]] = cols[i].checkbox(
            "include", value=1, key=id
        )
        globals()["slider_" + ids_list[i]] = cols[i].slider(
            id, min_value=0, max_value=100, value=50, key=id
        )
        checkboxes.append(globals()[st.session_state.names[i]])


write_coins(id_symbol_map)


# for i, symbol in enumerate(symbols_list):
#  col = cols[i]
#  col.image(f'logos/{symbol}.png',width=40)
#  globals()[st.session_state.names[i]] = col.checkbox(symbol, value = 1)
#  checkboxes.append(globals()[st.session_state.names[i]])


# if any(checkboxes):
#  checked_ids=[]
#  cols2 = st.columns(sum(checkboxes))
#  j=0
#  for i, value in enumerate(checkboxes):
#    if value==1:
#      checked_ids.append(ids_list[i])
#      col2=cols2[j]
#      col2.image(f'logos/{symbols_list[i]}.png',width=20)
#      j+=1


def create_grid(top_left, bottom_right):
    num_rows = 3
    num_cols = 7
    col_positions = np.linspace(top_left[0], bottom_right[0], num=num_cols)
    row_positions = np.linspace(top_left[1], bottom_right[1], num=num_rows)
    return [
        (int(col_positions[i]), int(row_positions[j]))
        for j in range(num_rows)
        for i in range(num_cols)
    ]


# These are the coordinates of the top left and bottom right of the cart image
# given it's curent size. You need to change these if you change the size of the
# cart
top_left = [300, 300]
bottom_right = [650, 450]

grid = create_grid(top_left, bottom_right)


def add_logo(background, symbol, position, size=(70, 70)):
    bg = Image.open(background)
    fg = Image.open("logos/{}.png".format(symbol))

    bg = bg.convert("RGBA")
    fg = fg.convert("RGBA")

    # Resize logo
    fg_resized = fg.resize(size)

    # Overlay logo onto background at position
    bg.paste(fg_resized, box=position, mask=fg_resized)

    # Save result
    bg.save(background)


cart_cols = st.columns([3, 2])


if any(checkboxes):
    checked_ids = []
    for i, value in enumerate(checkboxes):
        if value == 1:
            checked_ids.append(ids_list[i])
            # cart_cols[1].image(f'logos/{symbols_list[i]}.png',width=20)
            # cart_cols[2].slider(ids_list[i],min_value=0, max_value=100, value=50)


# change the below to make it run only if checked_ids ecists - i.e. wrap it up oin a function
original = Image.open("images/cart.png")
original.save("images/background.png")
position_ids = [round(x) for x in np.linspace(0, len(grid) - 1, num=len(checked_ids))]
for i, id in enumerate(checked_ids):
    size = tuple([int(num * globals()["slider_" + id] / 50) for num in (70, 70)])

    add_logo(
        "images/background.png", id_symbol_map[id], grid[position_ids[i]], size=size
    )

weights = []
for id in checked_ids:
    weights.append(globals()["slider_" + id])
sum_weights = sum(weights)
weights = [weight / sum_weights for weight in weights]

weights_df = pd.DataFrame(
    {"ids": checked_ids, "weights": weights, "portfolio": "port_1"}
)
pie_fig = px.pie(weights_df, values="weights", names="ids")
pie_fig.update_layout(showlegend=False)

bar_fig = px.bar(weights_df, x="portfolio", y="weights", color="ids", width=200)
bar_fig.update_layout(showlegend=False)

cart_cols[0].image("images/background.png", width=400)
cart_cols[1].write(bar_fig)
gen_port = st.button("Generate portfolio return")

metrics_dict = {
    "annual_return": "Return (annualised)",
    "absolute_return": "Return over period",
    "annual_vol": "Annual volatility",
    "max_drawdown": "Max loss",
}


def write_metrics(prices, *metrics):
    for metric in metrics:
        cols = st.columns(2)
        if metric.__name__ == "max_drawdown":
            cols[0].write(metrics_dict[metric.__name__] + ": ")
            cols[1].write("{:.2%}".format(metric(prices)[0]))
        else:
            cols[0].write(metrics_dict[metric.__name__] + ": ")
            cols[1].write("{:.2%}".format(metric(prices)))


if gen_port:
    # adjust weight calculation to read in from globals()["slider_"+ids_list[i]]
    # weights = [1/len(checked_ids)]*len(checked_ids)
    portfolio_dict = {checked_ids[i]: weights[i] for i in range(len(checked_ids))}
    start_date = dt.date.today() - dt.timedelta(360)
    weighted_prices_df = pd.DataFrame(
        columns=["coin", "date", "price", "weighted_price"]
    )
    for id in checked_ids:
        temp_weight_df = return_histories_df[
            (return_histories_df["date"] >= pd.Timestamp(start_date))
            & (return_histories_df["coin"] == id)
        ]
        weighted_price = [portfolio_dict[id]]
        for i in range(1, len(temp_weight_df)):
            weighted_price.append(
                temp_weight_df["price"].iloc[i] * weighted_price[i - 1]
            )
        temp_weight_df["weighted_price"] = weighted_price
        weighted_prices_df = pd.concat([weighted_prices_df, temp_weight_df])
    date_list = [start_date + dt.timedelta(days=x) for x in range(360)]
    port_returns = []
    for date in date_list:
        port_returns.append(
            weighted_prices_df["weighted_price"][
                weighted_prices_df["date"] == pd.Timestamp(date)
            ].sum()
        )
    port_returns_df = pd.DataFrame({"date": date_list, "price": port_returns})
    prices = port_returns_df["price"]
    max_dd, start_idx, end_idx = max_drawdown(prices)
    start_dt = port_returns_df["date"].iloc[start_idx]
    end_dt = port_returns_df["date"].iloc[end_idx]
    fig3 = px.line(port_returns_df, x="date", y="price")
    fig3.add_vline(x=start_dt, line_width=1, line_color="red")
    fig3.add_vline(x=end_dt, line_width=1, line_color="red")
    fig3.add_vrect(
        x0=start_dt,
        x1=end_dt,
        line_width=0,
        fillcolor="red",
        opacity=0.05,
        annotation_text="max loss ",
    )
    st.write(fig3)

    st.title("Risk metrics")
    write_metrics(prices, absolute_return, annual_return, annual_vol, max_drawdown)

    # for i, symbol in enumerate(symbols_list):
    #  col2 = cols2[i]
    #  col.image(f'logos/{symbol}.png',width=40)
    # price_subset_df = price_histories_df[price_histories_df['coin'].isin(checked_ids)]
    # rebased_subset_df = rebased_prices_df[rebased_prices_df['coin'].isin(checked_ids)]
    # fig1 = px.line(price_subset_df, x="date", y="price", color="coin")
    # st.write(fig1)
    # fig2 = px.line(rebased_subset_df, x="date", y="rebased_price", color="coin")
    # st.write(fig2)
