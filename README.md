
# ReWear – Marketplace Analytics

ReWear is a data analytics project based on a fictional second-hand marketplace inspired by platforms like Vinted.

A PostgreSQL database was created and populated with synthetic data.

## Project Overview

- PostgreSQL database with 12 related tables.
- 10,000 users, 15,000 listings and 8,000 orders.
- SQL queries and views for marketplace analysis.
- Python scripts for data generation and database integration.
- Streamlit dashboard with interactive charts and KPIs.

## Dashboard

The dashboard is divided into six sections:

1. Marketplace Overview
2. Sales Analysis
3. Customer Analytics
4. Seller Performance
5. Listing Analytics
6. Payment and Reviews

## Technologies

- PostgreSQL and SQL
- Python
- Pandas and NumPy
- SQLAlchemy
- Streamlit
- Plotly
- Faker

## SQL Analysis

SQL was used to analyse:

- Sales, GMV, marketplace revenue and average order value.
- Customer segmentation and repeat purchases.
- Customer cohort retention.
- Seller performance and ratings.
- Listing performance and time-to-sale.
- Payment success rates and refunds.
- Review trends and seller reputation.


## Project Structure

```text
rewear-marketplace/
├── analytics/
├── dashboard/
├── data_generation/
├── database/
├── docs/
├── sql/
├── main.py
└── requirements.txt
```

## Running the Project

1. Clone the repository.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure the PostgreSQL database and `.env` file.
4. Create the database tables.
5. Generate the synthetic data:

```bash
python main.py
```

6. Execute the SQL scripts in the `sql/` folder.
7. Start the dashboard:

```bash
streamlit run dashboard/app.py
```

## Database Design

The database structure and table relationships are shown in the ER diagram.

<img width="1564" height="1488" alt="image" src="https://github.com/user-attachments/assets/57c0e6b9-113e-47e8-920b-b911fc040c89" />

