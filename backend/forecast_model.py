import sqlite3
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.metrics import r2_score, mean_absolute_error

DB_PATH = "backend/sales.db"

def train_and_forecast_sales(db_path=DB_PATH, forecast_months=6):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM Sales", conn)
    conn.close()

    if df.empty:
        return {"error": "No sales data found in DB"}

    # Convert OrderDate to datetime
    df["OrderDate"] = pd.to_datetime(df["OrderDate"])
    df["YearMonth"] = df["OrderDate"].dt.to_period("M")

    # Aggregate monthly sales & profit
    monthly = df.groupby("YearMonth").agg(
        TotalSales=("Sales", "sum"),
        TotalProfit=("Profit", "sum"),
        TotalQuantity=("Quantity", "sum"),
        OrderCount=("OrderID", "count")
    ).reset_index()

    monthly["PeriodStr"] = monthly["YearMonth"].astype(str)
    monthly["MonthIdx"] = np.arange(len(monthly))

    X = monthly[["MonthIdx"]].values
    y = monthly["TotalSales"].values

    # Train Polynomial Regression model for capturing non-linear trends
    degree = 2 if len(monthly) >= 6 else 1
    model = make_pipeline(PolynomialFeatures(degree), LinearRegression())
    model.fit(X, y)

    y_pred = model.predict(X)
    r2 = round(float(r2_score(y, y_pred)), 4)
    mae = round(float(mean_absolute_error(y, y_pred)), 2)

    # Forecast future months
    last_month_period = monthly["YearMonth"].iloc[-1]
    future_indices = np.arange(len(monthly), len(monthly) + forecast_months)
    future_preds = model.predict(future_indices.reshape(-1, 1))

    forecast_results = []
    
    # Historical data points
    for idx, row in monthly.iterrows():
        forecast_results.append({
            "period": row["PeriodStr"],
            "actual_sales": round(float(row["TotalSales"]), 2),
            "actual_profit": round(float(row["TotalProfit"]), 2),
            "fitted_sales": round(float(y_pred[idx]), 2),
            "forecast_sales": None,
            "type": "Historical"
        })

    # Future predictions
    for idx_offset, pred in enumerate(future_preds, start=1):
        future_period = (last_month_period + idx_offset).strftime("%Y-%m")
        pred_val = max(round(float(pred), 2), 0.0) # non-negative
        
        # Add bounds (+/- 8% confidence interval estimation)
        lower_bound = round(pred_val * 0.92, 2)
        upper_bound = round(pred_val * 1.08, 2)

        forecast_results.append({
            "period": future_period,
            "actual_sales": None,
            "actual_profit": None,
            "fitted_sales": None,
            "forecast_sales": pred_val,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "type": "Forecast"
        })

    # Metrics calculation
    latest_month_sales = monthly["TotalSales"].iloc[-1]
    next_month_forecast = forecast_results[len(monthly)]["forecast_sales"]
    expected_growth_pct = round(((next_month_forecast - latest_month_sales) / latest_month_sales) * 100, 2)

    summary = {
        "r2_score": r2,
        "mae": mae,
        "forecast_accuracy": round((1.0 - (mae / monthly["TotalSales"].mean())) * 100, 1),
        "latest_actual_sales": round(float(latest_month_sales), 2),
        "next_month_forecast": next_month_forecast,
        "expected_growth_pct": expected_growth_pct,
        "total_historical_months": len(monthly),
        "forecast_months_count": forecast_months,
        "timeline": forecast_results
    }

    return summary

if __name__ == "__main__":
    result = train_and_forecast_sales()
    print("Forecast metrics:", {k: v for k, v in result.items() if k != 'timeline'})
