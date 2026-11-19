
import streamlit as st
import plotly.express as px

from analytics.database import read_sql


st.set_page_config(
    page_title="ReWear | Sales Analysis",
    page_icon="",
    layout="wide"
)

st.title("Sales Analysis")
st.caption("Marketplace sales trends, category performance and order analysis")
st.divider()


@st.cache_data(ttl=300)
def load_monthly_sales():
    return read_sql("""
        SELECT *
        FROM vw_monthly_sales
        ORDER BY month
    """)


@st.cache_data(ttl=300)
def load_category_performance():
    return read_sql("""
        SELECT *
        FROM vw_category_performance
        ORDER BY gmv DESC
    """)


@st.cache_data(ttl=300)
def load_monthly_category_sales():
    return read_sql("""
        SELECT *
        FROM vw_monthly_category_sales
        ORDER BY month
    """)


@st.cache_data(ttl=300)
def load_order_value_distribution():
    return read_sql("""
        SELECT *
        FROM vw_order_value_distribution
    """)


@st.cache_data(ttl=300)
def load_order_status_distribution():
    return read_sql("""
        SELECT *
        FROM vw_order_status_distribution
    """)


@st.cache_data(ttl=300)
def load_top_categories():
    return read_sql("""
        SELECT *
        FROM vw_top_selling_categories
        ORDER BY gmv DESC
        LIMIT 10
    """)



try:
    monthly_df = load_monthly_sales()
    category_df = load_category_performance()
    monthly_category_df = load_monthly_category_sales()
    order_value_df = load_order_value_distribution()
    order_status_df = load_order_status_distribution()
    top_categories_df = load_top_categories()

except Exception as error:
    st.error(f"Could not load sales data: {error}")
    st.stop()


def find_column(df, candidates):
    """Find the first matching column from a list of candidates."""
    for column in candidates:
        if column in df.columns:
            return column
    return None


def show_table(df):
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No data available.")


# MONTHLY SALES TRENDS

st.header("Monthly Sales Trends")

if monthly_df.empty:
    st.info("No monthly sales data available.")
else:
    month_col = find_column(monthly_df, ["month"])

    if month_col:
        monthly_df[month_col] = monthly_df[month_col].astype(str)

    gmv_col = find_column(monthly_df, ["gmv"])
    revenue_col = find_column(
        monthly_df,
        ["marketplace_revenue", "total_revenue"]
    )
    orders_col = find_column(
        monthly_df,
        ["completed_orders", "total_orders", "order_count"]
    )
    aov_col = find_column(
        monthly_df,
        ["average_order_value", "aov"]
    )

    col1, col2 = st.columns(2)

    with col1:
        if month_col and gmv_col:
            fig = px.line(
                monthly_df,
                x=month_col,
                y=gmv_col,
                markers=True,
                title="Monthly GMV",
                labels={
                    month_col: "Month",
                    gmv_col: "GMV (€)"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if month_col and revenue_col:
            fig = px.bar(
                monthly_df,
                x=month_col,
                y=revenue_col,
                title="Monthly Marketplace Revenue",
                labels={
                    month_col: "Month",
                    revenue_col: "Revenue (€)"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        if month_col and orders_col:
            fig = px.line(
                monthly_df,
                x=month_col,
                y=orders_col,
                markers=True,
                title="Monthly Orders",
                labels={
                    month_col: "Month",
                    orders_col: "Orders"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        if month_col and aov_col:
            fig = px.line(
                monthly_df,
                x=month_col,
                y=aov_col,
                markers=True,
                title="Monthly Average Order Value",
                labels={
                    month_col: "Month",
                    aov_col: "AOV (€)"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("View monthly sales data"):
        show_table(monthly_df)


# CATEGORY PERFORMANCE

st.divider()
st.header("Category Performance")

if category_df.empty:
    st.info("No category performance data available.")
else:
    category_col = find_column(
        category_df,
        ["category_name", "category"]
    )
    category_gmv_col = find_column(category_df, ["gmv"])
    category_orders_col = find_column(
        category_df,
        ["completed_orders", "order_count"]
    )

    col1, col2 = st.columns(2)

    with col1:
        if category_col and category_gmv_col:
            chart_df = category_df.sort_values(
                category_gmv_col,
                ascending=True
            ).tail(10)

            fig = px.bar(
                chart_df,
                x=category_gmv_col,
                y=category_col,
                orientation="h",
                title="Top 10 Categories by GMV",
                labels={
                    category_gmv_col: "GMV (€)",
                    category_col: "Category"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if category_col and category_orders_col:
            chart_df = category_df.sort_values(
                category_orders_col,
                ascending=False
            ).head(10)

            fig = px.bar(
                chart_df,
                x=category_col,
                y=category_orders_col,
                title="Top 10 Categories by Completed Orders",
                labels={
                    category_col: "Category",
                    category_orders_col: "Completed Orders"
                }
            )
            fig.update_layout(xaxis_tickangle=-35)
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("View category performance data"):
        show_table(category_df)


# MONTHLY CATEGORY SALES

st.divider()
st.header("Monthly Category Sales")

if not monthly_category_df.empty:
    month_col = find_column(monthly_category_df, ["month"])
    category_col = find_column(
        monthly_category_df,
        ["category_name", "category"]
    )
    gmv_col = find_column(monthly_category_df, ["gmv"])

    if month_col:
        monthly_category_df[month_col] = (
            monthly_category_df[month_col].astype(str)
        )

    if month_col and category_col and gmv_col:
        available_categories = sorted(
            monthly_category_df[category_col].dropna().unique()
        )

        selected_categories = st.multiselect(
            "Select categories",
            options=available_categories,
            default=available_categories[:5]
        )

        filtered_df = monthly_category_df[
            monthly_category_df[category_col].isin(selected_categories)
        ]

        if not filtered_df.empty:
            fig = px.line(
                filtered_df,
                x=month_col,
                y=gmv_col,
                color=category_col,
                markers=True,
                title="Monthly GMV by Category",
                labels={
                    month_col: "Month",
                    gmv_col: "GMV (€)",
                    category_col: "Category"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("View monthly category data"):
        show_table(monthly_category_df)
else:
    st.info("No monthly category sales data available.")


# ORDER VALUE DISTRIBUTION

st.divider()
st.header("Order Value Distribution")

if not order_value_df.empty:
    bucket_col = find_column(
        order_value_df,
        ["value_bucket", "order_value_bucket", "price_range", "order_value_range"]
    )
    count_col = find_column(
        order_value_df,
        ["order_count", "number_of_orders", "total_orders", "count"]
    )

    if bucket_col and count_col:
        fig = px.bar(
            order_value_df,
            x=bucket_col,
            y=count_col,
            title="Orders by Order Value Range",
            labels={
                bucket_col: "Order Value Range",
                count_col: "Number of Orders"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("View order value distribution data"):
        show_table(order_value_df)
else:
    st.info("No order value distribution data available.")


# ORDER STATUS DISTRIBUTION
st.divider()
st.header("Order Status Distribution")

if not order_status_df.empty:
    status_col = find_column(
        order_status_df,
        ["status_name", "order_status", "status"]
    )
    status_count_col = find_column(
        order_status_df,
        ["order_count", "total_orders", "count"]
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        if status_col and status_count_col:
            fig = px.pie(
                order_status_df,
                names=status_col,
                values=status_count_col,
                hole=0.45,
                title="Orders by Status"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        show_table(order_status_df)
else:
    st.info("No order status data available.")


st.divider()
