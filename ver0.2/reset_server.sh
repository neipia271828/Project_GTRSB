#!/bin/bash

# サーバー情報
SERVER="133.125.84.34"
APP_DIR="/var/www/gtr_scoreboard"
PASSWORD="o4UjZgxlK7pl"
USER="suzukiakiramuki"

echo "サーバーをリセット中..."

# サービスを停止
ssh ubuntu@$SERVER << EOF
    # サービスを停止
    echo "$PASSWORD" | sudo -S systemctl stop gtr_scoreboard
    echo "$PASSWORD" | sudo -S systemctl stop nginx

    # アプリケーションディレクトリを削除
    echo "$PASSWORD" | sudo -S rm -rf $APP_DIR

    # Nginxの設定を削除
    echo "$PASSWORD" | sudo -S rm -f /etc/nginx/sites-enabled/gtr_scoreboard
    echo "$PASSWORD" | sudo -S rm -f /etc/nginx/sites-available/gtr_scoreboard

    # systemdサービスの設定を削除
    echo "$PASSWORD" | sudo -S rm -f /etc/systemd/system/gtr_scoreboard.service
    echo "$PASSWORD" | sudo -S systemctl daemon-reload

    # ユーザーを削除
    echo "$PASSWORD" | sudo -S deluser --remove-home $USER

    # システムをクリーンアップ
    echo "$PASSWORD" | sudo -S apt-get clean
    echo "$PASSWORD" | sudo -S apt-get autoremove -y

    # Nginxを再起動
    echo "$PASSWORD" | sudo -S systemctl restart nginx
EOF

echo "サーバーのリセットが完了しました。"
echo "setup_server.shを実行して、サーバーを再セットアップしてください。" 