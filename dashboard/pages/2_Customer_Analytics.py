
import streamlit as st
import plotly.express as px
import pandas as pd
import html

from analytics.database import read_sql


st.set_page_config(
    page_title="ReWear | Customer Analytics",
    layout="wide"
)


st.markdown(
    """
    <style>
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
    </style>
    """,
    unsafe_allow_html=True
)


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


@st.cache_data(ttl=300)
def load_customer_segments():
    return read_sql("""
        SELECT *
        FROM vw_customer_segments
    """)


@st.cache_data(ttl=300)
def load_repeat_purchase_metrics():
    return read_sql("""
        SELECT *
        FROM vw_repeat_purchase_metrics
    """)


@st.cache_data(ttl=300)
def load_customer_cohorts():
    return read_sql("""
        SELECT *
        FROM vw_customer_cohorts
    """)


@st.cache_data(ttl=300)
def load_cohort_retention():
    return read_sql("""
        SELECT *
        FROM vw_cohort_retention
    """)


@st.cache_data(ttl=300)
def load_monthly_acquisition():
    return read_sql("""
        SELECT *
        FROM vw_monthly_customer_acquisition
        ORDER BY month
    """)


@st.cache_data(ttl=300)
def load_customer_lifetime_value():
    return read_sql("""
        SELECT *
        FROM vw_customer_lifetime_value
    """)


@st.cache_data(ttl=300)
def load_customer_summary():
    return read_sql("""
        SELECT *
        FROM vw_customer_purchase_summary
    """)



try:
    segments_df = load_customer_segments()
    repeat_df = load_repeat_purchase_metrics()
    cohorts_df = load_customer_cohorts()
    retention_df = load_cohort_retention()
    acquisition_df = load_monthly_acquisition()
    clv_df = load_customer_lifetime_value()
    customer_summary_df = load_customer_summary()

except Exception as error:
    st.error(f"Could not load customer analytics: {error}")
    st.stop()


# CUSTOMER OVERVIEW

st.title("Customer Analytics")

st.caption("Customer behaviour, purchasing patterns and retention")

st.divider()

st.header("Customer Overview")

if not customer_summary_df.empty:

    customer_count = len(customer_summary_df)

    orders_col = next(
        (
            col for col in [
                "completed_orders",
                "total_completed_orders"
            ]
            if col in customer_summary_df.columns
        ),
        None
    )

    buyers_with_orders = (
        customer_summary_df[orders_col].gt(0).sum()
        if orders_col else 0
    )

    repeat_customers = (
        customer_summary_df[orders_col].gt(1).sum()
        if orders_col else 0
    )

    overview_kpis = [
        ("Customers", f"{customer_count:,}"),
        ("Customers with Purchases", f"{buyers_with_orders:,}"),
        ("Repeat Customers", f"{repeat_customers:,}")
    ]

    cols = st.columns(3, gap="medium")

    for col, (label, value) in zip(cols, overview_kpis):
        with col:
            render_kpi_card(label, value)

else:
    st.info("No customer summary data available.")


# REPEAT PURCHASE METRICS

st.divider()
st.header("Repeat Purchase Behaviour")

if not repeat_df.empty:
    metrics = repeat_df.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    for col, label, value_col, suffix in [
        (col1, "Customers with Purchases", "customers_with_purchases", ""),
        (col2, "Repeat Customers", "repeat_customers", ""),
        (col3, "One-Time Customers", "one_time_customers", ""),
        (col4, "Repeat Purchase Rate", "repeat_purchase_rate_pct", "%"),
    ]:
        if value_col in repeat_df.columns:
            value = metrics[value_col]

            if pd.notna(value):
                formatted_value = (
                    f"{value:.2f}%"
                    if suffix == "%"
                    else f"{value:,.0f}"
                )

                with col:
                    render_kpi_card(label, formatted_value)

else:
    st.info("No repeat purchase data available.")


# CUSTOMER SEGMENTS

st.divider()
st.header("Customer Segmentation")

