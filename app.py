# ============================================================
# Coco's Letter (single file)
# ============================================================

# =========================
# [S1] DESIGN
# =========================
HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>{{ UI.app_title }}</title>
<style>
body{margin:0;background:#1b120f;color:#fff;font-family:sans-serif;}
.card{background:#fff;color:#000;padding:16px;margin:14px;}
textarea{width:100%;min-height:120px;}
button{padding:8px 12px;}
a{color:#2b59c3;}
</style>
</head>
<body>

<h1>{{ UI.app_title }}</h1>
<p>{{ UI.lead }}</p>

<div class="card">
<form method="POST" action="/add">
<textarea name="content" required></textarea>
<button>{{ UI.btn_save }}</button>
</form>
</div>

<div class="card">
<button id="cocoaBtn">ココアを呼ぶ</button>
<p id="cocoaText"></p>
</div>

{% for m in memos %}
<div class="card">
<div style="white-space:pre-wrap;">{{ m[1] }}</div>
<small>{{ m[2] }}</small>
&nbsp;|&nbsp;
<form method="POST" action="/delete/{{ m[0] }}" style="display:inline"><button type="submit">{{ UI.btn_delete }}</button></form>
</div>
{% endfor %}

<script>
const lines=[
"あなた、ちゃんと書いてる？",
"今日は少し静かですね。",
"その一言、大事にして。",
"無理しなくていいんですよ。",
"私は見ています。",
"……ふふ、呼びました？"
];
const b=document.getElementById("cocoaBtn");
const t=document.getElementById("cocoaText");
if(b){b.onclick=()=>t.textContent=lines[Math.floor(Math.random()*lines.length)];}
</script>

</body>
</html>
"""

# =========================
# [S2] OTHER
# =========================
from flask import Flask, render_template_string, request, redirect
import sqlite3
import os
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

# DB file will be created next to this app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("COCOLETTER_DB_PATH", os.path.join(BASE_DIR, "memo.db"))

UI_TEXT = {
    "app_title": "Coco’s Letter",
    "lead": "ここは、あなたの言葉を静かに置ける場所です。",
    "btn_save": "保存する",
    "btn_delete": "消す",
}

@app.context_processor
def inject():
    return dict(UI=UI_TEXT)

SQL_INIT = """
CREATE TABLE IF NOT EXISTS memos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""

def db():
    # check_same_thread=False is safe here because we open/close per request
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def db_init():
    with db() as c:
        c.execute(SQL_INIT)

def db_fetch():
    with db() as c:
        return c.execute(
            "SELECT id, content, created_at FROM memos ORDER BY id DESC"
        ).fetchall()

def db_insert(text: str):
    now = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S")
    with db() as c:
        c.execute(
            "INSERT INTO memos(content, created_at) VALUES(?, ?)",
            (text, now),
        )

def db_delete(mid: int):
    with db() as c:
        c.execute("DELETE FROM memos WHERE id=?", (mid,))

# init table on import
db_init()

# =========================
# [S3] RUN
# =========================
@app.route("/")
def index():
    return render_template_string(HTML, memos=db_fetch())

@app.route("/add", methods=["POST"])
def add():
    text = request.form.get("content", "").strip()
    if text:
        db_insert(text)
    return redirect("/")

@app.route("/delete/<int:mid>", methods=["POST"])
def delete(mid):
    db_delete(mid)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")


