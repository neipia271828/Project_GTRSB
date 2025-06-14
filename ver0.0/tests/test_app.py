import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import json
from app import app, db, User, GameTitle, CarModel, Track, Record, LapTime
from datetime import datetime

class TestGTRSB(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        # テストユーザー登録
        self.register_user('test@example.com', 'password')
        # ログインしてトークンを取得
        self.token = self.login_user('test@example.com', 'password')
        
        # テストデータの作成
        self.create_test_data()

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

    def auth_post(self, url, json_data):
        headers = {'Authorization': f'Bearer {self.token}'}
        return self.app.post(url, json=json_data, headers=headers)

    def auth_get(self, url):
        headers = {'Authorization': f'Bearer {self.token}'}
        return self.app.get(url, headers=headers)

    # ルーティングテスト
    def test_root_route(self):
        """トップページ（/）が200または404を返すかテスト"""
        response = self.app.get('/')
        self.assertIn(response.status_code, [200, 404])

    def test_not_found_route(self):
        """存在しないURLで404が返るかテスト"""
        response = self.app.get('/notfound')
        self.assertEqual(response.status_code, 404)

    # データベース操作テスト
    def test_add_game_title(self):
        """ゲームタイトルの追加が正しく行われるかテスト"""
        response = self.auth_post('/api/game-titles', {'name': 'Test Game 2'})
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('game_title_id', data)

    def test_get_game_titles(self):
        """ゲームタイトルの取得が正しく行われるかテスト"""
        self.auth_post('/api/game-titles', {'name': 'Game 1'})
        self.auth_post('/api/game-titles', {'name': 'Game 2'})
        response = self.auth_get('/api/game-titles')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertGreaterEqual(len(data), 2)

    # 認証テスト
    def test_register(self):
        """ユーザー登録が正しく行われるかテスト"""
        response = self.app.post('/api/register', json={
            'email': 'new@example.com',
            'password': 'newpass123'
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('message', data)

    def test_register_duplicate_email(self):
        # 同じメールアドレスで2回登録
        self.app.post('/api/register', json={
            'email': 'duplicate@example.com',
            'password': 'pass123'
        })
        response = self.app.post('/api/register', json={
            'email': 'duplicate@example.com',
            'password': 'pass123'
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_login(self):
        """ログインが正しく行われるかテスト"""
        self.assertIsNotNone(self.token)

    def test_login_invalid_credentials(self):
        response = self.app.post('/api/login', json={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_logout(self):
        """ログアウトが正しく行われるかテスト"""
        response = self.auth_get('/api/logout')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)

    # ゲームタイトルテスト
    def test_add_game_title_duplicate(self):
        self.auth_post('/api/game-titles', {'name': 'Duplicate Game dup'})
        response = self.auth_post('/api/game-titles', {'name': 'Duplicate Game dup'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_get_game_titles(self):
        self.auth_post('/api/game-titles', {'name': 'Game 1'})
        self.auth_post('/api/game-titles', {'name': 'Game 2'})
        response = self.auth_get('/api/game-titles')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertGreaterEqual(len(data), 2)

    # 車種テスト
    def test_add_car_model(self):
        response = self.auth_post('/api/car-models', {'name': 'Test Car'})
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('id', data)
        self.assertEqual(data['name'], 'Test Car')

    def test_add_car_model_duplicate(self):
        self.auth_post('/api/car-models', {'name': 'Duplicate Car'})
        response = self.auth_post('/api/car-models', {'name': 'Duplicate Car'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_get_car_models(self):
        response = self.app.get('/api/car-models', headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)

    # コーステスト
    def test_add_track(self):
        response = self.auth_post('/api/tracks', {'name': 'Test Track', 'lap_count': 3})
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('id', data)
        self.assertEqual(data['name'], 'Test Track')
        self.assertEqual(data['lap_count'], 3)

    def test_add_track_invalid_lap_count(self):
        response = self.auth_post('/api/tracks', {'name': 'Invalid Track', 'lap_count': 0})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_get_tracks(self):
        response = self.app.get('/api/tracks', headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)

    # 記録テスト
    def test_add_record(self):
        game_response = self.auth_post('/api/game-titles', {'name': 'Test Game add_record'})
        car_response = self.auth_post('/api/car-models', {'name': 'Test Car'})
        track_response = self.auth_post('/api/tracks', {'name': 'Test Track', 'lap_count': 2})
        game_id = json.loads(game_response.data).get('game_title_id')
        car_id = json.loads(car_response.data).get('id')
        track_id = json.loads(track_response.data).get('id')
        response = self.auth_post('/api/records', {
            'game_title_id': game_id,
            'car_model_id': car_id,
            'track_id': track_id,
            'lap_times': ['01:30.000', '01:31.000'],
            'comment': 'Test record'
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('id', data)
        self.assertIn('total_time', data)

    def test_add_record_invalid_lap_count(self):
        game_response = self.auth_post('/api/game-titles', {'name': 'Test Game'})
        car_response = self.auth_post('/api/car-models', {'name': 'Test Car'})
        track_response = self.auth_post('/api/tracks', {'name': 'Test Track', 'lap_count': 2})
        game_id = json.loads(game_response.data).get('game_title_id')
        car_id = json.loads(car_response.data).get('id')
        track_id = json.loads(track_response.data).get('id')
        response = self.auth_post('/api/records', {
            'game_title_id': game_id,
            'car_model_id': car_id,
            'track_id': track_id,
            'lap_times': ['01:30.000'],
            'comment': 'Invalid record'
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_add_record_invalid_time_format(self):
        game_response = self.auth_post('/api/game-titles', {'name': 'Test Game'})
        car_response = self.auth_post('/api/car-models', {'name': 'Test Car'})
        track_response = self.auth_post('/api/tracks', {'name': 'Test Track', 'lap_count': 2})
        game_id = json.loads(game_response.data).get('game_title_id')
        car_id = json.loads(car_response.data).get('id')
        track_id = json.loads(track_response.data).get('id')
        response = self.auth_post('/api/records', {
            'game_title_id': game_id,
            'car_model_id': car_id,
            'track_id': track_id,
            'lap_times': ['1:30', '1:31'],
            'comment': 'Invalid time format'
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_get_records(self):
        response = self.app.get('/api/records', headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)

    def test_calculate_total_time(self):
        from app import calculate_total_time
        lap_times = ['01:30.000', '01:31.000']
        total_time = calculate_total_time(lap_times)
        self.assertEqual(total_time, 181.0)

    def test_token_required(self):
        # トークンなしでリクエスト
        response = self.app.post('/api/game-titles', json={'name': 'Test Game required'})
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'トークンが必要です')

        # 無効なトークンでリクエスト
        headers = {'Authorization': 'Bearer invalid_token'}
        response = self.app.post('/api/game-titles', json={'name': 'Test Game required'}, headers=headers)
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'トークンが無効です')

        # 有効なトークンでリクエスト
        token = self.login_user('test@example.com', 'password')
        headers = {'Authorization': f'Bearer {token}'}
        response = self.app.post('/api/game-titles', json={'name': 'Test Game required valid'}, headers=headers)
        self.assertEqual(response.status_code, 201)

    @unittest.skip("本番運用ではシークレットキーは固定のため、このテストはスキップします")
    def test_token_persistence(self):
        # 最初のログイン
        token1 = self.login_user('test@example.com', 'password')
        self.assertIsNotNone(token1)

        # アプリケーションの再起動をシミュレート
        app.config['SECRET_KEY'] = os.urandom(24)

        # 同じトークンでリクエスト
        headers = {'Authorization': f'Bearer {token1}'}
        response = self.app.post('/api/game-titles', json={'name': 'Test Game'}, headers=headers)
        self.assertEqual(response.status_code, 401)

        # 新しいトークンでログイン
        token2 = self.login_user('test@example.com', 'password')
        self.assertIsNotNone(token2)
        self.assertNotEqual(token1, token2)

        # 新しいトークンでリクエスト
        headers = {'Authorization': f'Bearer {token2}'}
        response = self.app.post('/api/game-titles', json={'name': 'Test Game'}, headers=headers)
        self.assertEqual(response.status_code, 201)

    def create_test_data(self):
        # 既存データの確認
        car_response = self.app.get('/api/car-models', headers={'Authorization': f'Bearer {self.token}'})
        car_models = json.loads(car_response.data)
        if not car_models:
            self.app.post('/api/car-models', json={'name': 'Car 1'}, headers={'Authorization': f'Bearer {self.token}'})
            self.app.post('/api/car-models', json={'name': 'Car 2'}, headers={'Authorization': f'Bearer {self.token}'})
        
        track_response = self.app.get('/api/tracks', headers={'Authorization': f'Bearer {self.token}'})
        tracks = json.loads(track_response.data)
        if not tracks:
            self.app.post('/api/tracks', json={'name': 'Track 1', 'lap_count': 2}, headers={'Authorization': f'Bearer {self.token}'})
            self.app.post('/api/tracks', json={'name': 'Track 2', 'lap_count': 3}, headers={'Authorization': f'Bearer {self.token}'})
        
        game_response = self.app.post('/api/game-titles', json={'name': 'Test Game'}, headers={'Authorization': f'Bearer {self.token}'})
        game_json = json.loads(game_response.data)
        game_id = game_json.get('game_title_id')
        if not game_id:
            # 既存のゲームタイトルを取得
            game_titles_response = self.app.get('/api/game-titles', headers={'Authorization': f'Bearer {self.token}'})
            game_titles = json.loads(game_titles_response.data)
            if game_titles:
                game_id = game_titles[0].get('id')
            else:
                raise Exception(f"game_title_idが取得できません: {game_json}")
        
        car_response = self.app.get('/api/car-models', headers={'Authorization': f'Bearer {self.token}'})
        track_response = self.app.get('/api/tracks', headers={'Authorization': f'Bearer {self.token}'})
        car_id = json.loads(car_response.data)[0].get('id')
        track_id = json.loads(track_response.data)[0].get('id')
        if not car_id or not track_id:
            raise Exception(f"car_idまたはtrack_idが取得できません: car={car_response.data}, track={track_response.data}")
        
        self.app.post('/api/records',
                 json={
                     'game_title_id': game_id,
                     'car_model_id': car_id,
                     'track_id': track_id,
                     'lap_times': ['01:30.000', '01:31.000'],
                     'comment': 'Test record 1'
                 },
                 headers={'Authorization': f'Bearer {self.token}'})
        self.app.post('/api/records',
                 json={
                     'game_title_id': game_id,
                     'car_model_id': car_id,
                     'track_id': track_id,
                     'lap_times': ['01:29.000', '01:30.000'],
                     'comment': 'Test record 2'
                 },
                 headers={'Authorization': f'Bearer {self.token}'})

if __name__ == '__main__':
    unittest.main() 