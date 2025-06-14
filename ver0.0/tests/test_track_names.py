import unittest
import json
from app import app, db, User, TrackName
from datetime import datetime

class TestTrackNames(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        
        # テストユーザーの作成
        test_user = User(kamiyama_id_hash='test_hash')
        db.session.add(test_user)
        db.session.commit()
        
        # セッションにユーザーIDを設定
        with self.client.session_transaction() as session:
            session['user_id'] = test_user.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_track_name_success(self):
        """正常なコース名登録のテスト"""
        data = {
            'name': 'テストコース',
            'lap_count': 3
        }
        response = self.client.post(
            '/api/track-names',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('track', data)
        self.assertEqual(data['track']['name'], 'テストコース')
        self.assertEqual(data['track']['lap_count'], 3)

    def test_add_track_name_missing_name(self):
        """コース名が未指定の場合のテスト"""
        data = {
            'lap_count': 3
        }
        response = self.client.post(
            '/api/track-names',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_add_track_name_invalid_lap_count(self):
        """無効なラップ数のテスト"""
        data = {
            'name': 'テストコース',
            'lap_count': 0
        }
        response = self.client.post(
            '/api/track-names',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_add_track_name_duplicate(self):
        """重複するコース名のテスト"""
        # 最初のコースを登録
        data1 = {
            'name': 'テストコース',
            'lap_count': 3
        }
        self.client.post(
            '/api/track-names',
            data=json.dumps(data1),
            content_type='application/json'
        )
        
        # 同じ名前で再度登録を試みる
        data2 = {
            'name': 'テストコース',
            'lap_count': 3
        }
        response = self.client.post(
            '/api/track-names',
            data=json.dumps(data2),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main() 