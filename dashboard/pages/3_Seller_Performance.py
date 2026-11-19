
import streamlit as st
import plotly.express as px

from analytics.database import read_sql


st.set_page_config(
    page_title="ReWear | Seller Performance",
    layout="wide"
)

st.title("Seller Performance")
st.caption("Seller activity, sales performance and marketplace reputation")



@st.cache_data(ttl=300)
def load_seller_performance():
    return read_sql("""
        SELECT *
        FROM vw_seller_performance
    """)


@st.cache_data(ttl=300)
def load_top_sellers():
    return read_sql("""
        SELECT *
        FROM vw_top_sellers
        ORDER BY total_gmv DESC
    """)


@st.cache_data(ttl=300)
def load_country_performance():
    return read_sql("""
        SELECT *
        FROM vw_seller_country_performance
    """)


@st.cache_data(ttl=300)
def load_monthly_performance():
    return read_sql("""
        SELECT *
        FROM vw_monthly_seller_performance
        ORDER BY month
    """)


@st.cache_data(ttl=300)
def load_rating_distribution():
    return read_sql("""
        SELECT *
        FROM vw_seller_rating_distribution
    """)


@st.cache_data(ttl=300)
def load_seller_segments():
    return read_sql("""
        SELECT *
        FROM vw_seller_segments
    """)


try:
    seller_df = load_seller_performance()
    top_sellers_df = load_top_sellers()
    country_df = load_country_performance()
    monthly_df = load_monthly_performance()
    ratings_df = load_rating_distribution()
    segments_df = load_seller_segments()

except Exception as error:
    st.error(f"Could not load seller analytics: {error}")
    st.stop()


def find_column(df, candidates):
    for column in candidates:
        if column in df.columns:
            return column
    return None


def show_table(df):
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No data available.")

# SELLER OVERVIEW

st.header("Seller Overview")

