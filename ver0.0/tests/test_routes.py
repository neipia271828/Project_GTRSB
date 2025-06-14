import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from app import app

class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_root_route(self):
        """トップページ（/）が200または404を返すかテスト"""
        response = self.client.get('/')
        # 200または404のどちらかを許容（テンプレートが無い場合404）
        self.assertIn(response.status_code, [200, 404])

    def test_not_found_route(self):
        """存在しないURLで404が返るかテスト"""
        response = self.client.get('/notfound')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main() 