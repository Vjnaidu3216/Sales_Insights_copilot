import os
import csv
import random
from datetime import datetime, timedelta

def generate_crm_sales_data(filepath="backend/sales.csv", num_records=850):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    customers = [
        "Acme Corporation", "Global Dynamics", "Stark Industries", "Cyberdyne Systems",
        "Wayne Enterprises", "Initech", "Umbrella Corp", "Massive Dynamic",
        "Aperture Science", "Hooli", "Pied Piper", "Soylent Corp",
        "Wonka Industries", "Oscorp", "LexCorp", "Tyrell Corp"
    ]
    
    products = [
        {"name": "Enterprise Cloud Suite", "base_price": 4500.0, "margin": 0.35},
        {"name": "AI Analytics License", "base_price": 2800.0, "margin": 0.45},
        {"name": "Security Gateway X", "base_price": 1800.0, "margin": 0.28},
        {"name": "Data Integration Hub", "base_price": 3200.0, "margin": 0.30},
        {"name": "CRM Pro Workstations", "base_price": 1200.0, "margin": 0.20},
        {"name": "Storage Node Array", "base_price": 5500.0, "margin": 0.22},
        {"name": "DevOps Automation Tool", "base_price": 2100.0, "margin": 0.40},
        {"name": "Business Intelligence Server", "base_price": 3900.0, "margin": 0.38}
    ]
    
    regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
    
    salespeople = [
        "Sarah Jenkins", "Alex Rivera", "Michael Chen", 
        "David Miller", "Priya Sharma", "Elena Rostova"
    ]
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 6, 30)
    days_range = (end_date - start_date).days
    
    records = []
    
    # Introduce controlled seasonality and growth trend
    for i in range(1, num_records + 1):
        order_id = 1000 + i
        customer = random.choice(customers)
        prod = random.choice(products)
        region = random.choice(regions)
        salesperson = random.choice(salespeople)
        
        # Random date in range
        random_days = random.randint(0, days_range)
        order_date = start_date + timedelta(days=random_days)
        
        # Seasonality effect (higher sales Q4, lower sales Q1)
        month = order_date.month
        seasonal_multiplier = 1.3 if month in [10, 11, 12] else (0.85 if month in [1, 2] else 1.0)
        growth_factor = 1.0 + ((order_date.year - 2024) * 0.18) # 18% YoY growth
        
        quantity = random.randint(1, 15)
        unit_price = prod["base_price"] * random.uniform(0.9, 1.1)
        sales = round(unit_price * quantity * seasonal_multiplier * growth_factor, 2)
        
        base_profit_margin = prod["margin"] * random.uniform(0.85, 1.15)
        profit = round(sales * base_profit_margin, 2)
        
        records.append({
            "OrderID": order_id,
            "CustomerName": customer,
            "Product": prod["name"],
            "Region": region,
            "Sales": sales,
            "Profit": profit,
            "Quantity": quantity,
            "OrderDate": order_date.strftime("%Y-%m-%d"),
            "Salesperson": salesperson
        })
    
    # Sort records by order date
    records.sort(key=lambda x: x["OrderDate"])
    
    # Add a few intentional duplicate & missing value rows to demonstrate Python cleaning step!
    records.append(records[10].copy())
    records.append({
        "OrderID": 9999,
        "CustomerName": "Draft Order Inc",
        "Product": "Enterprise Cloud Suite",
        "Region": "North America",
        "Sales": 0.0,
        "Profit": 0.0,
        "Quantity": 0,
        "OrderDate": "2026-07-01",
        "Salesperson": "Sarah Jenkins"
    })
    
    fieldnames = ["OrderID", "CustomerName", "Product", "Region", "Sales", "Profit", "Quantity", "OrderDate", "Salesperson"]
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
        
    print(f"Generated {len(records)} sales records in {filepath}")

if __name__ == "__main__":
    generate_crm_sales_data()
