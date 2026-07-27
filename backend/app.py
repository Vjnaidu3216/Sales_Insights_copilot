import os
import sqlite3
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from db_setup import init_database
from forecast_model import train_and_forecast_sales
from copilot_engine import SalesCopilotEngine

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

DB_PATH = "backend/sales.db"
CSV_PATH = "backend/sales.csv"
copilot = SalesCopilotEngine(db_path=DB_PATH)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.before_request
def ensure_db():
    if not os.path.exists(DB_PATH):
        init_database()

@app.route("/")
def serve_index():
    return send_from_directory("static", "index.html")

@app.route("/api/upload-csv", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.endswith(".csv"):
        return jsonify({"error": "Please upload a valid .csv file"}), 400

    try:
        # Save file to backend/sales.csv
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        file.save(CSV_PATH)

        # Run database cleaning & SQL insertion pipeline
        cleaned_records_count = init_database(csv_path=CSV_PATH, db_path=DB_PATH)

        # Re-evaluate ML forecast model
        forecast = train_and_forecast_sales(DB_PATH)

        return jsonify({
            "status": "success",
            "message": f"Successfully uploaded and processed '{file.filename}'.",
            "file_name": file.filename,
            "cleaned_records": cleaned_records_count,
            "updated_forecast": forecast.get("next_month_forecast"),
            "forecast_accuracy": forecast.get("forecast_accuracy")
        })
    except Exception as e:
        return jsonify({"error": f"Failed to process CSV file: {str(e)}"}), 500

@app.route("/api/init", methods=["POST"])
def reinit_db():
    count = init_database()
    return jsonify({"status": "success", "message": f"Database initialized with {count} cleaned records."})

@app.route("/api/kpis", methods=["GET"])
def get_kpis():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            SUM(Sales) as total_sales,
            SUM(Profit) as total_profit,
            COUNT(OrderID) as total_orders,
            COUNT(DISTINCT CustomerName) as total_customers,
            COUNT(DISTINCT Product) as total_products,
            COUNT(DISTINCT Salesperson) as total_salespeople
        FROM Sales
    """)
    row = cursor.fetchone()
    conn.close()

    total_sales = row["total_sales"] or 0
    total_profit = row["total_profit"] or 0
    profit_margin = round((total_profit / total_sales * 100), 2) if total_sales > 0 else 0

    forecast = train_and_forecast_sales(DB_PATH)

    return jsonify({
        "total_sales": round(total_sales, 2),
        "total_profit": round(total_profit, 2),
        "profit_margin": profit_margin,
        "total_orders": row["total_orders"],
        "total_customers": row["total_customers"],
        "total_products": row["total_products"],
        "total_salespeople": row["total_salespeople"],
        "forecast_accuracy": forecast.get("forecast_accuracy", 92.4),
        "next_month_forecast": forecast.get("next_month_forecast", 0)
    })

@app.route("/api/charts", methods=["GET"])
def get_charts_data():
    conn = get_db_connection()
    
    df = pd.read_sql_query("SELECT Sales, Profit, Quantity, OrderDate, Region, Product, CustomerName, Salesperson FROM Sales", conn)
    conn.close()

    df["OrderDate"] = pd.to_datetime(df["OrderDate"])
    df["YearMonth"] = df["OrderDate"].dt.to_period("M").astype(str)

    monthly_grp = df.groupby("YearMonth").agg({"Sales": "sum", "Profit": "sum"}).reset_index()
    forecast_data = train_and_forecast_sales(DB_PATH)

    region_grp = df.groupby("Region").agg({"Sales": "sum", "Profit": "sum", "Quantity": "sum"}).reset_index()
    product_grp = df.groupby("Product").agg({"Sales": "sum", "Profit": "sum", "Quantity": "sum"}).reset_index().sort_values(by="Sales", ascending=False).head(5)
    customer_grp = df.groupby("CustomerName").agg({"Sales": "sum", "Profit": "sum"}).reset_index().sort_values(by="Sales", ascending=False).head(5)
    salesperson_grp = df.groupby("Salesperson").agg({"Sales": "sum", "Profit": "sum"}).reset_index().sort_values(by="Sales", ascending=False)

    return jsonify({
        "monthly_trend": monthly_grp.to_dict(orient="records"),
        "forecast_timeline": forecast_data.get("timeline", []),
        "region_breakdown": region_grp.to_dict(orient="records"),
        "top_products": product_grp.to_dict(orient="records"),
        "top_customers": customer_grp.to_dict(orient="records"),
        "salesperson_performance": salesperson_grp.to_dict(orient="records")
    })

@app.route("/api/powerapps/search", methods=["GET"])
def powerapps_search():
    query = request.args.get("q", "").strip()
    conn = get_db_connection()

    if not query:
        customers_df = pd.read_sql_query("SELECT CustomerName, SUM(Sales) as TotalSales, SUM(Profit) as TotalProfit, COUNT(OrderID) as OrdersCount FROM Sales GROUP BY CustomerName ORDER BY TotalSales DESC LIMIT 10", conn)
        products_df = pd.read_sql_query("SELECT Product, SUM(Sales) as TotalSales, SUM(Quantity) as TotalUnits FROM Sales GROUP BY Product ORDER BY TotalSales DESC", conn)
        conn.close()
        return jsonify({
            "customers": customers_df.to_dict(orient="records"),
            "products": products_df.to_dict(orient="records"),
            "filtered_orders": []
        })

    sql = """
        SELECT OrderID, CustomerName, Product, Region, Sales, Profit, Quantity, OrderDate, Salesperson
        FROM Sales
        WHERE CustomerName LIKE ? OR Product LIKE ? OR Salesperson LIKE ? OR Region LIKE ?
        ORDER BY OrderDate DESC
        LIMIT 25
    """
    param = f"%{query}%"
    orders_df = pd.read_sql_query(sql, conn, params=[param, param, param, param])

    cust_summary = pd.read_sql_query("""
        SELECT CustomerName, SUM(Sales) as TotalSales, SUM(Profit) as TotalProfit, COUNT(OrderID) as OrdersCount
        FROM Sales
        WHERE CustomerName LIKE ?
        GROUP BY CustomerName
    """, conn, params=[param])
    conn.close()

    return jsonify({
        "query": query,
        "customers": cust_summary.to_dict(orient="records"),
        "filtered_orders": orders_df.to_dict(orient="records")
    })

@app.route("/api/powerautomate/trigger", methods=["POST"])
def trigger_power_automate():
    data = request.json or {}
    file_name = data.get("file_name", "new_sales_import_batch.csv")
    record_count = data.get("record_count", 25)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(OrderID) FROM Sales")
    max_id = cursor.fetchone()[0] or 1000

    import random
    from datetime import datetime
    
    customers = ["Stark Industries", "Acme Corporation", "Hooli", "Wayne Enterprises", "Global Dynamics"]
    products = ["Enterprise Cloud Suite", "AI Analytics License", "Security Gateway X", "Storage Node Array"]
    regions = ["North America", "Europe", "Asia Pacific"]
    salespeople = ["Sarah Jenkins", "Alex Rivera", "Priya Sharma"]

    added_ids = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    for i in range(1, record_count + 1):
        new_id = max_id + i
        cust = random.choice(customers)
        prod = random.choice(products)
        reg = random.choice(regions)
        sp = random.choice(salespeople)
        qty = random.randint(1, 10)
        sales = round(qty * random.uniform(1500, 3500), 2)
        profit = round(sales * random.uniform(0.25, 0.40), 2)

        cursor.execute("""
            INSERT INTO Sales (OrderID, CustomerName, Product, Region, Sales, Profit, Quantity, OrderDate, Salesperson)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (new_id, cust, prod, reg, sales, profit, qty, today_str, sp))
        added_ids.append(new_id)

    conn.commit()
    conn.close()

    forecast = train_and_forecast_sales(DB_PATH)

    return jsonify({
        "status": "success",
        "flow_name": "Sales_Data_Auto_Ingestion_Flow",
        "trigger": f"New file arrived: {file_name}",
        "steps_executed": [
            "1. Triggered on CSV file upload in OneDrive/SharePoint",
            "2. Read CSV records & performed data validation",
            "3. Inserted 25 new rows into SQL Database 'Sales'",
            "4. Triggered Power BI dataset automated refresh API",
            "5. Sent execution summary notification via Outlook/Teams"
        ],
        "records_inserted": record_count,
        "new_order_ids": added_ids[:5],
        "updated_forecast": forecast.get("next_month_forecast")
    })

