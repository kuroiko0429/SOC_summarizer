import requests
import sqlite3
import datetime
import os
import time
from dotenv import load_dotenv

# ここでも .env を読み込む
load_dotenv()

# --- ⚙️ 設定エリア (環境変数から取得) ---
OBSIDIAN_DIR = "./obsidian_cves" 
DB_PATH = "cve_data.db"

# .envから取得、なければデフォルト値を使う
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
# ---------------------

class CVEHunter:
    def __init__(self):
        self.init_db()
        self.ensure_directories()
        # 起動時に接続先を表示してあげる（確認用）
        print(f"🔗 Ollama Connection: {OLLAMA_API_URL} (Model: {OLLAMA_MODEL})")

    def ensure_directories(self):
        if not os.path.exists(OBSIDIAN_DIR):
            os.makedirs(OBSIDIAN_DIR)

    def init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cves (
                cve_id TEXT PRIMARY KEY,
                description TEXT,
                summary_jp TEXT,
                severity_score REAL,
                severity_level TEXT,
                published_date TEXT,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def save_cve_to_db(self, data):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO cves 
            (cve_id, description, summary_jp, severity_score, severity_level, published_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['id'], data['original_desc'], data['summary_jp'], 
            data['score'], data['severity'], data['published']
        ))
        conn.commit()
        conn.close()

    def fetch_by_id(self, cve_id):
        """指定されたCVE IDの情報をNVDから取得する"""
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        params = {"cveId": cve_id}
        
        print(f"🔍 NVD検索中: {cve_id}")
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return None
            
            data = response.json()
            vulnerabilities = data.get("vulnerabilities", [])
            
            if not vulnerabilities:
                return None
                
            cve_item = vulnerabilities[0]
            cve = cve_item.get("cve", {})
            
            descriptions = cve.get("descriptions", [])
            english_desc = next((d['value'] for d in descriptions if d['lang'] == 'en'), "No description")

            metrics = cve.get("metrics", {})
            cvss_data = {}
            if "cvssMetricV31" in metrics:
                cvss_data = metrics["cvssMetricV31"][0]["cvssData"]
            elif "cvssMetricV30" in metrics:
                cvss_data = metrics["cvssMetricV30"][0]["cvssData"]
            elif "cvssMetricV2" in metrics:
                cvss_data = metrics["cvssMetricV2"][0]["cvssData"]

            return {
                "id": cve.get("id"),
                "original_desc": english_desc,
                "score": cvss_data.get("baseScore", 0.0),
                "severity": cvss_data.get("baseSeverity", "UNKNOWN"),
                "published": cve.get("published", ""),
                "vector": cvss_data.get("vectorString", "")
            }
        except Exception as e:
            print(f"Error: {e}")
            return None

    def analyze_with_ai(self, cve_data):
        """Ollamaで分析"""
        print(f"🤖 AI分析中: {cve_data['id']} (Server: {OLLAMA_API_URL})...")
        prompt = f"""
        あなたはセキュリティエンジニアです。以下のCVEを日本語で解説し、Obsidianで見やすいMarkdown形式で出力してください。

        CVE ID: {cve_data['id']}
        原文: {cve_data['original_desc']}

        出力形式:
        # 概要
        (3行で要約)

        # 影響
        (箇条書きで)

        # 対策
        (具体的なアクション)
        """
        payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
        try:
            # タイムアウトを少し長めに設定（リモート接続は遅れることがあるため）
            response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
            if response.status_code == 200:
                return response.json().get("response", "AI解析失敗")
            return f"AI Error: {response.status_code} - {response.text}"
        except requests.exceptions.ConnectionError:
            return "❌ AI接続エラー: Ollamaサーバーに繋がりません。IPアドレスやポートを確認してください。"
        except Exception as e:
            return f"AI Connection Error: {e}"

    def save_to_obsidian(self, cve_data, summary_jp):
        """ObsidianにMarkdownを保存"""
        filename = f"{cve_data['id']}.md"
        filepath = os.path.join(OBSIDIAN_DIR, filename)
        
        content = f"""---
id: {cve_data['id']}
score: {cve_data['score']}
severity: {cve_data['severity']}
tags:
  - CVE
  - ManualCheck
  - {cve_data['severity']}
date: {datetime.datetime.now().strftime('%Y-%m-%d')}
---

# 🛡️ {cve_data['id']} レポート

## メトリクス
- **Score**: {cve_data['score']} ({cve_data['severity']})
- **Vector**: `{cve_data['vector']}`

## 🤖 AI分析
{summary_jp}

---
## 原文
> {cve_data['original_desc']}
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def process_specific_cve(self, cve_id):
        # 1. NVD検索
        data = self.fetch_by_id(cve_id)
        if not data:
            return {"status": "error", "msg": "NVDに情報がないか、取得に失敗しました。"}

        # 2. AI分析
        summary = self.analyze_with_ai(data)
        data['summary_jp'] = summary

        # 3. DB保存
        self.save_cve_to_db(data)

        # 4. Obsidian保存
        file_path = self.save_to_obsidian(data, summary)

        return {
            "status": "success",
            "data": data,
            "summary": summary,
            "file": file_path
        }