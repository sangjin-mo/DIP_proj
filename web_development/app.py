from __future__ import annotations

import math
import os
import random
import secrets
import sqlite3
import time
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    abort,
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "instance" / "monitoring.db"


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-this-key"),
        DATABASE=str(DATABASE),
        SIMULATION_INTERVAL=4,
    )
    if test_config:
        app.config.update(test_config)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    app.teardown_appcontext(close_db)
    register_routes(app)

    with app.app_context():
        init_db()

    return app


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'member')),
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            connected INTEGER NOT NULL DEFAULT 1,
            base_temperature REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id INTEGER NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
            current_temperature REAL NOT NULL,
            max_temperature REAL NOT NULL,
            average_temperature REAL NOT NULL,
            status TEXT NOT NULL,
            captured_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id INTEGER NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
            level TEXT NOT NULL,
            max_temperature REAL NOT NULL,
            message TEXT NOT NULL,
            occurred_at TEXT NOT NULL,
            acknowledged INTEGER NOT NULL DEFAULT 0,
            acknowledged_by INTEGER REFERENCES users(id),
            acknowledged_at TEXT
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )

    now = iso_now()
    db.executemany(
        "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
        [("warning_temperature", "60"), ("danger_temperature", "80")],
    )
    db.executemany(
        """INSERT OR IGNORE INTO users
           (username, password_hash, display_name, role, active, created_at)
           VALUES (?, ?, ?, ?, 1, ?)""",
        [
            ("admin", generate_password_hash("admin1234"), "안전 관리자", "admin", now),
            ("member", generate_password_hash("member1234"), "현장 작업자", "member", now),
        ],
    )
    cameras = [
        ("CAM-01", "로봇팔·모터 열화상", "ROBOT_01", 1, 82.0),
    ]
    db.executemany(
        """INSERT OR IGNORE INTO cameras
           (camera_id, name, location, connected, base_temperature)
           VALUES (?, ?, ?, ?, ?)""",
        cameras,
    )
    # 첫 버전은 열화상 카메라 한 대만 사용한다. 이전 샘플 DB도 자동 정리한다.
    db.execute("DELETE FROM cameras WHERE camera_id <> 'CAM-01'")
    db.execute(
        """UPDATE cameras SET name = '로봇팔·모터 열화상', location = 'ROBOT_01',
                  connected = 1, base_temperature = 82.0 WHERE camera_id = 'CAM-01'"""
    )
    db.commit()

    reading_count = db.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
    if reading_count == 0:
        seed_readings(db)