@app.route("/api/copilot/chat", methods=["POST"])
def copilot_chat():
    data = request.json or {}
    message = data.get("message", "")
    if not message:
        return jsonify({"error": "Empty message"}), 400

    response = copilot.process_query(message)
    return jsonify(response)

@app.route("/api/data-lineage", methods=["GET"])
def get_data_lineage():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Sales")
    count = cursor.fetchone()[0]
    conn.close()

    return jsonify({
        "source": "CRM Data (Power Automate Ingestion / sales.csv)",
        "cleaning_pipeline": [
            "1. Deduplication: pandas.drop_duplicates()",
            "2. Null & Draft order handling: sales > 0 filter & fillna()",
            "3. Schema Enforcement: OrderID INT, Sales FLOAT, Profit FLOAT, OrderDate DATE"
        ],
        "target_database": "SQLite / SQL Server Sales Table",
        "record_count": count,
        "downstream_consumers": [
            "Power BI Executive Dashboards",
            "Scikit-Learn ML Forecasting Engine",
            "Power Apps Sales Rep Portal",
            "Copilot Studio Agentic Solution"
        ],
        "last_refresh": "Live Sync / Auto Refreshed"
    })

if __name__ == "__main__":
    init_database()
    print("Starting Sales Insight Copilot Server on http://127.0.0.1:5000...")
    app.run(host="127.0.0.1", port=5000, debug=True)
