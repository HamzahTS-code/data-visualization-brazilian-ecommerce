import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "all_data.csv")

all_df = pd.read_csv(csv_path)

sns.set(style="dark")

def create_monthly_orders_df(df):
    monthly_orders_df = df.resample(rule="ME", on="order_purchase_timestamp").agg(
        {"order_id": "count", "price": "sum"}
    )
    monthly_orders_df.index = monthly_orders_df.index.strftime("%Y-%m")
    monthly_orders_df = monthly_orders_df.reset_index()
    monthly_orders_df.rename(
        columns={"order_id": "order_count", "price": "revenue"}, inplace=True
    )
    return monthly_orders_df


def create_sum_order_items_df(df):
    sum_order_items_df = (
        df.groupby("product_category_name_english")
        .order_id.count()
        .sort_values(ascending=False)
        .reset_index()
    )
    sum_order_items_df.rename(columns={"order_id": "order_count"}, inplace=True)
    return sum_order_items_df


def create_byorderstatus_df(df):
    byorderstatus_df = df["order_status"].value_counts().reset_index()
    byorderstatus_df.columns = ["order_status", "order_count"]
    return byorderstatus_df


def create_bystate_df(df):
    bystate_df = df.groupby(by="customer_state").customer_id.nunique().reset_index()
    bystate_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bystate_df


def create_bysellercity_df(df):
    bysellercity_df = (
        df.groupby("seller_city").price.sum().sort_values(ascending=False).reset_index()
    )
    bysellercity_df.rename(columns={"price": "revenue"}, inplace=True)
    return bysellercity_df


def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg(
        {"order_purchase_timestamp": "max", "order_id": "nunique", "price": "sum"}
    )
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]

    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)

    return rfm_df

#all_df = pd.read_csv("all_data.csv")

datetime_columns = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(drop=True, inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

# --- Date filter ---
min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    st.image("logo.png")

    start_date, end_date = st.date_input(
        label="Dataset Date Range",
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date],
    )

main_df = all_df[
    (all_df["order_purchase_timestamp"] >= str(start_date))
    & (all_df["order_purchase_timestamp"] <= str(end_date))
]

monthly_orders_df = create_monthly_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
byorderstatus_df = create_byorderstatus_df(main_df)
bystate_df = create_bystate_df(main_df)
bysellercity_df = create_bysellercity_df(main_df)
rfm_df = create_rfm_df(main_df)

st.header("Olist Brazilian E-Commerce Public Dataset Dashboard :sparkles:")

st.subheader("Monthly Orders & Revenue")

col1, col2 = st.columns(2)

with col1:
    total_orders = monthly_orders_df.order_count.sum()
    st.metric("Total orders", value=f"{total_orders:,}")

with col2:
    total_revenue = format_currency(monthly_orders_df.revenue.sum(), "BRL", locale="pt_BR")
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    monthly_orders_df["order_purchase_timestamp"],
    monthly_orders_df["order_count"],
    marker="o",
    linewidth=2,
    color="#90CAF9",
)
ax.tick_params(axis="y", labelsize=20)
ax.tick_params(axis="x", labelsize=15, rotation=45)
st.pyplot(fig)

# --- Product performance ---
st.subheader("Best & Worst Performing Product Category")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(
    x="order_count",
    y="product_category_name_english",
    data=sum_order_items_df.head(5),
    hue="product_category_name_english",
    palette=colors,
    legend=False,
    ax=ax[0],
)
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Orders", fontsize=30)
ax[0].set_title("Best Performing Category", loc="center", fontsize=50)
ax[0].tick_params(axis="y", labelsize=30)
ax[0].tick_params(axis="x", labelsize=30)

sns.barplot(
    x="order_count",
    y="product_category_name_english",
    data=sum_order_items_df.sort_values(by="order_count", ascending=True).head(5),
    hue="product_category_name_english",
    palette=colors,
    legend=False,
    ax=ax[1],
)
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Orders", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Category", loc="center", fontsize=50)
ax[1].tick_params(axis="y", labelsize=30)
ax[1].tick_params(axis="x", labelsize=30)

st.pyplot(fig)

