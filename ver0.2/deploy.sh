#!/bin/bash

# サーバー情報
SERVER="133.125.84.34"
APP_DIR="/var/www/gtr_scoreboard"
PASSWORD="o4UjZgxlK7pl"
USER="suzukiakiramuki"  # ユーザー名を修正

# ローカル環境の準備
echo "ローカル環境の準備中..."
cat > requirements.txt << EOF
Flask==3.0.2
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
gunicorn==21.2.0
python-dotenv==1.0.1
Werkzeug==3.0.1
SQLAlchemy==2.0.28
WTForms==3.1.2
email-validator==2.1.0.post1
EOF

# サーバーセットアップ
echo "サーバーセットアップ中..."
ssh $USER@$SERVER << EOF
    # システムの更新
    echo "$PASSWORD" | sudo -S apt-get update
    echo "$PASSWORD" | sudo -S apt-get upgrade -y

    # 必要なパッケージのインストール
    echo "$PASSWORD" | sudo -S apt-get install -y python3-pip python3-venv nginx

    # アプリケーションディレクトリの作成
    echo "$PASSWORD" | sudo -S mkdir -p $APP_DIR
    echo "$PASSWORD" | sudo -S chown -R $USER:$USER $APP_DIR

    # Nginxの設定
    echo "$PASSWORD" | sudo -S tee /etc/nginx/sites-available/gtr_scoreboard << 'NGINX'
server {
    listen 80;
    server_name 133.125.84.34;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX

    # Nginxの設定を有効化
    echo "$PASSWORD" | sudo -S ln -sf /etc/nginx/sites-available/gtr_scoreboard /etc/nginx/sites-enabled/
    echo "$PASSWORD" | sudo -S rm -f /etc/nginx/sites-enabled/default
    echo "$PASSWORD" | sudo -S nginx -t
    echo "$PASSWORD" | sudo -S systemctl restart nginx

    # システムdサービスの設定
    echo "$PASSWORD" | sudo -S tee /etc/systemd/system/gtr_scoreboard.service << 'SERVICE'
[Unit]
Description=GTR ScoreBoard Application
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=/var/www/gtr_scoreboard
Environment="PATH=/var/www/gtr_scoreboard/venv/bin"
Environment="FLASK_APP=app.py"
Environment="FLASK_ENV=production"
Environment="FLASK_DEBUG=1"
ExecStart=/var/www/gtr_scoreboard/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 app:app --log-level debug --access-logfile /var/www/gtr_scoreboard/gunicorn-access.log --error-logfile /var/www/gtr_scoreboard/gunicorn-error.log --capture-output --enable-stdio-inheritance
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

    # ファイアウォールの設定
    echo "$PASSWORD" | sudo -S ufw allow 'Nginx Full'
    echo "$PASSWORD" | sudo -S ufw allow ssh
    echo "$PASSWORD" | sudo -S ufw --force enable

    # 仮想環境の作成とパッケージのインストール
    cd $APP_DIR
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
EOF

# アプリケーションファイルをアップロード
echo "アプリケーションファイルをアップロード中..."
ssh $USER@$SERVER "echo '$PASSWORD' | sudo -S rm -rf $APP_DIR/*"
ssh $USER@$SERVER "echo '$PASSWORD' | sudo -S mkdir -p $APP_DIR/templates $APP_DIR/static"

# メインのアプリケーションファイルをアップロード
scp app.py requirements.txt $USER@$SERVER:$APP_DIR/

# テンプレートファイルをアップロード
scp templates/*.html $USER@$SERVER:$APP_DIR/templates/

# 静的ファイルをアップロード
scp static/* $USER@$SERVER:$APP_DIR/static/

# パーミッションの設定
ssh $USER@$SERVER "echo '$PASSWORD' | sudo -S chown -R $USER:$USER $APP_DIR"
ssh $USER@$SERVER "echo '$PASSWORD' | sudo -S chmod -R 755 $APP_DIR"
ssh $USER@$SERVER "echo '$PASSWORD' | sudo -S chmod -R 644 $APP_DIR/templates/* $APP_DIR/static/*"

# 仮想環境の再作成
echo "仮想環境を再作成中..."
ssh $USER@$SERVER << EOF
    cd $APP_DIR
    rm -rf venv
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
EOF

# サービスを再起動
echo "サービスを再起動中..."
ssh $USER@$SERVER "echo '$PASSWORD' | sudo -S systemctl daemon-reload"
ssh $USER@$SERVER "echo '$PASSWORD' | sudo -S systemctl restart gtr_scoreboard"
ssh $USER@$SERVER "echo '$PASSWORD' | sudo -S systemctl restart nginx"

# ログの確認
echo "ログを確認中..."
ssh $USER@$SERVER "echo '$PASSWORD' | sudo -S tail -f /var/www/gtr_scoreboard/gunicorn-error.log"

echo "デプロイ完了！"
echo "アプリケーションにアクセス: http://$SERVER" 