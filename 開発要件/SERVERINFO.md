神山まるごと高専生向けGTRラップタイム記録アプリ - 実装情報（サクラの未来サーバー）
「複雑な仕組みは使わず、より簡単な方法を探し続ける」という方針に基づき、サクラの未来サーバーの設定とアプリのシステム構成を連携させます。

1. サーバーアクセス情報
サクラの未来サーバーにアクセスし、アプリをデプロイするために必要な情報です。

サーバーIPアドレス: 133.125.84.34
このIPアドレスにウェブブラウザからアクセスすることで、アプリに接続できるようになります。
OSユーザー名: ubuntu
OSのrootパスワード: o4UjZgxlK7pl
重要: このパスワードは初期設定です。セキュアな運用のため、早急に変更することを強く推奨します。
変更ルール: 10文字以上、英大文字・英小文字・数字・記号のうち3種類以上を含む。ユーザー名や推測されやすい文字列は避ける。
変更は、SSHでログイン後、sudo passwd root または sudo passwd ubuntu コマンドで行います。
シングルサーバコントロールパネル: https://secure.sakura.ad.jp/cloud/single/
サーバーの起動・停止、ネットワーク設定などの管理が行えます。
アクセストークンについて
アクセストークン (9e55e49c-3032-4adc-8c0b-77304f3a4298) とアクセストークンシークレット (uTBCT1NwFTLGEMtdMX9RRibxQl1OCyVoVV1BrCjJbzsUqhCe0M2OfKErKlspVIWm) は、さくらのクラウドAPIを介してサーバーをプログラマブルに操作するための情報です。今回のアプリ実装では、直接サーバーにアクセスしてデプロイするため、この段階で直接使用することはありません。将来的に自動デプロイやサーバー管理ツールと連携する際に利用を検討できます。

2. アプリケーションデプロイのステップ（推奨）
サクラの未来サーバー (Ubuntu OS) 上にアプリをデプロイするための一般的なステップです。

SSHでのサーバー接続:
ターミナルから以下のコマンドでサーバーに接続します。
Bash

ssh ubuntu@133.125.84.34
パスワードを求められたら、上記 OSのrootパスワード で提供された初期パスワードを入力します。（初回ログイン時に変更を促される場合があります）
必要なソフトウェアのインストール:
Python/Flask を使用する場合:
Bash

sudo apt update
sudo apt install python3 python3-pip
Node.js/Express を使用する場合:
Bash

sudo apt update
sudo apt install nodejs npm
Gitのインストール (任意だが推奨):
開発中のコードをサーバーに簡単にデプロイするためにGitをインストールします。
Bash

sudo apt install git
アプリケーションコードの取得:
Gitリポジトリからコードをクローンします。
Bash

git clone <あなたのGitリポジトリURL> /path/to/your/app
または、SCPなどを使って直接ファイルをアップロードします。
依存関係のインストール:
Pythonの場合:
Bash

cd /path/to/your/app
pip install -r requirements.txt
Node.jsの場合:
Bash

cd /path/to/your/app
npm install
データベースの設定:
SQLite を使用するため、特別なデータベースサーバーの構築は不要です。アプリケーションのコード内でSQLiteデータベースファイル (.db ファイル) を生成し、使用するように設定します。
初期スキーマの適用: アプリケーション起動時にDBスキーマが作成されるようにするか、専用のマイグレーションスクリプトを実行します。
アプリケーションの実行:
開発中は直接実行することもできますが、永続的な運用にはプロセス管理ツール（例: systemd や Supervisor）を使用することを推奨します。
例 (Flaskの場合):
Bash

# 簡易的な起動（開発用）
python3 app.py

# 本番運用の場合、GunicornなどのWSGIサーバーと連携し、systemdなどで管理
pip install gunicorn
gunicorn --bind 0.0.0.0:8000 app:app # ポート8000で起動
ポート開放: デフォルトではHTTP/HTTPSポートは開いていません。サーバーのファイアウォール設定で、アプリが使用するポート（例: 80番や8000番）を開放する必要があります。 これはシングルサーバコントロールパネルまたはufwコマンド (sudo ufw allow 8000) で行います。
Webサーバーの導入 (任意だが推奨):
パフォーマンスやセキュリティ、静的ファイルの配信のために、NginxやApacheなどのWebサーバーをフロントエンドに配置し、アプリケーションサーバーへのリバースプロキシとして利用することを検討します。
例 (Nginxの場合):
Bash

sudo apt install nginx
sudo nano /etc/nginx/sites-available/your_app
# リバースプロキシ設定を記述
sudo ln -s /etc/nginx/sites-available/your_app /etc/nginx/sites-enabled/
sudo systemctl restart nginx
3. パスワード・認証情報まとめ
実装時にコード内に含める、または環境変数として設定する可能性のあるパスワードと認証情報です。

ユーザー四桁パスワード (アプリ内):
ユーザー登録時に入力される4桁の数字。
サーバーサイドで必ずハッシュ化してデータベースに保存すること。
ログイン時には、入力されたパスワードをハッシュ化し、保存されたハッシュ値と比較することで認証を行います。
神山まるごと高専生識別情報 (アプリ内):
登録時に検証するメールアドレスの形式: kmcXXXX@kamiyama.ac.jp
登録時に使用するクイズの質問と正解。これはアプリのサーバーサイドのコード内に直接記述することになります。
例: QUIZ_QUESTION = "神山まるごと高専の校歌のタイトルは？", QUIZ_ANSWER = "未来への航海" (実際は変更してください)
4. その他注意点とサポート
パスワードの管理: サーバーのrootパスワード o4UjZgxlK7pl は非常に重要です。変更後は厳重に管理し、漏洩しないよう細心の注意を払ってください。
トラブルシューティング:
サーバーへの接続問題、アプリの起動問題などが発生した場合は、まずサクラの「みらいサーバー利用者専用チャンネル」(https://kosen-career.slack.com/archives/C07K9BGKQFP) や、提供されたメール (mirai-server@miraistudio.co.jp) にてサポートを求めることができます。
基本的なLinuxコマンドやデプロイに関する知識が役立ちます。
規約遵守: 提供された各種規約 (https://rs.sakura.ad.jp/terms.html, https://miraistudio.notion.site/08d72203244242609a7333378a1dea6b) を必ず確認し、遵守してください。特に、サーバーの乗っ取りに関する警告は重要です。