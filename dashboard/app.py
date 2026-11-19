
import streamlit as st
import plotly.express as px
import html

from analytics.marketplace import (
    get_marketplace_kpis,
    get_monthly_marketplace_metrics
)

from analytics.sales import (
    get_category_performance,
    get_order_status_distribution
)


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="ReWear | Marketplace Analytics",
    page_icon="",
    layout="wide"
)


# --------------------------------------------------
# STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>

    /* KPI cards */

    .kpi-card {
        border: 1px solid rgba(128, 128, 128, 0.35);
        border-radius: 3px;
        padding: 16px 18px;
        height: 105px;
        box-sizing: border-box;
        background-color: rgba(128, 128, 128, 0.04);
    }

    .kpi-label {
        font-size: 0.76rem;
        font-weight: 600;
        color: #808080;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-bottom: 12px;
    }

    .kpi-value {
        font-size: 1.45rem;
        font-weight: 650;
        line-height: 1.2;
        color: inherit;
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
    }

    /* Search results */

    .search-result {
        padding: 9px 12px;
        border: 1px solid rgba(128, 128, 128, 0.3);
        border-radius: 3px;
        margin-bottom: 6px;
        font-size: 0.9rem;
    }

    .search-category {
        color: #808080;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 3px;
    }

    /* Search input */

    div[data-testid="stTextInput"] input {
        border-radius: 3px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# DATA LOADING
# --------------------------------------------------

@st.cache_data(ttl=300)
def load_marketplace_kpis():
    return get_marketplace_kpis()


@st.cache_data(ttl=300)
def load_monthly_metrics():
    return get_monthly_marketplace_metrics()


@st.cache_data(ttl=300)
def load_categories():
    return get_category_performance()


@st.cache_data(ttl=300)
def load_order_status():
    return get_order_status_distribution()


# --------------------------------------------------
# KPI CARD FUNCTION
# --------------------------------------------------

def render_kpi_card(label, value):

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{html.escape(label)}</div>
            <div class="kpi-value">{html.escape(str(value))}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("ReWear Marketplace Analytics")

st.markdown(
    """
    **Marketplace Overview**

    Monitor marketplace growth, sales performance,
    customer activity, and operational performance.
    """
)

st.divider()


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

try:
    kpi_df = load_marketplace_kpis()
    monthly_df = load_monthly_metrics()
    category_df = load_categories()
    status_df = load_order_status()

    if kpi_df.empty:
        st.warning("No marketplace KPI data available.")
        st.stop()

    kpis = kpi_df.iloc[0]

except Exception as error:
    st.error(f"Unable to load marketplace data: {error}")
    st.stop()


# --------------------------------------------------
# DASHBOARD SEARCH
# --------------------------------------------------

st.subheader("Dashboard Search")

search_query = st.text_input(
    "Search",
    placeholder="Search metrics, categories, order statuses or dashboard pages...",
    label_visibility="collapsed"
)

# Searchable KPI data

kpi_search_data = [
    {
        "name": "Total Orders",
        "value": f"{int(kpis['total_orders']):,}",
        "section": "Marketplace Performance",
        "anchor": "marketplace-performance"
    },
    {
        "name": "Completed Orders",
        "value": f"{int(kpis['completed_orders']):,}",
        "section": "Marketplace Performance",
        "anchor": "marketplace-performance"
    },
    {
        "name": "GMV",
        "value": f"€{float(kpis['total_gmv']):,.2f}",
        "section": "Marketplace Performance",
        "anchor": "marketplace-performance"
    },
    {
        "name": "Marketplace Revenue",
        "value": f"€{float(kpis['marketplace_revenue']):,.2f}",
        "section": "Marketplace Performance",
        "anchor": "marketplace-performance"
    },
    {
        "name": "Average Order Value",
        "value": f"€{float(kpis['average_order_value']):,.2f}",
        "section": "Marketplace Performance",
        "anchor": "marketplace-performance"
    },
    {
        "name": "Unique Buyers",
        "value": f"{int(kpis['total_buyers']):,}",
        "section": "Marketplace Performance",
        "anchor": "marketplace-performance"
    },
    {
        "name": "Unique Sellers",
        "value": f"{int(kpis['total_sellers']):,}",
        "section": "Marketplace Performance",
        "anchor": "marketplace-performance"
    },
    {
        "name": "Cancellation Rate",
        "value": f"{float(kpis['cancellation_rate_pct']):.2f}%",
        "section": "Marketplace Performance",
        "anchor": "marketplace-performance"
    },
    {
        "name": "Refund Rate",
        "value": f"{float(kpis['refund_rate_pct']):.2f}%",
        "section": "Marketplace Performance",
        "anchor": "marketplace-performance"
    }
]


# Dashboard pages

dashboard_pages = [
    {
        "name": "Sales Analysis",
        "description": "Sales trends, GMV and category performance",
        "path": "pages/1_Sales_Analysis.py"
    },
    {
        "name": "Customer Analytics",
        "description": "Customer behaviour, retention and cohorts",
        "path": "pages/2_Customer_Analytics.py"
    },
    {
        "name": "Seller Performance",
        "description": "Seller activity, revenue and rankings",
        "path": "pages/3_Seller_Performance.py"
    },
    {
        "name": "Listing Analytics",
        "description": "Listing inventory and time-to-sale analysis",
        "path": "pages/4_Listing_Analytics.py"
    },
    {
        "name": "Payment and Reviews",
        "description": "Payment performance and customer reviews",
        "path": "pages/5_Payment_and_Reviews.py"
    }
]


# Search results

if search_query.strip():

    query = search_query.strip().lower()

    matching_kpis = [
        item for item in kpi_search_data
        if query in item["name"].lower()
        or query in item["value"].lower()
    ]

    matching_pages = [
        page for page in dashboard_pages
        if query in page["name"].lower()
        or query in page["description"].lower()
    ]

    matching_categories = []

    if not category_df.empty and "category_name" in category_df.columns:

        matching_categories = category_df[
            category_df["category_name"]
            .astype(str)
            .str.contains(query, case=False, na=False)
        ].to_dict("records")

    matching_statuses = []

    if not status_df.empty and "status_name" in status_df.columns:

        matching_statuses = status_df[
            status_df["status_name"]
            .astype(str)
            .str.contains(query, case=False, na=False)
        ].to_dict("records")

    total_matches = (
        len(matching_kpis)
        + len(matching_pages)
        + len(matching_categories)
        + len(matching_statuses)
    )

    with st.container(border=True):

        st.markdown("**Search Results**")

        if total_matches == 0:

            st.info("No matching results found.")

        else:

            st.caption(f"{total_matches} matching results")

            # KPI results

            if matching_kpis:

                st.markdown("**Marketplace Metrics**")

                for item in matching_kpis:

                    st.markdown(
                        f"""
                        <div class="search-result">
                            <div class="search-category">
                                {html.escape(item['section'])}
                            </div>
                            <strong>{html.escape(item['name'])}</strong>
                            &nbsp; — &nbsp;
                            {html.escape(item['value'])}
                            &nbsp; | &nbsp;
                            <a href="#{item['anchor']}">View metric</a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # Category results

            if matching_categories:

                st.markdown("**Categories**")

                for item in matching_categories[:10]:

                    category_name = str(item["category_name"])
                    gmv = float(item.get("gmv", 0) or 0)

                    st.markdown(
                        f"""
                        <div class="search-result">
                            <div class="search-category">Category</div>
                            <strong>{html.escape(category_name)}</strong>
                            &nbsp; — &nbsp;
                            GMV: €{gmv:,.2f}
                            &nbsp; | &nbsp;
                            <a href="#category-performance">View section</a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # Order status results

            if matching_statuses:

                st.markdown("**Order Statuses**")

                for item in matching_statuses:

                    status_name = str(item["status_name"])
                    order_count = int(item.get("order_count", 0) or 0)

                    st.markdown(
                        f"""
                        <div class="search-result">
                            <div class="search-category">Order Status</div>
                            <strong>{html.escape(status_name)}</strong>
                            &nbsp; — &nbsp;
                            {order_count:,} orders
                            &nbsp; | &nbsp;
                            <a href="#order-status-distribution">View section</a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # Dashboard navigation results

            if matching_pages:

                st.markdown("**Dashboard Pages**")

                for page in matching_pages:

                    st.markdown(
                        f"""
                        <div class="search-result">
                            <div class="search-category">Dashboard Navigation</div>
                            <strong>{html.escape(page['name'])}</strong>
                            <br>
                            {html.escape(page['description'])}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.page_link(
                        page["path"],
                        label=f"Open {page['name']}",
                        icon=":material/arrow_forward:"
                    )


st.divider()


# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------

st.markdown(
    '<div id="marketplace-performance"></div>',
    unsafe_allow_html=True
)

st.subheader("Marketplace Performance")

# Three-column layout: all nine KPIs aligned

kpi_values = [
    ("Total Orders", f"{int(kpis['total_orders']):,}"),
    ("Completed Orders", f"{int(kpis['completed_orders']):,}"),
    ("GMV", f"€{float(kpis['total_gmv']):,.2f}"),

    ("Marketplace Revenue", f"€{float(kpis['marketplace_revenue']):,.2f}"),
    ("Average Order Value", f"€{float(kpis['average_order_value']):,.2f}"),
    ("Unique Buyers", f"{int(kpis['total_buyers']):,}"),

    ("Unique Sellers", f"{int(kpis['total_sellers']):,}"),
    ("Cancellation Rate", f"{float(kpis['cancellation_rate_pct']):.2f}%"),
    ("Refund Rate", f"{float(kpis['refund_rate_pct']):.2f}%")
]

for row_start in range(0, 9, 3):

    cols = st.columns(3, gap="medium")

    for col, (label, value) in zip(
        cols,
        kpi_values[row_start:row_start + 3]
    ):

        with col:
            render_kpi_card(label, value)


st.divider()


# --------------------------------------------------
# MONTHLY SALES PERFORMANCE
# --------------------------------------------------

st.markdown(
    '<div id="monthly-sales-performance"></div>',
    unsafe_allow_html=True
)

st.subheader("Monthly Sales Performance")

if not monthly_df.empty:

    monthly_df["month"] = (
        monthly_df["month"].astype(str)
    )

    col1, col2 = st.columns(2)

    with col1:

        fig_gmv = px.line(
            monthly_df,
            x="month",
            y="gmv",
            markers=True,
            title="Monthly GMV",
            labels={
                "month": "Month",
                "gmv": "GMV (€)"
            }
        )

        fig_gmv.update_layout(
            xaxis_tickangle=-45,
            hovermode="x unified"
        )

        st.plotly_chart(
            fig_gmv,
            use_container_width=True
        )

    with col2:

        fig_revenue = px.bar(
            monthly_df,
            x="month",
            y="marketplace_revenue",
            title="Monthly Marketplace Revenue",
            labels={
                "month": "Month",
                "marketplace_revenue": "Revenue (€)"
            }
        )

        fig_revenue.update_layout(
            xaxis_tickangle=-45
        )

        st.plotly_chart(
            fig_revenue,
            use_container_width=True
        )

    col1, col2 = st.columns(2)

    with col1:

        fig_orders = px.line(
            monthly_df,
            x="month",
            y=[
                "total_orders",
                "completed_orders"
            ],
            markers=True,
            title="Monthly Order Activity",
            labels={
                "month": "Month",
                "value": "Orders",
                "variable": "Order Type"
            }
        )

        fig_orders.update_layout(
            xaxis_tickangle=-45
        )

        st.plotly_chart(
            fig_orders,
            use_container_width=True
        )

    with col2:

        fig_aov = px.line(
            monthly_df,
            x="month",
            y="average_order_value",
            markers=True,
            title="Monthly Average Order Value",
            labels={
                "month": "Month",
                "average_order_value": "AOV (€)"
            }
        )

        fig_aov.update_layout(
            xaxis_tickangle=-45
        )

        st.plotly_chart(
            fig_aov,
            use_container_width=True
        )

else:
    st.info("No monthly sales data available.")


st.divider()


# --------------------------------------------------
# CATEGORY PERFORMANCE
# --------------------------------------------------

st.markdown(
    '<div id="category-performance"></div>',
    unsafe_allow_html=True
)

st.subheader("Category Performance")

if not category_df.empty:

    category_df = category_df.sort_values(
        "gmv",
        ascending=False
    ).head(10)

    fig_categories = px.bar(
        category_df.sort_values("gmv"),
        x="gmv",
        y="category_name",
        orientation="h",
        title="Top 10 Categories by GMV",
        labels={
            "gmv": "GMV (€)",
            "category_name": "Category"
        }
    )

    st.plotly_chart(
        fig_categories,
        use_container_width=True
    )


st.divider()


# --------------------------------------------------
# ORDER STATUS DISTRIBUTION
# --------------------------------------------------

st.markdown(
    '<div id="order-status-distribution"></div>',
    unsafe_allow_html=True
)

st.subheader("Order Status Distribution")

if not status_df.empty:

    col1, col2 = st.columns([1, 1])

    with col1:

        fig_status = px.pie(
            status_df,
            names="status_name",
            values="order_count",
            hole=0.45,
            title="Orders by Status"
        )

        st.plotly_chart(
            fig_status,
            use_container_width=True
        )

    with col2:

        st.dataframe(
            status_df,
            use_container_width=True,
            hide_index=True
        )


st.divider()


# --------------------------------------------------
# MONTHLY DATA TABLE
# --------------------------------------------------

with st.expander("View monthly marketplace data"):

    st.dataframe(
        monthly_df,
        use_container_width=True,
        hide_index=True
    )

