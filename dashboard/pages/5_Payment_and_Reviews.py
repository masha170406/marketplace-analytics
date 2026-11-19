
import html

import streamlit as st
import plotly.express as px

from analytics.database import read_sql


st.set_page_config(
    page_title="ReWear | Payment and Reviews",
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
    safe_label = html.escape(str(label))
    safe_value = html.escape(str(value))

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{safe_label}</div>
            <div class="kpi-value">{safe_value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.title("Payment and Reviews")
st.caption("Payment reliability, refund activity and marketplace reputation")


@st.cache_data(ttl=300)
def load_payment_performance():
    return read_sql("SELECT * FROM vw_payment_performance")


@st.cache_data(ttl=300)
def load_payment_methods():
    return read_sql("SELECT * FROM vw_payment_method_performance")


@st.cache_data(ttl=300)
def load_monthly_payments():
    return read_sql("""
        SELECT *
        FROM vw_monthly_payment_trends
        ORDER BY month
    """)


@st.cache_data(ttl=300)
def load_payment_attempts():
    return read_sql("SELECT * FROM vw_payment_attempts_per_order")


@st.cache_data(ttl=300)
def load_attempt_distribution():
    return read_sql("SELECT * FROM vw_payment_attempt_distribution")


@st.cache_data(ttl=300)
def load_refunds():
    return read_sql("SELECT * FROM vw_refund_analysis")


@st.cache_data(ttl=300)
def load_reconciliation():
    return read_sql("SELECT * FROM vw_order_payment_reconciliation")


@st.cache_data(ttl=300)
def load_review_metrics():
    return read_sql("SELECT * FROM vw_review_metrics")


@st.cache_data(ttl=300)
def load_rating_distribution():
    return read_sql("SELECT * FROM vw_review_rating_distribution")


@st.cache_data(ttl=300)
def load_seller_reputation():
    return read_sql("SELECT * FROM vw_seller_reputation")


@st.cache_data(ttl=300)
def load_top_rated_sellers():
    return read_sql("""
        SELECT *
        FROM vw_top_rated_sellers
        ORDER BY average_rating DESC
    """)


@st.cache_data(ttl=300)
def load_monthly_reviews():
    return read_sql("""
        SELECT *
        FROM vw_monthly_review_trends
        ORDER BY month
    """)


@st.cache_data(ttl=300)
def load_country_reviews():
    return read_sql("SELECT * FROM vw_review_country_performance")


@st.cache_data(ttl=300)
def load_review_response():
    return read_sql("SELECT * FROM vw_review_response_time")


@st.cache_data(ttl=300)
def load_review_response_summary():
    return read_sql("SELECT * FROM vw_review_response_summary")


try:
    payment_df = load_payment_performance()
    methods_df = load_payment_methods()
    monthly_payment_df = load_monthly_payments()
    attempts_df = load_payment_attempts()
    attempt_distribution_df = load_attempt_distribution()
    refunds_df = load_refunds()
    reconciliation_df = load_reconciliation()

    review_metrics_df = load_review_metrics()
    rating_df = load_rating_distribution()
    reputation_df = load_seller_reputation()
    top_rated_df = load_top_rated_sellers()
    monthly_reviews_df = load_monthly_reviews()
    country_reviews_df = load_country_reviews()
    response_df = load_review_response()
    response_summary_df = load_review_response_summary()

except Exception as error:
    st.error(f"Could not load payment and review analytics: {error}")
    st.stop()



def find_column(df, candidates):
    return next(
        (column for column in candidates if column in df.columns),
        None
    )


def show_table(df):
    if not df.empty:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No data available.")


# PAYMENT OVERVIEW

st.header("Payment Overview")

if not payment_df.empty:
    row = payment_df.iloc[0]

    payment_kpis = [
        (
            "Payment Attempts",
            ["total_payment_attempts"],
            0,
            ""
        ),
        (
            "Successful Payments",
            ["successful_payments"],
            0,
            ""
        ),
        (
            "Failed Payments",
            ["failed_payments"],
            0,
            ""
        ),
        (
            "Payment Success Rate",
            ["payment_success_rate_pct"],
            2,
            "%"
        ),
        (
            "Successful Payment Value",
            ["successful_payment_value"],
            2,
            "€"
        ),
        (
            "Refunded Payment Value",
            ["refunded_payment_value"],
            2,
            "€"
        )
    ]

    for start in range(0, len(payment_kpis), 3):
        cols = st.columns(3)

        for col, (label, candidates, decimals, prefix) in zip(
            cols,
            payment_kpis[start:start + 3]
        ):
            column = find_column(payment_df, candidates)

            if column:
                value = row[column]

                if value is not None:
                    with col:
                        render_kpi_card(
                            label,
                            f"{prefix}{value:,.{decimals}f}"
                            if prefix == "€"
                            else f"{value:,.{decimals}f}{prefix}"
                        )


else:
    st.info("No payment performance data available.")


# PAYMENT METHODS

st.divider()
st.header("Payment Method Performance")

if not methods_df.empty:
    method_col = find_column(
        methods_df,
        ["payment_method"]
    )

    success_col = find_column(
        methods_df,
        ["resolved_payment_success_rate_pct"]
    )

    count_col = find_column(
        methods_df,
        ["total_attempts", "payment_attempts", "total_payment_attempts"]
    )

    col1, col2 = st.columns(2)

    with col1:
        if method_col and success_col:
            fig = px.bar(
                methods_df.sort_values(success_col),
                x=success_col,
                y=method_col,
                orientation="h",
                title="Payment Success Rate by Method",
                labels={
                    success_col: "Success Rate (%)",
                    method_col: "Payment Method"
                }
            )

            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if method_col and count_col:
            fig = px.pie(
                methods_df,
                names=method_col,
                values=count_col,
                hole=0.45,
                title="Payment Attempts by Method"
            )

            st.plotly_chart(fig, use_container_width=True)

    with st.expander("View payment method data"):
        show_table(methods_df)

else:
    st.info("No payment method data available.")


# MONTHLY PAYMENT TRENDS

st.divider()
st.header("Monthly Payment Trends")

if not monthly_payment_df.empty:
    month_col = find_column(monthly_payment_df, ["month"])

    success_col = find_column(
        monthly_payment_df,
        ["successful_payments"]
    )

    failed_col = find_column(
        monthly_payment_df,
        ["failed_payments"]
    )

    if month_col:
        monthly_payment_df[month_col] = (
            monthly_payment_df[month_col].astype(str)
        )

    if month_col and (success_col or failed_col):
        chart_columns = [
            column
            for column in [success_col, failed_col]
            if column
        ]

        chart_df = monthly_payment_df[
            [month_col] + chart_columns
        ].melt(
            id_vars=month_col,
            var_name="Payment Status",
            value_name="Payments"
        )

        fig = px.line(
            chart_df,
            x=month_col,
            y="Payments",
            color="Payment Status",
            markers=True,
            title="Successful and Failed Payments Over Time"
        )

        st.plotly_chart(fig, use_container_width=True)

    with st.expander("View monthly payment data"):
        show_table(monthly_payment_df)

else:
    st.info("No monthly payment data available.")


# PAYMENT ATTEMPTS

st.divider()
st.header("Payment Attempts per Order")

if not attempt_distribution_df.empty:
    attempts_col = find_column(
        attempt_distribution_df,
        ["payment_attempts", "attempt_count", "number_of_attempts"]
    )

    count_col = find_column(
        attempt_distribution_df,
        ["order_count", "total_orders", "count"]
    )

    if attempts_col and count_col:
        fig = px.bar(
            attempt_distribution_df,
            x=attempts_col,
            y=count_col,
            title="Orders by Number of Payment Attempts",
            labels={
                attempts_col: "Payment Attempts",
                count_col: "Number of Orders"
            }
        )

        st.plotly_chart(fig, use_container_width=True)

    with st.expander("View payment attempt distribution"):
        show_table(attempt_distribution_df)

if not attempts_df.empty:
    with st.expander("View payment attempts per order"):
        show_table(attempts_df)


# REFUND ANALYSIS

st.divider()
st.header("Refund Analysis")

if not refunds_df.empty:
    with st.expander("View refund analysis"):
        show_table(refunds_df)

else:
    st.info("No refund analysis data available.")


# PAYMENT RECONCILIATION

st.divider()
st.header("Payment Reconciliation")

if not reconciliation_df.empty:
    with st.expander("View order and payment reconciliation"):
        show_table(reconciliation_df)

else:
    st.info("No reconciliation data available.")


# REVIEW OVERVIEW

st.divider()
st.header("Review Overview")

if not review_metrics_df.empty:
    row = review_metrics_df.iloc[0]

    review_kpis = [
        (
            "Total Reviews",
            ["total_reviews"],
            0,
            ""
        ),
        (
            "Average Rating",
            ["average_rating"],
            2,
            "/5"
        ),
        (
            "Five-Star Reviews",
            ["five_star_reviews"],
            0,
            ""
        ),
        (
            "Positive Review Rate",
            ["positive_review_rate_pct"],
            2,
            "%"
        )
    ]

    cols = st.columns(4)

    for col, (label, candidates, decimals, suffix) in zip(
        cols,
        review_kpis
    ):
        column = find_column(review_metrics_df, candidates)

        if column:
            value = row[column]

            if value is not None:
                with col:
                    render_kpi_card(
                        label,
                        f"{value:,.{decimals}f}{suffix}"
                    )

    with st.expander("View review metrics"):
        show_table(review_metrics_df)

else:
    st.info("No review metrics available.")


# REVIEW RATING DISTRIBUTION

st.divider()
st.header("Review Rating Distribution")

if not rating_df.empty:
    rating_col = find_column(rating_df, ["rating"])

    count_col = find_column(
        rating_df,
        ["review_count", "total_reviews", "count"]
    )

    if rating_col and count_col:
        fig = px.bar(
            rating_df.sort_values(rating_col),
            x=rating_col,
            y=count_col,
            title="Number of Reviews by Rating",
            labels={
                rating_col: "Rating",
                count_col: "Reviews"
            }
        )

        st.plotly_chart(fig, use_container_width=True)

    with st.expander("View rating distribution"):
        show_table(rating_df)

else:
    st.info("No rating distribution data available.")


# SELLER REPUTATION

st.divider()
st.header("Seller Reputation")

if not top_rated_df.empty:
    st.subheader("Top Rated Sellers")

    rating_col = find_column(
        top_rated_df,
        ["average_rating", "avg_rating"]
    )

    name_col = find_column(
        top_rated_df,
        ["username", "seller_username", "seller_id"]
    )

    if rating_col and name_col:
        top_rated_df = top_rated_df.sort_values(
            rating_col,
            ascending=False
        ).head(10)

        fig = px.bar(
            top_rated_df.sort_values(rating_col),
            x=rating_col,
            y=name_col,
            orientation="h",
            title="Top 10 Sellers by Average Rating",
            labels={
                rating_col: "Average Rating",
                name_col: "Seller"
            }
        )

        st.plotly_chart(fig, use_container_width=True)

    with st.expander("View top rated sellers"):
        show_table(top_rated_df)

if not reputation_df.empty:
    with st.expander("View seller reputation data"):
        show_table(reputation_df)


# MONTHLY REVIEW TRENDS

st.divider()
st.header("Monthly Review Trends")

if not monthly_reviews_df.empty:
    month_col = find_column(monthly_reviews_df, ["month"])

    count_col = find_column(
        monthly_reviews_df,
        ["total_reviews", "review_count"]
    )

    rating_col = find_column(
        monthly_reviews_df,
        ["average_rating", "avg_rating"]
    )

    if month_col:
        monthly_reviews_df[month_col] = (
            monthly_reviews_df[month_col].astype(str)
        )

    col1, col2 = st.columns(2)

    with col1:
        if month_col and count_col:
            fig = px.bar(
                monthly_reviews_df,
                x=month_col,
                y=count_col,
                title="Reviews per Month"
            )

            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if month_col and rating_col:
            fig = px.line(
                monthly_reviews_df,
                x=month_col,
                y=rating_col,
                markers=True,
                title="Average Rating per Month"
            )

            st.plotly_chart(fig, use_container_width=True)

    with st.expander("View monthly review data"):
        show_table(monthly_reviews_df)

else:
    st.info("No monthly review data available.")


# COUNTRY REVIEW PERFORMANCE

st.divider()
st.header("Review Performance by Country")

if not country_reviews_df.empty:
    country_col = find_column(country_reviews_df, ["country"])

    rating_col = find_column(
        country_reviews_df,
        ["average_rating", "avg_rating"]
    )

    if country_col and rating_col:
        fig = px.bar(
            country_reviews_df.sort_values(rating_col),
            x=rating_col,
            y=country_col,
            orientation="h",
            title="Average Seller Rating by Country"
        )

        st.plotly_chart(fig, use_container_width=True)

    with st.expander("View country review data"):
        show_table(country_reviews_df)

else:
    st.info("No country review data available.")


# REVIEW RESPONSE ANALYSIS

st.divider()
st.header("Review Response Analysis")

if not response_summary_df.empty:
    with st.expander("View review response summary"):
        show_table(response_summary_df)

if not response_df.empty:
    with st.expander("View review response time data"):
        show_table(response_df)



st.divider()
