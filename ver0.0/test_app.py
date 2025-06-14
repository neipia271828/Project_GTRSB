import unittest
import os
from sqlalchemy import inspect
from app import app, db, User, GameTitle, CarModel, Track, Record, LapTime

class TestApp(unittest.TestCase):
    def setUp(self):
        """テストの前準備"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        """テストの後処理"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
        if os.path.exists('test.db'):
            os.remove('test.db')

    def test_database_initialization(self):
        """データベースの初期化テスト"""
        with app.app_context():
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            self.assertIn('user', tables)
            self.assertIn('game_title', tables)
            self.assertIn('car_model', tables)
            self.assertIn('track', tables)
            self.assertIn('record', tables)
            self.assertIn('lap_time', tables)

    def test_user_registration(self):
        """ユーザー登録のテスト"""
        response = self.app.post('/api/register', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 201)
        
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.email, 'test@example.com')

    def test_user_registration_duplicate_email(self):
        """重複メールアドレスでのユーザー登録テスト"""
        # 最初のユーザー登録
        self.app.post('/api/register', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # 同じメールアドレスで再度登録
        response = self.app.post('/api/register', json={
            'email': 'test@example.com',
            'password': 'password456'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_user_registration_invalid_email(self):
        """無効なメールアドレスでのユーザー登録テスト"""
        response = self.app.post('/api/register', json={
            'email': 'invalid-email',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_user_registration_short_password(self):
        """短すぎるパスワードでのユーザー登録テスト"""
        response = self.app.post('/api/register', json={
            'email': 'test@example.com',
            'password': '123'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_game_title_creation(self):
        """ゲームタイトル作成のテスト"""
        # まずユーザーを作成
        with app.app_context():
            user = User(email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

            # ゲームタイトルを作成
            game_title = GameTitle(name='Gran Turismo 7', created_by=user.id)
            db.session.add(game_title)
            db.session.commit()

            # 作成されたことを確認
            saved_game_title = GameTitle.query.filter_by(name='Gran Turismo 7').first()
            self.assertIsNotNone(saved_game_title)
            self.assertEqual(saved_game_title.name, 'Gran Turismo 7')

    def test_game_title_creation_duplicate_name(self):
        """重複名でのゲームタイトル作成テスト"""
        # ユーザー登録とログイン（トークン取得）
        self.app.post('/api/register', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        login_res = self.app.post('/api/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        token = login_res.get_json().get('token')
        headers = {'Authorization': f'Bearer {token}'}
        # 最初のゲームタイトル作成
        res1 = self.app.post('/api/game-titles', json={'name': 'Gran Turismo 7'}, headers=headers)
        self.assertEqual(res1.status_code, 201)
        # 同じ名前で再度作成
        res2 = self.app.post('/api/game-titles', json={'name': 'Gran Turismo 7'}, headers=headers)
        self.assertEqual(res2.status_code, 400)
        self.assertIn('error', res2.get_json())

    def test_car_model_creation(self):
        """車種作成のテスト"""
        with app.app_context():
            user = User(email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

            car_model = CarModel(name='Nissan GT-R', created_by=user.id)
            db.session.add(car_model)
            db.session.commit()

            saved_car_model = CarModel.query.filter_by(name='Nissan GT-R').first()
            self.assertIsNotNone(saved_car_model)
            self.assertEqual(saved_car_model.name, 'Nissan GT-R')

    def test_track_creation(self):
        """コース作成のテスト"""
        with app.app_context():
            user = User(email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

            track = Track(name='Suzuka Circuit', lap_count=3, created_by=user.id)
            db.session.add(track)
            db.session.commit()

            saved_track = Track.query.filter_by(name='Suzuka Circuit').first()
            self.assertIsNotNone(saved_track)
            self.assertEqual(saved_track.name, 'Suzuka Circuit')
            self.assertEqual(saved_track.lap_count, 3)

    def test_record_creation(self):
        """記録作成のテスト"""
        with app.app_context():
            # ユーザー作成
            user = User(email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

            # ゲームタイトル作成
            game_title = GameTitle(name='Gran Turismo 7', created_by=user.id)
            db.session.add(game_title)
            db.session.commit()

            # 車種作成
            car_model = CarModel(name='Nissan GT-R', created_by=user.id)
            db.session.add(car_model)
            db.session.commit()

            # コース作成
            track = Track(name='Suzuka Circuit', lap_count=3, created_by=user.id)
            db.session.add(track)
            db.session.commit()

            # 記録作成
            record = Record(
                game_title_id=game_title.id,
                car_model_id=car_model.id,
                track_id=track.id,
                total_time=180.5,
                created_by=user.id
            )
            db.session.add(record)
            db.session.flush()

            # ラップタイム作成
            lap_times = [
                LapTime(record_id=record.id, lap_number=1, time=60.2),
                LapTime(record_id=record.id, lap_number=2, time=59.8),
                LapTime(record_id=record.id, lap_number=3, time=60.5)
            ]
            for lap_time in lap_times:
                db.session.add(lap_time)

            db.session.commit()

            # 作成されたことを確認
            saved_record = Record.query.filter_by(total_time=180.5).first()
            self.assertIsNotNone(saved_record)
            self.assertEqual(saved_record.total_time, 180.5)
            self.assertEqual(len(saved_record.lap_times), 3)

    def test_record_creation_invalid_lap_count(self):
        """無効なラップ数での記録作成テスト"""
        # ユーザー登録とログイン（トークン取得）
        self.app.post('/api/register', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        login_res = self.app.post('/api/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        token = login_res.get_json().get('token')
        headers = {'Authorization': f'Bearer {token}'}
        # ゲームタイトル・車種・コース作成
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            game_title = GameTitle(name='Gran Turismo 7', created_by=user.id)
            db.session.add(game_title)
            car_model = CarModel(name='Nissan GT-R', created_by=user.id)
            db.session.add(car_model)
            track = Track(name='Suzuka Circuit', lap_count=3, created_by=user.id)
            db.session.add(track)
            db.session.commit()
            game_title_id = game_title.id
            car_model_id = car_model.id
            track_id = track.id
        # 記録作成（2ラップしかない）
        record_data = {
            'game_title_id': game_title_id,
            'car_model_id': car_model_id,
            'track_id': track_id,
            'total_time': 120.0,
            'lap_times': [
                {'lap_number': 1, 'time': 60.0},
                {'lap_number': 2, 'time': 60.0}
            ]
        }
        res = self.app.post('/api/records', json=record_data, headers=headers)
        self.assertEqual(res.status_code, 400)
        self.assertIn('error', res.get_json())

if __name__ == '__main__':
    unittest.main() 