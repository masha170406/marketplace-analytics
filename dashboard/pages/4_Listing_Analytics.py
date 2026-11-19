
import streamlit as st
import plotly.express as px

from analytics.database import read_sql


st.set_page_config(
    page_title="ReWear | Listing Analytics",
    layout="wide"
)

st.title("Listing Analytics")
st.caption("Marketplace inventory, listing activity, pricing and time to sale")


@st.cache_data(ttl=300)
def load_inventory():
    return read_sql("SELECT * FROM vw_listing_inventory_summary")


@st.cache_data(ttl=300)
def load_status_distribution():
    return read_sql("SELECT * FROM vw_listing_status_distribution")


@st.cache_data(ttl=300)
def load_category_performance():
    return read_sql("SELECT * FROM vw_listing_category_performance")


@st.cache_data(ttl=300)
def load_monthly_creation():
    return read_sql("""
        SELECT *
        FROM vw_monthly_listing_creation
        ORDER BY month
    """)


@st.cache_data(ttl=300)
def load_time_to_sale():
    return read_sql("SELECT * FROM vw_listing_time_to_sale")


@st.cache_data(ttl=300)
def load_category_time_to_sale():
    return read_sql("SELECT * FROM vw_category_time_to_sale")


@st.cache_data(ttl=300)
def load_price_distribution():
    return read_sql("SELECT * FROM vw_listing_price_distribution")


try:
    inventory_df = load_inventory()
    status_df = load_status_distribution()
    category_df = load_category_performance()
    monthly_df = load_monthly_creation()
    time_to_sale_df = load_time_to_sale()
    category_time_df = load_category_time_to_sale()
    price_df = load_price_distribution()

except Exception as error:
    st.error(f"Could not load listing analytics: {error}")
    st.stop()



def find_column(df, candidates):
    return next(
        (column for column in candidates if column in df.columns),
        None
    )


def show_table(df):
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No data available.")


# INVENTORY OVERVIEW


st.header("Inventory Overview")

if not inventory_df.empty:
    row = inventory_df.iloc[0]

    total_col = find_column(inventory_df, ["total_listings"])
    published_col = find_column(inventory_df, ["published_listings"])
    active_col = find_column(inventory_df, ["active_listings"])
    sold_col = find_column(
        inventory_df,
        ["currently_sold_listings", "sold_listings"]
    )
    price_col = find_column(
        inventory_df,
        ["average_listing_price", "avg_listing_price"]
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    if total_col:
        col1.metric("Total Listings", f"{int(row[total_col]):,}")

    if published_col:
        col2.metric("Published Listings", f"{int(row[published_col]):,}")

    if active_col:
        col3.metric("Active Listings", f"{int(row[active_col]):,}")

    if sold_col:
        col4.metric("Currently Sold", f"{int(row[sold_col]):,}")

    if price_col:
        col5.metric("Average Listing Price", f"€{row[price_col]:,.2f}")

    with st.expander("View inventory summary"):
        show_table(inventory_df)
else:
    st.info("No inventory summary available.")


# LISTING STATUS DISTRIBUTION

st.divider()
st.header("Listing Status Distribution")

if not status_df.empty:
    status_col = find_column(
        status_df,
        ["status_name", "listing_status", "status"]
    )
    count_col = find_column(
        status_df,
        ["listing_count", "total_listings", "count"]
    )

    if status_col and count_col:
        col1, col2 = st.columns(2)

        with col1:
            fig = px.pie(
                status_df,
                names=status_col,
                values=count_col,
                hole=0.45,
                title="Listings by Current Status"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                status_df.sort_values(count_col),
                x=count_col,
                y=status_col,
                orientation="h",
                title="Listing Count by Status"
            )
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("View listing status data"):
        show_table(status_df)
else:
    st.info("No listing status data available.")


# CATEGORY PERFORMANCE


st.divider()
st.header("Listing Performance by Category")

if not category_df.empty:
    category_col = find_column(
        category_df,
        ["category_name", "category"]
    )
    count_col = find_column(
        category_df,
        ["total_listings", "listing_count", "published_listings"]
    )

    if category_col and count_col:
        fig = px.bar(
            category_df.nlargest(10, count_col),
            x=count_col,
            y=category_col,
            orientation="h",
            title="Top 10 Categories by Listing Volume",
            labels={
                count_col: "Listings",
                category_col: "Category"
            }
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("View category listing data"):
        show_table(category_df)
else:
    st.info("No category listing data available.")


# MONTHLY LISTING CREATION

st.divider()
st.header("Monthly Listing Creation")

if not monthly_df.empty:
    month_col = find_column(monthly_df, ["month"])
    count_col = find_column(
        monthly_df,
        ["new_listings", "listing_count", "total_listings"]
    )

    if month_col and count_col:
        monthly_df[month_col] = monthly_df[month_col].astype(str)

        fig = px.bar(
            monthly_df,
            x=month_col,
            y=count_col,
            title="New Listings per Month",
            labels={
                month_col: "Month",
                count_col: "New Listings"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("View monthly listing data"):
        show_table(monthly_df)
else:
    st.info("No monthly listing creation data available.")

# LISTING PRICE DISTRIBUTION

st.divider()
st.header("Listing Price Distribution")

if not price_df.empty:
    bucket_col = find_column(
        price_df,
        ["price_bucket", "price_range", "listing_price_range"]
    )
    count_col = find_column(
        price_df,
        ["listing_count", "total_listings", "count"]
    )

    if bucket_col and count_col:
        fig = px.bar(
            price_df,
            x=bucket_col,
            y=count_col,
            title="Listings by Price Range",
            labels={
                bucket_col: "Price Range",
                count_col: "Number of Listings"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("View price distribution data"):
        show_table(price_df)
else:
    st.info("No listing price distribution data available.")


# TIME TO SALE

st.divider()
st.header("Time to Sale")

if not time_to_sale_df.empty:
    days_col = find_column(
        time_to_sale_df,
        ["days_to_sale", "time_to_sale_days", "days_until_sold"]
    )

    if days_col:
        valid_df = time_to_sale_df.dropna(subset=[days_col])

        if not valid_df.empty:
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Average Days to Sale",
                    f"{valid_df[days_col].mean():.1f}"
                )

            with col2:
                st.metric(
                    "Median Days to Sale",
                    f"{valid_df[days_col].median():.1f}"
                )

            fig = px.histogram(
                valid_df,
                x=days_col,
                nbins=30,
                title="Distribution of Time to Sale",
                labels={days_col: "Days to Sale"}
            )
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("View time-to-sale records"):
        show_table(time_to_sale_df)
else:
    st.info("No time-to-sale data available.")


# TIME TO SALE BY CATEGORY

st.divider()
st.header("Time to Sale by Category")

if not category_time_df.empty:
    category_col = find_column(
        category_time_df,
        ["category_name", "category"]
    )
    days_col = find_column(
        category_time_df,
        ["average_days_to_sale", "avg_days_to_sale", "median_days_to_sale"]
    )

    if category_col and days_col:
        fig = px.bar(
            category_time_df.sort_values(days_col),
            x=days_col,
            y=category_col,
            orientation="h",
            title="Average Time to Sale by Category",
            labels={
                days_col: "Days to Sale",
                category_col: "Category"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("View category time-to-sale data"):
        show_table(category_time_df)
else:
    st.info("No category time-to-sale data available.")


st.divider()
