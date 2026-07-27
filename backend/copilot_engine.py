import sqlite3
import re
import pandas as pd
from forecast_model import train_and_forecast_sales

DB_PATH = "backend/sales.db"

class SalesCopilotEngine:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def _get_db_connection(self):
        return sqlite3.connect(self.db_path)

    def process_query(self, user_query):
        query = user_query.strip().lower()

        # Extract number limit if user specifies (e.g. "top 3 customers", "top 10 customers")
        limit_match = re.search(r'\btop\s+(\d+)\b', query)
        limit = int(limit_match.group(1)) if limit_match else 5
        
        # Check for specific month queries (e.g. "sales in June", "sales in May")
        months = {
            "january": "01", "jan": "01",
            "february": "02", "feb": "02",
            "march": "03", "mar": "03",
            "april": "04", "apr": "04",
            "may": "05",
            "june": "06", "jun": "06",
            "july": "07", "jul": "07",
            "august": "08", "aug": "08",
            "september": "09", "sep": "09", "sept": "09",
            "october": "10", "oct": "10",
            "november": "11", "nov": "11",
            "december": "12", "dec": "12"
        }

        matched_month = None
        for m_name, m_num in months.items():
            if re.search(r'\b' + m_name + r'\b', query):
                matched_month = (m_name.capitalize(), m_num)
                break

        # 1. Month-Specific Sales Query
        if matched_month and ("sales" in query or "revenue" in query or "total" in query):
            return self._get_month_sales_response(matched_month)

        # 2. Top Customers (by Profit or Sales)
        elif "top customer" in query or "best customer" in query or "biggest client" in query or "top 5 customer" in query or "top customers" in query:
            order_by_profit = "profit" in query
            return self._get_top_customers_response(limit=limit, order_by_profit=order_by_profit)

        # 3. Top Products (by Profit or Sales)
        elif "top product" in query or "best selling" in query or "highest selling product" in query or "top products" in query:
            order_by_profit = "profit" in query
            return self._get_top_products_response(limit=limit, order_by_profit=order_by_profit)

        # 4. Total Sales & Overview
        elif "total sales" in query or "overall sales" in query or "how much sales" in query or "total revenue" in query:
            return self._get_total_sales_response()
            
        # 5. Highest Profit Region / Region breakdown
        elif "region" in query or "highest profit" in query or "profit by region" in query:
            return self._get_region_profit_response()
            
        # 6. Forecast next month
        elif "forecast" in query or "next month" in query or "predict" in query:
            return self._get_forecast_response()

        # 7. Low-performing products / AI actions
        elif "low-performing" in query or "low performing" in query or "poor" in query or "decrease" in query or "underperforming" in query:
            return self._get_low_performing_response()

        # 8. Customer search / lookup query
        elif "customer" in query or "client" in query:
            return self._search_customer_response(user_query)

        # Fallback / General NL Query processing via SQL
        else:
            return self._general_ai_response(user_query)

    def _get_month_sales_response(self, month_tuple):
        month_name, month_num = month_tuple
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        sql = "SELECT SUM(Sales), SUM(Profit), COUNT(OrderID) FROM Sales WHERE strftime('%m', OrderDate) = ?"
        cursor.execute(sql, (month_num,))
        sales, profit, count = cursor.fetchone()
        conn.close()

        sales = sales or 0.0
        profit = profit or 0.0
        count = count or 0
        margin = round((profit / sales * 100), 2) if sales > 0 else 0.0

        if count == 0:
            return {
                "answer": f"No transactions recorded for **{month_name}** in the database.",
                "sql_executed": f"SELECT SUM(Sales), SUM(Profit) FROM Sales WHERE strftime('%m', OrderDate) = '{month_num}'",
                "type": "month_summary"
            }

        return {
            "answer": f"### Sales Summary for {month_name}\n- **Total Sales**: **${sales:,.2f}**\n- **Total Profit**: **${profit:,.2f}** ({margin}% Profit Margin)\n- **Orders Processed**: **{count:,}**",
            "sql_executed": f"SELECT SUM(Sales), SUM(Profit), COUNT(OrderID) FROM Sales WHERE strftime('%m', OrderDate) = '{month_num}'",
            "type": "month_summary",
            "data": { "sales": sales, "profit": profit, "orders": count }
        }

    def _get_total_sales_response(self):
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(Sales), SUM(Profit), COUNT(DISTINCT CustomerName), COUNT(OrderID) FROM Sales")
        total_sales, total_profit, customer_count, total_orders = cursor.fetchone()
        conn.close()

        total_sales = total_sales or 0
        total_profit = total_profit or 0
        profit_margin = round((total_profit / total_sales) * 100, 2) if total_sales > 0 else 0

        return {
            "answer": f"**Total Sales**: ${total_sales:,.2f}\n**Total Profit**: ${total_profit:,.2f} ({profit_margin}% Profit Margin)\n**Orders Processed**: {total_orders:,} across {customer_count} active accounts.",
            "sql_executed": "SELECT SUM(Sales), SUM(Profit), COUNT(DISTINCT CustomerName), COUNT(OrderID) FROM Sales",
            "type": "kpi_summary",
            "data": {
                "total_sales": total_sales,
                "total_profit": total_profit,
                "profit_margin": profit_margin,
                "total_orders": total_orders
            }
        }

    def _get_region_profit_response(self):
        conn = self._get_db_connection()
        df = pd.read_sql_query("""
            SELECT Region, 
                   SUM(Sales) as TotalSales, 
                   SUM(Profit) as TotalProfit,
                   ROUND((SUM(Profit) * 100.0 / SUM(Sales)), 2) as MarginPct
            FROM Sales 
            GROUP BY Region 
            ORDER BY TotalProfit DESC
        """, conn)
        conn.close()

        if df.empty:
            return {"answer": "No regional data available.", "sql_executed": "", "type": "text"}

        top_region = df.iloc[0]["Region"]
        top_profit = df.iloc[0]["TotalProfit"]

        table_rows = []
        for idx, row in df.iterrows():
            table_rows.append({
                "Region": row["Region"],
                "Sales": f"${row['TotalSales']:,.2f}",
                "Profit": f"${row['TotalProfit']:,.2f}",
                "Margin": f"{row['MarginPct']}%"
            })

        return {
            "answer": f"**{top_region}** generated the highest profit at **${top_profit:,.2f}**.\n\nHere is the regional performance breakdown:",
            "sql_executed": "SELECT Region, SUM(Sales) as TotalSales, SUM(Profit) as TotalProfit FROM Sales GROUP BY Region ORDER BY TotalProfit DESC",
            "type": "table",
            "table": table_rows
        }

    def _get_forecast_response(self):
        forecast = train_and_forecast_sales(self.db_path)
        next_month = forecast.get("next_month_forecast", 0)
        growth = forecast.get("expected_growth_pct", 0)
        accuracy = forecast.get("forecast_accuracy", 90.0)

        direction = "increase" if growth >= 0 else "decrease"

        return {
            "answer": f"**Forecast for Next Month**: **${next_month:,.2f}**\n\n- Expected MoM change: **{growth:+.2f}%** ({direction})\n- ML Model R² Score: **{forecast.get('r2_score')}**\n- Forecast Model Confidence / Accuracy: **{accuracy}%**\n\n*Model: Scikit-Learn Polynomial Trend Regression fit on monthly CRM aggregations.*",
            "sql_executed": "SELECT strftime('%Y-%m', OrderDate) as Month, SUM(Sales) FROM Sales GROUP BY Month",
            "type": "forecast_insight",
            "data": forecast
        }

    def _get_top_customers_response(self, limit=5, order_by_profit=False):
        conn = self._get_db_connection()
        order_column = "TotalProfit" if order_by_profit else "TotalSales"
        sql = f"""
            SELECT CustomerName, 
                   COUNT(OrderID) as TotalOrders,
                   SUM(Sales) as TotalSales, 
                   SUM(Profit) as TotalProfit,
                   ROUND((SUM(Profit) * 100.0 / SUM(Sales)), 2) as MarginPct
            FROM Sales 
            GROUP BY CustomerName 
            ORDER BY {order_column} DESC 
            LIMIT {limit}
        """
        df = pd.read_sql_query(sql, conn)
        conn.close()

        table_rows = []
        for idx, row in df.iterrows():
            table_rows.append({
                "Rank": f"#{idx+1}",
                "Customer": row["CustomerName"],
                "Orders": int(row["TotalOrders"]),
                "Sales": f"${row['TotalSales']:,.2f}",
                "Profit": f"${row['TotalProfit']:,.2f}",
                "Margin": f"{row['MarginPct']}%"
            })

        metric_name = "Profit" if order_by_profit else "Total Revenue"

        return {
            "answer": f"Here are the **Top {len(df)} Customers** ranked by {metric_name}:",
            "sql_executed": sql.strip(),
            "type": "table",
            "table": table_rows
        }

    def _get_top_products_response(self, limit=5, order_by_profit=False):
        conn = self._get_db_connection()
        order_column = "TotalProfit" if order_by_profit else "TotalSales"
        sql = f"""
            SELECT Product, 
                   SUM(Quantity) as TotalUnits,
                   SUM(Sales) as TotalSales, 
                   SUM(Profit) as TotalProfit,
                   ROUND((SUM(Profit) * 100.0 / SUM(Sales)), 2) as MarginPct
            FROM Sales 
            GROUP BY Product 
            ORDER BY {order_column} DESC 
            LIMIT {limit}
        """
        df = pd.read_sql_query(sql, conn)
        conn.close()

        table_rows = []
        for idx, row in df.iterrows():
            table_rows.append({
                "Rank": f"#{idx+1}",
                "Product": row["Product"],
                "Units Sold": int(row["TotalUnits"]),
                "Sales": f"${row['TotalSales']:,.2f}",
                "Profit": f"${row['TotalProfit']:,.2f}",
                "Margin": f"{row['MarginPct']}%"
            })

        metric_name = "Profit" if order_by_profit else "Revenue"

        return {
            "answer": f"Here are the **Top {len(df)} Products** ranked by {metric_name}:",
            "sql_executed": sql.strip(),
            "type": "table",
            "table": table_rows
        }

    def _get_low_performing_response(self):
        conn = self._get_db_connection()
        df = pd.read_sql_query("""
            SELECT Product, 
                   SUM(Sales) as TotalSales, 
                   SUM(Profit) as TotalProfit,
                   ROUND((SUM(Profit) * 100.0 / SUM(Sales)), 2) as MarginPct
            FROM Sales 
            GROUP BY Product 
            ORDER BY TotalSales ASC 
            LIMIT 3
        """, conn)
        conn.close()

        recommendations = [
            "Increase promotional campaigns & bundle with top-selling Enterprise Cloud Suite.",
            "Offer targeted 10% volume discount for mid-market accounts.",
            "Review pricing strategy & sales rep incentives in underperforming regions."
        ]

        action_items = []
        for idx, row in df.iterrows():
            action_items.append({
                "product": row["Product"],
                "sales": f"${row['TotalSales']:,.2f}",
                "profit": f"${row['TotalProfit']:,.2f}",
                "margin": f"{row['MarginPct']}%",
                "recommendation": recommendations[idx % len(recommendations)]
            })

        return {
            "answer": "### AI Insight & Power Automate Action Trigger\n\nFound **low-performing products** requiring strategic attention:",
            "sql_executed": "SELECT Product, SUM(Sales), SUM(Profit) FROM Sales GROUP BY Product ORDER BY TotalSales ASC LIMIT 3",
            "type": "action_items",
            "action_items": action_items
        }

    def _search_customer_response(self, user_query):
        conn = self._get_db_connection()
        df = pd.read_sql_query("SELECT DISTINCT CustomerName FROM Sales", conn)
        conn.close()

        matched = None
        for cust in df["CustomerName"]:
            if cust.lower() in user_query.lower():
                matched = cust
                break

        if matched:
            conn = self._get_db_connection()
            cdf = pd.read_sql_query(f"""
                SELECT OrderID, Product, Region, Sales, Profit, OrderDate, Salesperson
                FROM Sales
                WHERE CustomerName = '{matched}'
                ORDER BY OrderDate DESC
                LIMIT 5
            """, conn)
            conn.close()

            orders = cdf.to_dict(orient="records")
            total_spent = cdf["Sales"].sum()
            total_profit = cdf["Profit"].sum()

            return {
                "answer": f"**Customer Profile**: **{matched}**\n- Total Spent: **${total_spent:,.2f}**\n- Generated Profit: **${total_profit:,.2f}**\n\nRecent Order History:",
                "sql_executed": f"SELECT * FROM Sales WHERE CustomerName = '{matched}' ORDER BY OrderDate DESC LIMIT 5",
                "type": "customer_detail",
                "customer": matched,
                "total_spent": total_spent,
                "orders": orders
            }
        else:
            return self._get_top_customers_response()

    def _general_ai_response(self, user_query):
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(Sales), SUM(Profit) FROM Sales")
        count, sales, profit = cursor.fetchone()
        conn.close()

        sales = sales or 0.0
        profit = profit or 0.0

        return {
            "answer": f"I processed your request against the Sales SQL Database.\n\nCurrently monitoring **{count:,} transactions** totaling **${sales:,.2f}** in revenue and **${profit:,.2f}** in profit.\n\nTry asking me:\n- *What were total sales in June?*\n- *Which region had highest profit?*\n- *Show forecast for next month*\n- *Top 5 customers by sales*\n- *Top 5 customers by profit*",
            "sql_executed": "SELECT COUNT(*), SUM(Sales), SUM(Profit) FROM Sales",
            "type": "general_info"
        }

if __name__ == "__main__":
    copilot = SalesCopilotEngine()
    print("Test top 5 customers by profit:", copilot.process_query("top 5 customers by profit"))
