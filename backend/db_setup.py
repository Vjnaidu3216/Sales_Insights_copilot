import os
import sqlite3
import pandas as pd
from generate_dataset import generate_crm_sales_data

DB_PATH = "backend/sales.db"
CSV_PATH = "backend/sales.csv"

def init_database(csv_path=CSV_PATH, db_path=DB_PATH):
    if not os.path.exists(csv_path):
        print(f"CSV path {csv_path} not found. Generating fresh dataset...")
        generate_crm_sales_data(filepath=csv_path)

    print(f"Reading raw CRM dataset from {csv_path}...")
    df = pd.read_csv(csv_path)

    initial_rows = len(df)
    
    # Step 3 Data Cleaning
    # 1. Drop exact duplicates
    df.drop_duplicates(inplace=True)
    duplicate_rows_removed = initial_rows - len(df)
    
    # 2. Filter out incomplete / draft records (e.g. Sales == 0 or missing order ID)
    df = df[df["Sales"] > 0].copy()
    
    # 3. Fill missing textual fields if any
    df.fillna({"CustomerName": "Unknown Customer", "Product": "General License", "Region": "Unassigned"}, inplace=True)
    
    # 4. Standardize types
    df["OrderID"] = df["OrderID"].astype(int)
    df["Quantity"] = df["Quantity"].astype(int)
    df["Sales"] = df["Sales"].round(2)
    df["Profit"] = df["Profit"].round(2)
    df["OrderDate"] = pd.to_datetime(df["OrderDate"]).dt.strftime("%Y-%m-%d")
    
    print(f"Cleaned dataset: {len(df)} valid records (removed {duplicate_rows_removed} duplicate/invalid entries).")

    # Connect to SQLite DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Step 2: Create SQL Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Sales (
        OrderID INTEGER PRIMARY KEY,
        CustomerName TEXT,
        Product TEXT,
        Region TEXT,
        Sales REAL,
        Profit REAL,
        Quantity INTEGER,
        OrderDate TEXT,
        Salesperson TEXT
    )
    """)
    
    # Replace existing table data
    cursor.execute("DELETE FROM Sales")
    
    # Save cleaned data to SQL database
    df.to_sql("Sales", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()
    
    print(f"Successfully populated SQL table 'Sales' in SQLite DB: {db_path}")
    return len(df)

if __name__ == "__main__":
    init_database()
