# CVE Sentinel Bot

CVE Sentinel Botは、新しいCVE（共通脆弱性識別子）情報を取得し、Discordへの通知、データベースへの保存、そしてObsidianと連携可能なMarkdownファイルの生成を行う多機能ツールです。ローカルで動作するAI（Ollama）を活用して、CVEの概要を日本語で自動的に要約・分析します。

また、収集したCVE情報を閲覧するためのWebダッシュボード機能も備えています。

## ✨ 主な機能

- **Discordボット連携**: `!cve <CVE-ID>` コマンドで特定のCVE情報をオンデマンドで取得・分析。
- **AIによる自動分析**: Ollamaを利用して、CVEの技術的な説明を日本語で分かりやすく要約・解説。
- **データベース保存**: 収集したCVE情報をSQLiteデータベースに永続化。
- **Markdownファイル生成**: 分析結果をObsidianで管理しやすいようにMarkdown形式で出力。
- **Webダッシュボード**: Flask製のシンプルなWeb UIで、これまでに収集したCVE情報を一覧・詳細表示。

## 🛠️ セットアップ

### 1. 前提条件

- Python 3.8以上
- [Ollama](https://ollama.com/) がローカル環境で起動していること。
  - `llama3.2` などのモデルがインストールされている必要があります (`ollama run llama3.2`)。

### 2. インストール

```bash
# 1. リポジトリをクローンします
git clone https://github.com/your-username/cve-sentinel-bot.git

# 2. プロジェクトディレクトリに移動します
cd cve-sentinel-bot

# 3. 必要なライブラリをインストールします
pip install -r requirements.txt
```

### 3. 設定

プロジェクトのルートディレクトリに `.env` という名前のファイルを作成し、以下の内容を記述してください。

```dotenv
# Discordボットのトークン
DISCORD_TOKEN="ここにあなたのDiscordボットのトークンを貼り付け"

# (任意) Ollamaの設定 (デフォルトで localhost:11434 を使用します)
# OLLAMA_API_URL="http://<OllamaサーバーのIP>:11434/api/generate"
# OLLAMA_MODEL="gemma:2b" # 使用するモデル名
```

- `DISCORD_TOKEN`: あなたが作成したDiscordボットのトークンを設定します。
- `OLLAMA_API_URL`, `OLLAMA_MODEL`: Ollamaを別サーバーで動かしている場合や、使用するモデルを変更したい場合に設定します。

## 🚀 実行方法

本プロジェクトは、用途に応じて2つのコンポーネントを実行します。

### Discordボットの起動

CVEの分析と通知を行うボットを起動します。

```bash
python bot.py
```

ボットがオンラインになったら、Discordの任意のチャンネルで以下のコマンドを試すことができます。

```
!cve CVE-2021-44228
```

### Webダッシュボードの起動

収集したCVE情報をブラウザで確認したい場合は、以下のコマンドでWebサーバーを起動します。

```bash
python web_dashboard.py
```

起動後、ブラウザで `http://localhost:5000` にアクセスすると、ダッシュボードが表示されます。

## 📂 ディレクトリ構成

```
.
├── bot.py              # Discordボットのメインプログラム
├── cve_hunter.py       # CVE情報の取得・AI分析・DB保存を行うコアロジック
├── web_dashboard.py    # Flask製のWebダッシュボード
├── requirements.txt    # 依存ライブラリ
├── cve_data.db         # CVE情報を保存するSQLiteデータベース
├── obsidian_cves/      # 分析済みのCVEがMarkdown形式で保存されるディレクトリ
└── templates/
    └── index.html      # WebダッシュボードのHTMLテンプレート
```
