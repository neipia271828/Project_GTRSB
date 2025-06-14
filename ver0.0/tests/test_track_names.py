import unittest
import json
from app import app, db, User, Track
from datetime import datetime

class TestTrackNames(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        
        # テストユーザー登録
        self.register_user('test@example.com', 'password')
        # ログインしてトークンを取得
        self.token = self.login_user('test@example.com', 'password')

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def register_user(self, email, password):
        response = self.app.post('/api/register', json={'email': email, 'password': password})
        return response

    def login_user(self, email, password):
        response = self.app.post('/api/login', json={'email': email, 'password': password})
        return response.json.get('token')

    def test_add_track_name_success(self):
        """正常なコース名登録のテスト"""
        data = {
            'name': 'テストコース_success',
            'lap_count': 3
        }
        response = self.app.post(
            '/api/tracks',
            data=json.dumps(data),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.token}'}
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('id', data)
        self.assertEqual(data['name'], 'テストコース_success')
        self.assertEqual(data['lap_count'], 3)

    def test_add_track_name_missing_name(self):
        """コース名が未指定の場合のテスト"""
        data = {
            'lap_count': 3
        }
        response = self.app.post(
            '/api/tracks',
            data=json.dumps(data),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.token}'}
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_add_track_name_invalid_lap_count(self):
        """無効なラップ数のテスト"""
        data = {
            'name': 'テストコース_invalid',
            'lap_count': 0
        }
        response = self.app.post(
            '/api/tracks',
            data=json.dumps(data),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.token}'}
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_add_track_name_duplicate(self):
        """重複するコース名のテスト"""
        # 最初のコースを登録
        data1 = {
            'name': 'テストコース_duplicate',
            'lap_count': 3
        }
        self.app.post(
            '/api/tracks',
            data=json.dumps(data1),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.token}'}
        )
        
        # 同じ名前で再度登録を試みる
        data2 = {
            'name': 'テストコース_duplicate',
            'lap_count': 3
        }
        response = self.app.post(
            '/api/tracks',
            data=json.dumps(data2),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.token}'}
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main() 