
# Marketplace Analytics

Data analytics project based on a fictional second-hand marketplace inspired by platforms like Vinted.

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

## Dashboard Preview

<img width="2523" height="1327" alt="Screenshot From 2026-11-19 17-31-41" src="https://github.com/user-attachments/assets/03c4b19c-2c2a-49ad-88d3-0bf71f1ed416" />
<img width="2523" height="1327" alt="Screenshot From 2026-11-19 17-31-58" src="https://github.com/user-attachments/assets/4551806a-f916-4c71-9ee0-4d1b9ecef34e" />
<img width="2523" height="1327" alt="Screenshot From 2026-11-19 17-32-07" src="https://github.com/user-attachments/assets/c2f15ca1-1bdd-47bd-8da0-21482b4910b4" />

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

