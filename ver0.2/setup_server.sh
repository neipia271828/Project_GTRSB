#!/bin/bash

# サーバー情報
SERVER="133.125.84.34"
APP_DIR="/var/www/gtr_scoreboard"
PASSWORD="o4UjZgxlK7pl"
USER="suzukiakiramuki"

echo "サーバーセットアップを開始します..."

# ユーザーの作成と設定
ssh ubuntu@$SERVER << EOF
    # ユーザーの作成
    echo "$PASSWORD" | sudo -S adduser --gecos "" --disabled-password $USER
    echo "$PASSWORD" | sudo -S usermod -aG sudo $USER
    echo "$USER:$PASSWORD" | sudo -S chpasswd

    # SSH設定
    echo "$PASSWORD" | sudo -S mkdir -p /home/$USER/.ssh
    echo "$PASSWORD" | sudo -S chmod 700 /home/$USER/.ssh
    echo "$PASSWORD" | sudo -S chown -R $USER:$USER /home/$USER/.ssh

    # 必要なパッケージのインストール
    echo "$PASSWORD" | sudo -S apt-get update
    echo "$PASSWORD" | sudo -S apt-get install -y python3-pip python3-venv nginx

    # アプリケーションディレクトリの作成
    echo "$PASSWORD" | sudo -S mkdir -p $APP_DIR
    echo "$PASSWORD" | sudo -S chown -R $USER:$USER $APP_DIR
EOF

echo "サーバーセットアップが完了しました。"
echo "デプロイスクリプトを実行してください。" 