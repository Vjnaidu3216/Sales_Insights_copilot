import unittest
import json
from app import app, init_database

class SalesInsightCopilotTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_database()
        cls.client = app.test_client()

    def test_01_kpis(self):
        res = self.client.get('/api/kpis')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('total_sales', data)
        self.assertIn('total_profit', data)
        self.assertGreater(data['total_sales'], 0)
        print("[OK] KPI Endpoint verified:", data['total_sales'])
    def test_02_charts(self):
        res = self.client.get('/api/charts')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('monthly_trend', data)
        self.assertIn('forecast_timeline', data)
        self.assertIn('region_breakdown', data)
        print("[OK] Charts Endpoint verified:", len(data['monthly_trend']), "historical months")

    def test_03_powerapps_search(self):
        res = self.client.get('/api/powerapps/search?q=Acme')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('customers', data)
        print("[OK] Power Apps Search verified:", len(data['customers']), "customers matched")

    def test_04_copilot_chat(self):
        queries = [
            "What were total sales in June?",
            "Which region had highest profit?",
            "Show forecast for next month",
            "Show low-performing products"
        ]
        for q in queries:
            res = self.client.post('/api/copilot/chat', json={"message": q})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertIn('answer', data)
            print(f"[OK] Copilot query '{q}' -> Response type: {data.get('type')}")

if __name__ == '__main__':
    unittest.main()