st.subheader("Order Status & Customer Demographics")

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots(figsize=(20, 10))
    colors = ["#90CAF9"] + ["#D3D3D3"] * (len(byorderstatus_df) - 1)
    sns.barplot(
        y="order_count",
        x="order_status",
        data=byorderstatus_df.sort_values(by="order_count", ascending=False),
        hue="order_status",
        palette=colors,
        legend=False,
        ax=ax,
    )
    ax.set_title("Number of Orders by Status", loc="center", fontsize=50)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.tick_params(axis="x", labelsize=25, rotation=30)
    ax.tick_params(axis="y", labelsize=30)
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots(figsize=(20, 10))
    top_states = bystate_df.sort_values(by="customer_count", ascending=False).head(10)
    colors = ["#90CAF9"] + ["#D3D3D3"] * (len(top_states) - 1)
    sns.barplot(
        y="customer_count",
        x="customer_state",
        data=top_states,
        hue="customer_state",
        palette=colors,
        legend=False,
        ax=ax,
    )
    ax.set_title("Top 10 States by Customer Count", loc="center", fontsize=50)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.tick_params(axis="x", labelsize=25, rotation=30)
    ax.tick_params(axis="y", labelsize=30)
    st.pyplot(fig)

st.subheader("Best & Worst Seller Cities by Revenue")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 6))
colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(
    x="revenue",
    y="seller_city",
    data=bysellercity_df.head(5),
    hue="seller_city",
    palette=colors,
    legend=False,
    ax=ax[0],
)
ax[0].set_ylabel(None)
ax[0].set_xlabel("Total Revenue (R$)")
ax[0].set_title("Best Seller City", loc="center", fontsize=18)
ax[0].tick_params(axis="y", labelsize=15)

sns.barplot(
    x="revenue",
    y="seller_city",
    data=bysellercity_df.sort_values(by="revenue", ascending=True).head(5),
    hue="seller_city",
    palette=colors,
    legend=False,
    ax=ax[1],
)
ax[1].set_ylabel(None)
ax[1].set_xlabel("Total Revenue (R$)")
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Seller City", loc="center", fontsize=18)
ax[1].tick_params(axis="y", labelsize=15)

formatter = ticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
ax[0].xaxis.set_major_formatter(formatter)
ax[1].xaxis.set_major_formatter(formatter)

st.pyplot(fig)

st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_monetary = format_currency(rfm_df.monetary.mean(), "BRL", locale="pt_BR")
    st.metric("Average Monetary", value=avg_monetary)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9"] * 5

sns.barplot(
    y="recency",
    x="customer_id",
    data=rfm_df.sort_values(by="recency", ascending=True).head(5),
    hue="customer_id",
    palette=colors,
    legend=False,
    ax=ax[0],
)
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer_id", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis="x", labelsize=0)
ax[0].tick_params(axis="y", labelsize=30)

sns.barplot(
    y="frequency",
    x="customer_id",
    data=rfm_df.sort_values(by="frequency", ascending=False).head(5),
    hue="customer_id",
    palette=colors,
    legend=False,
    ax=ax[1],
)
ax[1].set_ylabel(None)
ax[1].set_xlabel("customer_id", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis="x", labelsize=0)
ax[1].tick_params(axis="y", labelsize=30)

sns.barplot(
    y="monetary",
    x="customer_id",
    data=rfm_df.sort_values(by="monetary", ascending=False).head(5),
    hue="customer_id",
    palette=colors,
    legend=False,
    ax=ax[2],
)
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer_id", fontsize=30)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis="x", labelsize=0)
ax[2].tick_params(axis="y", labelsize=30)

st.pyplot(fig)

st.subheader("Delivery Time to Customer")

fig, ax = plt.subplots(figsize=(10, 5))
main_df["delivery_customer_time_in_day"].hist(bins=10, ax=ax, color="#90CAF9")
ax.set_title("Distribution of Delivery Time to Customer", fontsize=14, fontweight="bold")
ax.set_xlabel("Delivery Time (days)", fontsize=12)
ax.set_ylabel("Number of Orders", fontsize=12)
st.pyplot(fig)

st.caption("Copyright © Hamzah Tsabatul Aqdam 2026")
