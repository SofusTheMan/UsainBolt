from flask import Flask, request, render_template, redirect, url_for, send_file, session, flash
from utils.psql import psql
import psycopg2  # needed for psycopg2.Binary
import io
import os, hashlib, hmac
from pathlib import Path
import mimetypes
from functools import wraps

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
    goal = 10

    return render_template("index.html", total_runs=total_runs, goal=goal)


@app.route("/info")
def info():
    return render_template("info.html")


# ---------------------------
# Admin Login / Logout Routes
# ---------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")
        if is_admin_password_ok(password):
            session["admin_logged_in"] = True
            flash("✅ Logged in as admin!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("❌ Wrong password!", "danger")

    return render_template("admin/login.html")

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("🛑 Admin login required", "warning")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    # Only visible to logged-in admin
    users = psql("SELECT * FROM users ORDER BY user_id;")
    runs = psql("SELECT * FROM runs ORDER BY run_id;")
    return render_template("admin/dashboard.html", users=users, runs=runs)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("👋 Logged out!", "info")
    return redirect(url_for("index"))

# -----------------------
# DELETE USER (and runs)
# -----------------------
@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    # delete runs first (foreign key constraint)
    psql("DELETE FROM runs WHERE user_id = %s;", (user_id,), fetch=False)
    # delete user
    psql("DELETE FROM users WHERE user_id = %s;", (user_id,), fetch=False)
    flash(f"🗑️ Deleted user {user_id} and their runs.", "success")
    return redirect(url_for("admin_dashboard"))


# -----------------------
# EDIT USER
# -----------------------
@app.route("/admin/user/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    if request.method == "POST":
        new_username = request.form.get("username").strip()
        profile_picture = request.files.get("profile_picture")
        remove_picture = request.form.get("remove_picture")
        
        if new_username != psql("SELECT username FROM users WHERE user_id = %s;", (user_id,))[0]['username']:
            psql(
                "UPDATE users SET username=%s, username_lower=LOWER(%s) WHERE user_id=%s;",
                (new_username, new_username, user_id),
                fetch=False,
            )
            flash("✅ Username updated.", "success")
        
        # Handle profile picture upload
        if profile_picture and profile_picture.filename:
            picture_bytes = profile_picture.read()
            mimetype = mimetypes.guess_type(profile_picture.filename)[0] or "image/jpeg"
            psql(
                "UPDATE users SET profile_picture=%s, profile_picture_mime=%s WHERE user_id=%s;",
                (psycopg2.Binary(picture_bytes), mimetype, user_id),
                fetch=False
            )
            flash("✅ Profile picture updated.", "success")
        
        # Handle profile picture removal
        if remove_picture == "yes":
            psql(
                "UPDATE users SET profile_picture=NULL, profile_picture_mime=NULL WHERE user_id=%s;",
                (user_id,),
                fetch=False
            )
            flash("🗑️ Profile picture removed.", "success")
        
        return redirect(url_for("admin_dashboard"))
    
    user = psql("SELECT * FROM users WHERE user_id = %s;", (user_id,))
    return render_template("admin/edit_user.html", user=user[0])


# -----------------------
# DELETE RUN
# -----------------------
@app.route("/admin/run/<int:run_id>/delete", methods=["POST"])
@admin_required
def delete_run(run_id):
    psql("DELETE FROM runs WHERE run_id = %s;", (run_id,), fetch=False)
    flash(f"🗑️ Deleted run {run_id}.", "success")
    return redirect(url_for("admin_dashboard"))


# -----------------------
# EDIT RUN
# -----------------------
@app.route("/admin/run/<int:run_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_run(run_id):
    if request.method == "POST":
        # Get the username and check if changing user
        username = request.form.get("username").strip()
        desc = request.form.get("description", "").strip()
        time_s = request.form.get("time_seconds")
        video_file = request.files.get("video")
        
        # Get current run info
        current_run = psql("SELECT user_id FROM runs WHERE run_id = %s;", (run_id,))[0]
        
        # Check if user exists (case-insensitive)
        user = psql("SELECT user_id FROM users WHERE username_lower = LOWER(%s);", (username,))
        
        if not user:
            # Create new user if doesn't exist
            psql("INSERT INTO users (username, username_lower) VALUES (%s, LOWER(%s));", (username, username))
            user = psql("SELECT user_id FROM users WHERE username_lower = LOWER(%s);", (username,))
            flash(f"✨ Created new user: {username}", "info")
        
        user_id = user[0]['user_id']
        
        # Update the run
        cur_desc, cur_time = current_run['description'], current_run['time_seconds']
        if (desc, time_s) != (cur_desc, cur_time) or user_id != current_run['user_id']:
            psql(
                "UPDATE runs SET user_id=%s, description=%s, time_seconds=%s WHERE run_id=%s;",
                (user_id, desc, time_s, run_id),
                fetch=False,
            )
            flash("✅ Run updated.", "success")
        
        # Update video if provided
        if video_file and video_file.filename:
            video_bytes = video_file.read()
            mimetype = mimetypes.guess_type(video_file.filename)[0] or "application/octet-stream"
            psql(
                "UPDATE runs SET video_data=%s, video_mime=%s WHERE run_id=%s;",
                (psycopg2.Binary(video_bytes), mimetype, run_id),
                fetch=False
            )
            flash("🎥 Video updated.", "success")
        
        return redirect(url_for("admin_dashboard"))
    
    run = psql("""
        SELECT r.*, u.username 
        FROM runs r 
        JOIN users u ON r.user_id = u.user_id 
        WHERE r.run_id = %s;
    """, (run_id,))
    
    # Get all usernames for datalist
    users = psql("SELECT username FROM users ORDER BY username;")
    
    return render_template("admin/edit_run.html", run=run[0], users=users)


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
    user = psql("SELECT user_id, username FROM users WHERE user_id = %s;", (user_id,))[0]
    runs = psql("""
        SELECT run_id, time_seconds, run_date
        FROM runs
        WHERE user_id = %s
        ORDER BY run_date DESC;
    """, (user_id,))
    best = min((run['time_seconds'] for run in runs), default=None)
    avg = (sum(run['time_seconds'] for run in runs) / len(runs)) if runs else None
    return render_template("profile.html", user=user, runs=runs, best=best, avg=avg)

# -----------------------
# EDIT PROFILE (for users to upload their own picture)
# -----------------------
@app.route("/profile/<int:user_id>/edit", methods=["GET", "POST"])
def edit_profile(user_id):
    user = psql("SELECT user_id, username FROM users WHERE user_id = %s;", (user_id,))
    if not user:
        return "User not found", 404
    
    if request.method == "POST":
        picture = request.files.get("profile_picture")
        
        if picture and picture.filename:
            # Read and store the picture
            picture_bytes = picture.read()
            mimetype = mimetypes.guess_type(picture.filename)[0] or "image/jpeg"
            
            psql(
                "UPDATE users SET profile_picture=%s, profile_picture_mime=%s WHERE user_id=%s;",
                (psycopg2.Binary(picture_bytes), mimetype, user_id),
                fetch=False
            )
            flash("✅ Profile picture updated!", "success")
        else:
            flash("⚠️ No picture selected", "warning")
        
        return redirect(url_for("profile", user_id=user_id))
    
    return render_template("edit_profile.html", user=user[0])

# -----------------------
# SERVE PROFILE PICTURE
# -----------------------
@app.route("/profile_picture/<int:user_id>")
def profile_picture(user_id):
    query = "SELECT profile_picture, profile_picture_mime FROM users WHERE user_id = %s;"
    rows = psql(query, (user_id,))
    if rows and rows[0]["profile_picture"]:
        return send_file(
            io.BytesIO(rows[0]["profile_picture"]),
            mimetype=rows[0]["profile_picture_mime"] or "image/jpeg",
            as_attachment=False
        )
    # Return a default avatar if no picture exists
    return redirect(url_for("static", filename="default_avatar.png"))

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
        profile_picture = request.files.get("profile_picture")

        if not username or not file or not time_seconds:
            return "Missing fields", 400

        # Check if user exists (case-insensitive)
        user = psql("SELECT user_id FROM users WHERE username_lower = LOWER(%s);", (username,))
        
        if not user:
            # Create new user
            picture_bytes = None
            picture_mime = None
            
            # If profile picture provided for new user, save it
            if profile_picture and profile_picture.filename:
                picture_bytes = profile_picture.read()
                picture_mime = mimetypes.guess_type(profile_picture.filename)[0] or "image/jpeg"
            
            psql(
                "INSERT INTO users (username, username_lower, profile_picture, profile_picture_mime) VALUES (%s, LOWER(%s), %s, %s);",
                (username, username, psycopg2.Binary(picture_bytes) if picture_bytes else None, picture_mime)
            )
            user = psql("SELECT user_id FROM users WHERE username_lower = LOWER(%s);", (username,))

        user_id = user[0]['user_id']

        # Save the video with MIME type
        video_bytes = file.read()
        mimetype = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"

        psql(
            "INSERT INTO runs (user_id, description, time_seconds, video_data, video_mime) VALUES (%s, %s, %s, %s, %s);",
            (user_id, description, time_seconds, psycopg2.Binary(video_bytes), mimetype),
            fetch=False
        )

        return redirect(url_for("index"))

    users = psql("SELECT username FROM users ORDER BY username;")
    return render_template("upload.html", users=users)



@app.route("/video/<int:run_id>")
def video(run_id):
    query = "SELECT video_data, video_mime FROM runs WHERE run_id = %s;"
    rows = psql(query, (run_id,))
    if rows and rows[0]["video_data"]:
        return send_file(
            io.BytesIO(rows[0]["video_data"]),
            mimetype=rows[0]["video_mime"] or "application/octet-stream",
            as_attachment=False,
            download_name=f"run_{run_id}"
        )
    return "Video not found", 404

if __name__ == "__main__":
    app.run(debug=True, port=5151)