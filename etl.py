import pandas as pd
import sqlite3
from datetime import date


#Definitions for data integrity & cleaning
def column_cleaner (columns):
    for column in columns:
        ev_df[column] = ev_df[column].astype(str).str.strip()

def column_int_cleaner (columns):
    for column in columns:
        ev_df[column] = pd.to_numeric(ev_df[column], errors='coerce').astype('Int64')

def column_float_cleaner (columns):
    for column in columns:
        ev_df[column] = pd.to_numeric(ev_df[column], errors='coerce')


#Putting data into a DF
ev_df = pd.read_csv("ev_market_2026.csv")


# Data validation:
print(ev_df.columns)
print(ev_df.info())
print(ev_df.shape)
print(ev_df.dtypes)


#Data cleaning:
ev_df.drop_duplicates(inplace=True)
ev_df.dropna(inplace=True)

column_cleaner(['brand', 'model', 'variant', 'drive_type', 'body_type', 'country_of_origin', 'market_segment'])
column_int_cleaner(['year', 'seating_capacity', 'safety_rating', 'autopilot_level', 'annual_sales_units', 'warranty_years'])
column_float_cleaner(['price_usd', 'battery_capacity_kwh', 'charging_speed_kw', 'range_miles',
                      'acceleration_0_60_mph', 'top_speed_mph', 'horsepower', 'torque_nm', 'cargo_volume_cubic_ft', 'weight_kg',
                      'customer_rating'])

columns = ['brand', 'model', 'variant', 'drive_type', 'body_type', 'country_of_origin', 'market_segment']
for column in columns:
    ev_df[column] = ev_df[column].astype(str).str.title()


#Validating ETL logic
print(ev_df.columns)
print(ev_df.info())
print(ev_df.shape)
print(ev_df.dtypes)


#SQLite connection created
conn = sqlite3.connect("ev_market_2026.db")
ev_df.to_sql("ev_table", conn, if_exists="replace", index=False)

query = """
SELECT *
FROM ev_table
LIMIT 10;
"""

result = pd.read_sql(query, conn)
print(result)

#Brand KPI View
brand_kpi_view = """
CREATE VIEW IF NOT EXISTS brand_kpi AS
SELECT 
    brand,
    SUM(annual_sales_units) as Total_Annual_Units,
    SUM(annual_sales_units * price_usd) as Estimated_Annual_Revenue,
    ROUND(AVG(price_usd), 0) as Average_Brand_Price,
    ROUND(AVG(range_miles), 2) as Average_Miles,
    ROUND(AVG(safety_rating), 2) as Average_Brand_Safety
FROM ev_table
GROUP BY brand
"""

conn.execute("DROP VIEW IF EXISTS brand_kpi;")
conn.execute(brand_kpi_view)

query = """
SELECT *
FROM brand_kpi
LIMIT 10
"""

result = pd.read_sql(query, conn)
print(result)

#Efficiency KPI View
efficiency_kpi_view = """
CREATE VIEW IF NOT EXISTS efficiency_kpi AS
SELECT
    brand,
    body_type,
    ROUND(AVG(range_miles / battery_capacity_kwh), 2) AS range_miles_by_capacity,
    ROUND(AVG(price_usd), 2) AS avg_price_usd
FROM ev_table
GROUP BY brand, body_type;
"""

conn.execute("DROP VIEW IF EXISTS efficiency_kpi;")
conn.execute(efficiency_kpi_view)

query = """
SELECT *
FROM efficiency_kpi
LIMIT 10
"""
result = pd.read_sql(query, conn)
print(result)

#Luxury vs Budget View
luxury_vs_budget = """
CREATE VIEW IF NOT EXISTS luxury_vs_budget AS
SELECT
    market_segment,
    ROUND(AVG(price_usd), 2) AS Average_Price,
    ROUND(AVG(range_miles), 2) AS Average_Mileage,
    ROUND(AVG(customer_rating), 2) AS Average_Customer_Rating,
    ROUND(AVG(horsepower), 2) AS Average_Horsepower,
    ROUND(AVG(charging_speed_kw), 2) AS Average_Charging_Speed_kw,
    SUM(annual_sales_units) AS Total_Units_Sold
FROM ev_table
WHERE market_segment in ('Luxury', 'Budget')
GROUP BY market_segment
"""
conn.execute("DROP VIEW IF EXISTS luxury_vs_budget")
conn.execute(luxury_vs_budget)

query = """
SELECT *
FROM luxury_vs_budget
LIMIT 10
"""

result = pd.read_sql(query, conn)
print(result)

#Body Type View
body_type_sales_performance = """
CREATE VIEW IF NOT EXISTS  body_type_sales_performance AS
SELECT 
    body_type,
    SUM(annual_sales_units) AS Total_Units_Sold,
    SUM(price_usd * annual_sales_units) AS Estimated_Annual_Revenue,
    ROUND(AVG(customer_rating), 2) AS Average_Customer_Rating
FROM ev_table
WHERE body_type in ('Suv', 'Truck', 'Sedan')
GROUP BY body_type
"""
conn.execute("DROP VIEW IF EXISTS body_type_sales_performance")
conn.execute(body_type_sales_performance)

query = """
SELECT *
FROM body_type_sales_performance
LIMIT 10
"""

result = pd.read_sql(query, conn)
print(result)

#Close out Connection
conn.close()