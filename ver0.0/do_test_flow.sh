#!/bin/bash
set -e

# 0. 仮想環境の有効化と依存パッケージのインストール
source venv/bin/activate
pip install -r requirements.txt

# 1. DB・マイグレーション履歴の完全削除
rm -rf migrations instance
find . -name 'gtrsb.db' -delete

# 2. マイグレーション初期化・適用
flask db init
flask db migrate -m "initial migration"
flask db upgrade

# 3. テスト実行
python -m unittest discover tests

# 4. アプリケーション起動
flask run --host=0.0.0.0 --port=8080 