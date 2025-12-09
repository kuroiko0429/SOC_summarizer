from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)
DB_PATH = "cve_data.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # カラム名でアクセスできるようにする
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    # 最新順に取得
    cves = conn.execute('SELECT * FROM cves ORDER BY published_date DESC').fetchall()
    conn.close()
    return render_template('index.html', cves=cves)

@app.route('/cve/<cve_id>')
def detail(cve_id):
    conn = get_db_connection()
    cve = conn.execute('SELECT * FROM cves WHERE cve_id = ?', (cve_id,)).fetchone()
    conn.close()
    if cve:
        return render_template('index.html', cve_detail=cve)
    return "Not Found", 404

if __name__ == '__main__':
    # 外部からもアクセスしたければ host='0.0.0.0' にする
    print("🌍 Web UI starting at http://localhost:5000")
    app.run(debug=True, port=5000)