def seed_readings(db: sqlite3.Connection) -> None:
    warning, danger = get_thresholds(db)
    cameras = db.execute("SELECT * FROM cameras").fetchall()
    start = datetime.now() - timedelta(minutes=29)
    for minute in range(30):
        captured_at = (start + timedelta(minutes=minute)).isoformat(timespec="seconds")
        for camera in cameras:
            wave = math.sin((minute + camera["id"] * 2) / 4) * 4
            maximum = camera["base_temperature"] + wave + random.uniform(-1.5, 1.5)
            average = maximum - random.uniform(8, 15)
            current = average + random.uniform(1, 5)
            status = status_for(maximum, warning, danger)
            db.execute(
                """INSERT INTO readings
                   (camera_id, current_temperature, max_temperature,
                    average_temperature, status, captured_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (camera["id"], current, maximum, average, status, captured_at),
            )
    db.commit()


def get_thresholds(db: sqlite3.Connection | None = None) -> tuple[float, float]:
    db = db or get_db()
    values = dict(db.execute("SELECT key, value FROM settings").fetchall())
    return float(values["warning_temperature"]), float(values["danger_temperature"])


def status_for(maximum: float, warning: float, danger: float) -> str:
    if maximum >= danger:
        return "danger"
    if maximum >= warning:
        return "warning"
    return "normal"


def iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def login_required(view):
    @wraps(view)
    def wrapped(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return view(**kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(**kwargs):
        if g.user["role"] != "admin":
            abort(403)
        return view(**kwargs)

    return wrapped


def validate_csrf() -> None:
    if not secrets.compare_digest(session.get("csrf_token", ""), request.form.get("csrf_token", "")):
        abort(400, "잘못된 요청입니다. 페이지를 새로고침해 주세요.")


def simulate_if_due() -> None:
    db = get_db()
    last = db.execute("SELECT captured_at FROM readings ORDER BY id DESC LIMIT 1").fetchone()
    if last and (datetime.now() - datetime.fromisoformat(last["captured_at"])).total_seconds() < 4:
        return

    warning, danger = get_thresholds(db)
    now = iso_now()
    for camera in db.execute("SELECT * FROM cameras").fetchall():
        phase = time.time() / 20 + camera["id"]
        maximum = camera["base_temperature"] + math.sin(phase) * 6 + random.uniform(-2, 2)
        average = maximum - random.uniform(9, 14)
        current = average + random.uniform(2, 6)
        status = status_for(maximum, warning, danger)
        db.execute(
            """INSERT INTO readings
               (camera_id, current_temperature, max_temperature,
                average_temperature, status, captured_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (camera["id"], current, maximum, average, status, now),
        )

        if status in ("warning", "danger"):
            recent = db.execute(
                """SELECT id FROM alerts WHERE camera_id = ? AND level = ?
                   AND occurred_at >= ? LIMIT 1""",
                (camera["id"], status, (datetime.now() - timedelta(minutes=2)).isoformat(timespec="seconds")),
            ).fetchone()
            if not recent:
                label = "화재 위험" if status == "danger" else "과열 주의"
                db.execute(
                    """INSERT INTO alerts
                       (camera_id, level, max_temperature, message, occurred_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (camera["id"], status, maximum, f"{camera['location']} {label} 감지", now),
                )
    db.execute(
        "DELETE FROM readings WHERE id NOT IN (SELECT id FROM readings ORDER BY id DESC LIMIT 2000)"
    )
    db.commit()


def camera_snapshot(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute(
        """SELECT c.*, r.current_temperature, r.max_temperature,
                  r.average_temperature, r.status, r.captured_at
           FROM cameras c
           JOIN readings r ON r.id = (
               SELECT id FROM readings WHERE camera_id = c.id ORDER BY id DESC LIMIT 1
           )
           ORDER BY c.camera_id"""
    ).fetchall()
    warning, danger = get_thresholds(db)
    cameras = []
    for row in rows:
        camera = dict(row)
        maximum = camera["max_temperature"]
        camera["hotspots"] = [
            {"id": "MOTOR-BASE", "name": "베이스 모터", "x": 79, "y": 69,
             "temperature": round(maximum, 1), "status": status_for(maximum, warning, danger)},
            {"id": "MOTOR-SHOULDER", "name": "어깨 모터", "x": 72, "y": 25,
             "temperature": round(maximum - 3.6, 1), "status": status_for(maximum - 3.6, warning, danger)},
            {"id": "MOTOR-WRIST", "name": "손목 모터", "x": 45, "y": 43,
             "temperature": round(maximum - 11.8, 1), "status": status_for(maximum - 11.8, warning, danger)},
        ]
        cameras.append(camera)
    return cameras


def register_routes(app: Flask) -> None:
    @app.before_request
    def load_user():
        g.user = None
        user_id = session.get("user_id")
        if user_id:
            g.user = get_db().execute(
                "SELECT id, username, display_name, role, active FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if not g.user or not g.user["active"]:
                session.clear()
                return redirect(url_for("login"))
        session.setdefault("csrf_token", secrets.token_hex(16))

    @app.context_processor
    def inject_globals():
        return {"csrf_token": session.get("csrf_token", "")}

    @app.get("/")
    def index():
        return redirect(url_for("dashboard") if g.user else url_for("login"))

    @app.get("/favicon.ico")
    def favicon():
        return "", 204

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.user:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            validate_csrf()
            user = get_db().execute(
                "SELECT * FROM users WHERE username = ?", (request.form.get("username", ""),)
            ).fetchone()
            if user and user["active"] and check_password_hash(user["password_hash"], request.form.get("password", "")):
                session.clear()
                session["user_id"] = user["id"]
                session["csrf_token"] = secrets.token_hex(16)
                return redirect(url_for("dashboard"))
            flash("아이디 또는 비밀번호를 확인해 주세요.", "error")
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        validate_csrf()
        session.clear()
        return redirect(url_for("login"))

    @app.get("/dashboard")
    @login_required
    def dashboard():
        simulate_if_due()
        return render_template("dashboard.html", page="dashboard")

    @app.get("/cameras")
    @login_required
    def cameras():
        simulate_if_due()
        return render_template("cameras.html", page="cameras")

    @app.get("/cameras/<camera_id>")
    @login_required
    def camera_detail(camera_id: str):
        camera = get_db().execute("SELECT * FROM cameras WHERE camera_id = ?", (camera_id,)).fetchone()
        if not camera:
            abort(404)
        return render_template("camera_detail.html", page="cameras", camera=camera)

    @app.get("/alerts")
    @login_required
    def alerts():
        rows = get_db().execute(
            """SELECT a.*, c.camera_id, c.location, u.display_name AS acknowledged_name
               FROM alerts a JOIN cameras c ON c.id = a.camera_id
               LEFT JOIN users u ON u.id = a.acknowledged_by
               ORDER BY a.occurred_at DESC LIMIT 200"""
        ).fetchall()
        return render_template("alerts.html", page="alerts", alerts=rows)

    @app.post("/alerts/<int:alert_id>/acknowledge")
    @admin_required
    def acknowledge_alert(alert_id: int):
        validate_csrf()
        get_db().execute(
            """UPDATE alerts SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = ?
               WHERE id = ?""",
            (g.user["id"], iso_now(), alert_id),
        )
        get_db().commit()
        flash("경고를 확인 처리했습니다.", "success")
        return redirect(url_for("alerts"))

    @app.route("/settings", methods=["GET", "POST"])
    @admin_required
    def settings():
        db = get_db()
        if request.method == "POST":
            validate_csrf()
            try:
                warning = float(request.form["warning_temperature"])
                danger = float(request.form["danger_temperature"])
                if not (0 <= warning < danger <= 300):
                    raise ValueError
            except (ValueError, KeyError):
                flash("주의 온도는 위험 온도보다 낮은 0~300 사이 값이어야 합니다.", "error")
            else:
                db.executemany(
                    "UPDATE settings SET value = ? WHERE key = ?",
                    [(str(warning), "warning_temperature"), (str(danger), "danger_temperature")],
                )
                db.commit()
                flash("임계온도를 저장했습니다.", "success")
        warning, danger = get_thresholds(db)
        return render_template("settings.html", page="settings", warning=warning, danger=danger)

    @app.route("/users", methods=["GET", "POST"])
    @admin_required
    def users():
        db = get_db()
        if request.method == "POST":
            validate_csrf()
            username = request.form.get("username", "").strip()
            display_name = request.form.get("display_name", "").strip()
            password = request.form.get("password", "")
            role = request.form.get("role", "member")
            if len(username) < 3 or not display_name or len(password) < 8 or role not in ("admin", "member"):
                flash("아이디 3자, 비밀번호 8자 이상과 올바른 사용자 정보를 입력해 주세요.", "error")
            else:
                try:
                    db.execute(
                        """INSERT INTO users
                           (username, password_hash, display_name, role, active, created_at)
                           VALUES (?, ?, ?, ?, 1, ?)""",
                        (username, generate_password_hash(password), display_name, role, iso_now()),
                    )
                    db.commit()
                    flash("사용자를 추가했습니다.", "success")
                except sqlite3.IntegrityError:
                    flash("이미 사용 중인 아이디입니다.", "error")
        rows = db.execute(
            "SELECT id, username, display_name, role, active, created_at FROM users ORDER BY id"
        ).fetchall()
        return render_template("users.html", page="users", users=rows)

    @app.post("/users/<int:user_id>/toggle")
    @admin_required
    def toggle_user(user_id: int):
        validate_csrf()
        if user_id == g.user["id"]:
            flash("현재 로그인한 계정은 비활성화할 수 없습니다.", "error")
        else:
            get_db().execute("UPDATE users SET active = 1 - active WHERE id = ?", (user_id,))
            get_db().commit()
            flash("사용자 상태를 변경했습니다.", "success")
        return redirect(url_for("users"))

    @app.get("/api/snapshot")
    @login_required
    def api_snapshot():
        simulate_if_due()
        db = get_db()
        cameras_data = camera_snapshot(db)
        warning, danger = get_thresholds(db)
        counts = {"normal": 0, "warning": 0, "danger": 0}
        for camera in cameras_data:
            counts[camera["status"]] += 1
        alerts_data = [dict(row) for row in db.execute(
            """SELECT a.id, a.level, a.max_temperature, a.message, a.occurred_at,
                      a.acknowledged, c.camera_id, c.location
               FROM alerts a JOIN cameras c ON c.id = a.camera_id
               ORDER BY a.occurred_at DESC LIMIT 8"""
        ).fetchall()]
        trend = [dict(row) for row in db.execute(
            """SELECT captured_at, ROUND(MAX(max_temperature), 1) AS max_temperature,
                      ROUND(AVG(average_temperature), 1) AS average_temperature
               FROM readings GROUP BY captured_at ORDER BY captured_at DESC LIMIT 30"""
        ).fetchall()][::-1]
        return jsonify(
            cameras=cameras_data,
            counts=counts,
            thresholds={"warning": warning, "danger": danger},
            max_temperature=round(max(c["max_temperature"] for c in cameras_data), 1),
            average_temperature=round(sum(c["average_temperature"] for c in cameras_data) / len(cameras_data), 1),
            alerts=alerts_data,
            trend=trend,
            generated_at=iso_now(),
        )

    @app.get("/api/cameras/<camera_id>/history")
    @login_required
    def api_camera_history(camera_id: str):
        camera = get_db().execute("SELECT id FROM cameras WHERE camera_id = ?", (camera_id,)).fetchone()
        if not camera:
            abort(404)
        rows = get_db().execute(
            """SELECT current_temperature, max_temperature, average_temperature,
                      status, captured_at FROM readings WHERE camera_id = ?
               ORDER BY id DESC LIMIT 60""",
            (camera["id"],),
        ).fetchall()
        return jsonify(readings=[dict(row) for row in rows][::-1])

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("error.html", code=403, message="관리자만 접근할 수 있는 페이지입니다."), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="요청한 페이지를 찾을 수 없습니다."), 404


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
