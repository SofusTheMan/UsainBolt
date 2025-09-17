from flask import Flask, request, render_template, redirect, url_for, send_file
from utils.psql import psql
import psycopg2  # needed for psycopg2.Binary
import io
import os, hashlib, hmac
from pathlib import Path

# naive loader (or use python-dotenv to load .env into os.environ)
def load_env_to_os(path=Path(".env")):
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
load_env_to_os()

ADMIN_SALT = bytes.fromhex(os.getenv("ADMIN_SALT"))
ADMIN_HASH = bytes.fromhex(os.getenv("ADMIN_HASH"))
ADMIN_ITER = int(os.getenv("ADMIN_ITER", "200000"))

def is_admin_password_ok(plain_password: str) -> bool:
    derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), ADMIN_SALT, ADMIN_ITER)
    return hmac.compare_digest(derived, ADMIN_HASH)

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route("/")
def index():
    # total runs
    total_runs = psql("SELECT COUNT(*) FROM runs;")[0][0]
    goal = 100

    return render_template("index.html", total_runs=total_runs, goal=goal)

@app.route("/leaderboard")
def leaderboard():
    rows = psql("""
        SELECT u.user_id, u.username, COUNT(r.run_id) AS runs_count, MIN(r.time_seconds) AS best_time
        FROM users u
        NATURAL JOIN runs r
        GROUP BY u.user_id
        ORDER BY runs_count DESC, best_time ASC;
    """)
    return render_template("leaderboard.html", leaderboard=rows)

@app.route("/history")
def history():
    rows = psql("""
        SELECT u.user_id, u.username, r.run_id, r.time_seconds, r.run_date
        FROM runs r
        NATURAL JOIN users u
        ORDER BY r.run_date DESC;
    """)
    return render_template("history.html", runs=rows)

@app.route("/profile/<int:user_id>")
def profile(user_id):
    user = psql("SELECT username FROM users WHERE user_id = %s;", (user_id,))[0]
    runs = psql("""
        SELECT run_id, time_seconds, run_date
        FROM runs
        WHERE user_id = %s
        ORDER BY run_date DESC;
    """, (user_id,))
    return render_template("profile.html", user=user, runs=runs)

@app.route("/meter/<int:run_id>")
def meter(run_id):
    row = psql("""
        SELECT r.run_id, r.time_seconds, r.run_date, u.username
        FROM runs r
        NATURAL JOIN users u
        WHERE r.run_id = %s;
    """, (run_id,))
    if not row:
        return "Meter not found", 404
    run = row[0]
    return render_template("meter.html", run=run)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        username = request.form.get("username").strip()
        description = request.form.get("description").strip()
        time_seconds = request.form.get("time_seconds")
        file = request.files.get("video")

        if not username or not file or not time_seconds:
            return "Missing fields", 400

        # Check if user exists (case-insensitive)
        user = psql("SELECT user_id FROM users WHERE username_lower = LOWER(%s);", (username,))
        if not user:
            # Ask confirmation to create new user
            # For simplicity: auto-create for now
            psql("INSERT INTO users (username, username_lower) VALUES (%s, LOWER(%s));", (username, username))
            user = psql("SELECT user_id FROM users WHERE username_lower = LOWER(%s);", (username,))

        user_id = user[0]['user_id']

        # Save the video
        video_bytes = file.read()
        psql("INSERT INTO runs (user_id, description, time_seconds, video_data) VALUES (%s, %s, %s, %s);",
             (user_id, description, time_seconds, psycopg2.Binary(video_bytes)), fetch=False)

        return redirect(url_for("index"))

    users = psql("SELECT username FROM users ORDER BY username;")
    return render_template("upload.html", users=users)


@app.route("/video/<int:run_id>")
def video(run_id):
    query = "SELECT video_data FROM runs WHERE run_id = %s;"
    rows = psql(query, (run_id,))
    if rows and rows[0]["video_data"]:
        return send_file(
            io.BytesIO(rows[0]["video_data"]),
            mimetype="video/mp4",
            as_attachment=False,
            download_name=f"run_{run_id}.mp4"
        )
    return "Video not found", 404

if __name__ == "__main__":
    app.run(debug=True, port=5151)