if not seller_df.empty:
    completed_col = find_column(
        seller_df,
        ["completed_orders", "total_completed_orders"]
    )
    gmv_col = find_column(seller_df, ["total_gmv", "gmv"])
    rating_col = find_column(
        seller_df,
        ["average_rating", "avg_rating"]
    )

    total_sellers = len(seller_df)

    active_sellers = (
        int((seller_df[completed_col] > 0).sum())
        if completed_col else 0
    )

    total_gmv = seller_df[gmv_col].sum() if gmv_col else 0

    average_rating = (
        seller_df.loc[seller_df[rating_col] > 0, rating_col].mean()
        if rating_col else None
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Sellers", f"{total_sellers:,}")
    col2.metric("Sellers with Completed Sales", f"{active_sellers:,}")
    col3.metric("Seller GMV", f"€{total_gmv:,.2f}")

    if average_rating is not None:
        col4.metric("Average Seller Rating", f"{average_rating:.2f}/5")
    else:
        col4.metric("Average Seller Rating", "N/A")

else:
    st.info("No seller performance data available.")


# TOP SELLERS

st.divider()
st.header("Top Sellers by GMV")

if not top_sellers_df.empty:
    username_col = find_column(
        top_sellers_df,
        ["username", "seller_username"]
    )
    seller_id_col = find_column(
        top_sellers_df,
        ["seller_id", "user_id"]
    )
    gmv_col = find_column(top_sellers_df, ["total_gmv", "gmv"])
    orders_col = find_column(
        top_sellers_df,
        ["completed_orders", "total_completed_orders"]
    )

    if orders_col:
        minimum_orders = st.slider(
            "Minimum completed orders",
            min_value=1,
            max_value=10,
            value=1
        )

        filtered_sellers = top_sellers_df[
            top_sellers_df[orders_col] >= minimum_orders
        ]
    else:
        filtered_sellers = top_sellers_df.copy()

    if not filtered_sellers.empty and gmv_col:
        chart_name_col = username_col or seller_id_col

        if chart_name_col:
            chart_df = filtered_sellers.nlargest(10, gmv_col)

            fig = px.bar(
                chart_df.sort_values(gmv_col),
                x=gmv_col,
                y=chart_name_col,
                orientation="h",
                title="Top 10 Sellers by GMV",
                labels={
                    gmv_col: "GMV (€)",
                    chart_name_col: "Seller"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            filtered_sellers.sort_values(gmv_col, ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No sellers match the selected minimum order threshold.")
else:
    st.info("No top seller data available.")


# SELLER SEGMENTS

st.divider()
st.header("Seller Segmentation")

if not segments_df.empty:
    segment_col = find_column(
        segments_df,
        ["seller_segment", "segment_name", "segment"]
    )
    count_col = find_column(
        segments_df,
        ["seller_count", "total_sellers", "count"]
    )

    col1, col2 = st.columns(2)

    if segment_col and count_col:
        with col1:
            fig = px.pie(
                segments_df,
                names=segment_col,
                values=count_col,
                hole=0.45,
                title="Seller Distribution by Segment"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                segments_df.sort_values(count_col),
                x=count_col,
                y=segment_col,
                orientation="h",
                title="Number of Sellers per Segment"
            )
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("View seller segment data"):
        show_table(segments_df)
else:
    st.info("No seller segmentation data available.")


# COUNTRY PERFORMANCE

st.divider()
st.header("Seller Performance by Country")

if not country_df.empty:
    country_col = find_column(country_df, ["country"])
    country_gmv_col = find_column(country_df, ["total_gmv", "gmv"])
    country_sellers_col = find_column(
        country_df,
        ["seller_count", "total_sellers", "sellers"]
    )

    col1, col2 = st.columns(2)

    with col1:
        if country_col and country_gmv_col:
            fig = px.bar(
                country_df.sort_values(country_gmv_col),
                x=country_gmv_col,
                y=country_col,
                orientation="h",
                title="GMV by Seller Country",
                labels={
                    country_gmv_col: "GMV (€)",
                    country_col: "Country"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if country_col and country_sellers_col:
            fig = px.bar(
                country_df.sort_values(country_sellers_col),
                x=country_sellers_col,
                y=country_col,
                orientation="h",
                title="Number of Sellers by Country",
                labels={
                    country_sellers_col: "Sellers",
                    country_col: "Country"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("View country performance data"):
        show_table(country_df)
else:
    st.info("No country performance data available.")



# MONTHLY SELLER PERFORMANCE

st.divider()
st.header("Monthly Seller Performance")

if not monthly_df.empty:
    month_col = find_column(monthly_df, ["month"])
    monthly_gmv_col = find_column(monthly_df, ["total_gmv", "gmv"])
    monthly_sellers_col = find_column(
        monthly_df,
        ["active_sellers", "seller_count", "total_sellers"]
    )

    if month_col:
        monthly_df[month_col] = monthly_df[month_col].astype(str)

    col1, col2 = st.columns(2)

    with col1:
        if month_col and monthly_gmv_col:
            fig = px.line(
                monthly_df,
                x=month_col,
                y=monthly_gmv_col,
                markers=True,
                title="Monthly Seller GMV",
                labels={
                    month_col: "Month",
                    monthly_gmv_col: "GMV (€)"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if month_col and monthly_sellers_col:
            fig = px.line(
                monthly_df,
                x=month_col,
                y=monthly_sellers_col,
                markers=True,
                title="Monthly Active Sellers",
                labels={
                    month_col: "Month",
                    monthly_sellers_col: "Active Sellers"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("View monthly seller data"):
        show_table(monthly_df)
else:
    st.info("No monthly seller data available.")

# SELLER RATINGS

st.divider()
st.header("Seller Rating Distribution")

if not ratings_df.empty:
    rating_col = find_column(ratings_df, ["rating"])
    count_col = find_column(
        ratings_df,
        ["review_count", "total_reviews", "count"]
    )

    if rating_col and count_col:
        fig = px.bar(
            ratings_df.sort_values(rating_col),
            x=rating_col,
            y=count_col,
            title="Reviews by Rating",
            labels={
                rating_col: "Rating",
                count_col: "Number of Reviews"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("View rating distribution data"):
        show_table(ratings_df)
else:
    st.info("No seller rating data available.")


st.divider()
