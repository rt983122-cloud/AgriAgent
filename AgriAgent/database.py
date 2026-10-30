"""SQLite database persistence for AgriAgent field management and irrigation history."""
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.environ.get("AGRIAGENT_DB_PATH", os.path.join(os.path.dirname(__file__), "data", "agriagent.db"))


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fields (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    crop TEXT NOT NULL,
                    soil_type TEXT NOT NULL,
                    area REAL NOT NULL,
                    location TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS irrigation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    field_name TEXT,
                    crop TEXT NOT NULL,
                    soil_type TEXT NOT NULL,
                    soil_moisture REAL NOT NULL,
                    target_moisture REAL NOT NULL,
                    temperature REAL NOT NULL,
                    humidity REAL NOT NULL,
                    rainfall REAL NOT NULL DEFAULT 0.0,
                    area REAL NOT NULL,
                    water_mm REAL NOT NULL,
                    water_litres INTEGER NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    action TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)
            
            # Check if seed fields exist; if not, seed realistic starter fields
            cur = conn.execute("SELECT COUNT(*) AS cnt FROM fields")
            if cur.fetchone()["cnt"] == 0:
                now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                demo_fields = [
                    ("North Sector Paddy", "rice", "clayey", 4.5, "Zone A - North"),
                    ("Highland Wheat Basin", "wheat", "loamy", 6.0, "Zone B - Ridge"),
                    ("Sunny Valley Orchard", "tomato", "loamy", 2.2, "Zone C - Greenhouses")
                ]
                conn.executemany(
                    "INSERT INTO fields (name, crop, soil_type, area, location, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    [(name, crop, soil, area, loc, now) for name, crop, soil, area, loc in demo_fields]
                )

            # Check if seed logs exist; if not, add realistic demo history
            cur_logs = conn.execute("SELECT COUNT(*) AS cnt FROM irrigation_logs")
            if cur_logs.fetchone()["cnt"] == 0:
                now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                demo_logs = [
                    ("North Sector Paddy", "Rice", "Clayey", 32.0, 45.0, 31.5, 62.0, 0.0, 4.5, 4.6, 83770, "High", "Irrigation recommended", "Scheduled alternate wetting cycle", now),
                    ("Highland Wheat Basin", "Wheat", "Loamy", 34.0, 35.0, 26.0, 50.0, 5.0, 6.0, 0.0, 0, "Low", "No irrigation needed (Rainfall sufficient)", "Rainfall recorded covers moisture requirement", now),
                    ("Sunny Valley Orchard", "Tomato", "Loamy", 28.0, 38.0, 33.0, 48.0, 0.0, 2.2, 3.8, 33832, "High", "Irrigation recommended", "Drip cycle in progress", now)
                ]
                conn.executemany("""
                    INSERT INTO irrigation_logs 
                    (field_name, crop, soil_type, soil_moisture, target_moisture, temperature, humidity, rainfall, area, water_mm, water_litres, priority, status, action, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, demo_logs)
    finally:
        conn.close()


def get_fields():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM fields ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_field(name, crop, soil_type, area, location="Primary Zone"):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO fields (name, crop, soil_type, area, location, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (name.strip(), crop.lower().strip(), soil_type.lower().strip(), float(area), location.strip(), now)
            )
            new_id = cur.lastrowid
            row = conn.execute("SELECT * FROM fields WHERE id = ?", (new_id,)).fetchone()
            return dict(row)
    finally:
        conn.close()


def delete_field(field_id):
    conn = get_connection()
    try:
        with conn:
            conn.execute("DELETE FROM fields WHERE id = ?", (int(field_id),))
            return True
    finally:
        conn.close()


def log_recommendation(data, field_name=None):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    try:
        with conn:
            conn.execute("""
                INSERT INTO irrigation_logs
                (field_name, crop, soil_type, soil_moisture, target_moisture, temperature, humidity, rainfall, area, water_mm, water_litres, priority, status, action, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                (field_name or "Ad-hoc Field").strip(),
                data.get("crop", "Unknown"),
                data.get("soil_type", "Loamy"),
                float(data.get("soil_moisture", 0)),
                float(data.get("target_moisture", 0)),
                float(data.get("temperature", 0)),
                float(data.get("humidity", 0)),
                float(data.get("rainfall_mm", 0)),
                float(data.get("area_acres", 1)),
                float(data.get("estimated_water_mm", 0)),
                int(data.get("estimated_water_litres", 0)),
                data.get("priority", "Low"),
                data.get("status", ""),
                data.get("action", ""),
                now
            ))
    finally:
        conn.close()


def get_history(limit=50):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM irrigation_logs ORDER BY id DESC LIMIT ?",
            (int(limit),)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_dashboard_stats():
    conn = get_connection()
    try:
        field_count = conn.execute("SELECT COUNT(*) AS cnt, TOTAL(area) AS total_area FROM fields").fetchone()
        log_summary = conn.execute("""
            SELECT 
                COUNT(*) AS total_recommendations,
                TOTAL(water_litres) AS total_water_litres,
                AVG(soil_moisture) AS avg_moisture
            FROM irrigation_logs
        """).fetchone()

        priority_distribution = conn.execute("""
            SELECT priority, COUNT(*) AS count
            FROM irrigation_logs
            GROUP BY priority
        """).fetchall()

        recent_logs = conn.execute(
            "SELECT * FROM irrigation_logs ORDER BY id DESC LIMIT 5"
        ).fetchall()

        crop_stats = conn.execute("""
            SELECT crop, COUNT(*) as count, TOTAL(water_litres) as total_litres
            FROM irrigation_logs
            GROUP BY crop
            ORDER BY count DESC
        """).fetchall()

        return {
            "total_fields": field_count["cnt"],
            "total_area_acres": round(field_count["total_area"], 2),
            "total_recommendations": log_summary["total_recommendations"],
            "total_water_litres": int(log_summary["total_water_litres"]),
            "avg_soil_moisture": round(log_summary["avg_moisture"] or 0, 1),
            "priority_distribution": {r["priority"]: r["count"] for r in priority_distribution},
            "recent_activities": [dict(r) for r in recent_logs],
            "crop_usage": [dict(r) for r in crop_stats]
        }
    finally:
        conn.close()