if not segments_df.empty:

    segment_col = next(
        (
            col for col in [
                "customer_segment",
                "segment_name",
                "segment"
            ]
            if col in segments_df.columns
        ),
        None
    )

    count_col = next(
        (
            col for col in [
                "customer_count",
                "total_customers",
                "customers"
            ]
            if col in segments_df.columns
        ),
        None
    )

    if segment_col and count_col:

        col1, col2 = st.columns(2)

        with col1:

            fig = px.pie(
                segments_df,
                names=segment_col,
                values=count_col,
                hole=0.45,
                title="Customer Distribution by Segment"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with col2:

            fig = px.bar(
                segments_df.sort_values(
                    count_col,
                    ascending=True
                ),
                x=count_col,
                y=segment_col,
                orientation="h",
                title="Customers per Segment"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    with st.expander("View customer segment data"):

        st.dataframe(
            segments_df,
            use_container_width=True,
            hide_index=True
        )

else:
    st.info("No customer segment data available.")



# MONTHLY CUSTOMER ACQUISITION

st.divider()
st.header("Monthly Customer Acquisition")

if not acquisition_df.empty:

    month_col = next(
        (
            col for col in [
                "month",
                "acquisition_month"
            ]
            if col in acquisition_df.columns
        ),
        None
    )

    count_col = next(
        (
            col for col in [
                "new_customers",
                "customer_count",
                "new_users",
                "total_customers"
            ]
            if col in acquisition_df.columns
        ),
        None
    )

    if month_col and count_col:

        acquisition_df[month_col] = (
            acquisition_df[month_col].astype(str)
        )

        fig = px.bar(
            acquisition_df,
            x=month_col,
            y=count_col,
            title="New Customers per Month",
            labels={
                month_col: "Month",
                count_col: "New Customers"
            }
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with st.expander("View acquisition data"):

        st.dataframe(
            acquisition_df,
            use_container_width=True,
            hide_index=True
        )

else:
    st.info("No customer acquisition data available.")


# COHORT RETENTION

st.divider()
st.header("Customer Cohort Retention")

if not retention_df.empty:

    st.caption(
        "Retention shows the percentage of customers from each acquisition "
        "cohort who made purchases in subsequent calendar months."
    )

    cohort_col = next(
        (
            col for col in [
                "cohort_month",
                "cohort",
                "acquisition_month"
            ]
            if col in retention_df.columns
        ),
        None
    )

    period_col = next(
        (
            col for col in [
                "months_since_first_purchase",
                "cohort_index",
                "month_number"
            ]
            if col in retention_df.columns
        ),
        None
    )

    retention_value_col = next(
        (
            col for col in [
                "retention_rate_pct",
                "retention_rate",
                "retention_pct"
            ]
            if col in retention_df.columns
        ),
        None
    )

    if cohort_col and period_col and retention_value_col:

        pivot_df = retention_df.pivot_table(
            index=cohort_col,
            columns=period_col,
            values=retention_value_col,
            aggfunc="mean"
        )

        pivot_df = pivot_df.sort_index()

        fig = px.imshow(
            pivot_df,
            text_auto=".1f",
            aspect="auto",
            color_continuous_scale="Blues",
            labels={
                "x": "Months Since First Purchase",
                "y": "Cohort",
                "color": "Retention (%)"
            },
            title="Cohort Retention Heatmap"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with st.expander("View cohort retention data"):

        st.dataframe(
            retention_df,
            use_container_width=True,
            hide_index=True
        )

else:
    st.info("No cohort retention data available.")



# CUSTOMER LIFETIME VALUE

st.divider()
st.header("Customer Lifetime Value")

if not clv_df.empty:

    clv_col = next(
        (
            col for col in [
                "customer_lifetime_value",
                "lifetime_value",
                "total_gmv",
                "total_spent"
            ]
            if col in clv_df.columns
        ),
        None
    )

    if clv_col:

        col1, col2 = st.columns(2)

        with col1:

            fig = px.histogram(
                clv_df,
                x=clv_col,
                nbins=30,
                title="Customer Lifetime Value Distribution",
                labels={
                    clv_col: "Lifetime Value (€)"
                }
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with col2:

            top_customers = clv_df.nlargest(
                10,
                clv_col
            )

            name_col = next(
                (
                    col for col in [
                        "username",
                        "customer_id",
                        "buyer_id"
                    ]
                    if col in top_customers.columns
                ),
                None
            )

            if name_col:

                fig = px.bar(
                    top_customers.sort_values(clv_col),
                    x=clv_col,
                    y=name_col,
                    orientation="h",
                    title="Top 10 Customers by Lifetime Value",
                    labels={
                        clv_col: "Lifetime Value (€)",
                        name_col: "Customer"
                    }
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

    with st.expander("View customer lifetime value data"):

        st.dataframe(
            clv_df,
            use_container_width=True,
            hide_index=True
        )

else:
    st.info("No customer lifetime value data available.")


st.divider()

