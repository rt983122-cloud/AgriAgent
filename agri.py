"""AgriAgent Flask Web Application.

Provides a modern dashboard, deterministic irrigation planner, crop advisory,
field management, analytics, and an AI Farm Assistant powered by the existing
ReAct agent architecture.
"""
import os
import time
from collections import defaultdict
from flask import Flask, render_template, request, jsonify

import config
import database
from main import run_agent
from tools.irrigation import build_irrigation_recommendation, CROP_PROFILES, CROP_THRESHOLDS, SOIL_FACTOR

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1MB max payload

# In-memory rate limiting for AI endpoint (per-IP sliding window)
AI_RATE_LIMIT = 20  # requests per minute
_request_records = defaultdict(list)


def is_rate_limited(ip_address: str) -> bool:
    now = time.time()
    cutoff = now - 60.0
    history = _request_records[ip_address]
    _request_records[ip_address] = [t for t in history if t > cutoff]
    if len(_request_records[ip_address]) >= AI_RATE_LIMIT:
        return True
    _request_records[ip_address].append(now)
    return False


def get_active_provider() -> str:
    if os.environ.get("GEMINI_API_KEY"):
        return "Gemini (" + config.GEMINI_MODEL + ")"
    if os.environ.get("GROQ_API_KEY"):
        return "Groq (" + config.GROQ_MODEL + ")"
    return "None (Set GEMINI_API_KEY or GROQ_API_KEY in .env)"


# Initialize database tables on application import
try:
    database.init_db()
except Exception as e:
    app.logger.warning(f"Database initialization warning: {e}")


@app.get("/")
def home():
    """Render the main AgriAgent dashboard application."""
    return render_template("index.html")


@app.get("/api/health")
def health():
    """Health check endpoint for Render, monitoring, and hackathon evaluation."""
    provider = "gemini" if os.environ.get("GEMINI_API_KEY") else ("groq" if os.environ.get("GROQ_API_KEY") else "none")
    return jsonify({
        "ok": True,
        "service": "AgriAgent",
        "status": "healthy",
        "ai_provider": provider,
        "database": "sqlite_ready",
        "version": "1.0.0"
    })


@app.get("/api/status")
def system_status():
    """System diagnostic information for settings and status widgets."""
    has_gemini = bool(os.environ.get("GEMINI_API_KEY"))
    has_groq = bool(os.environ.get("GROQ_API_KEY"))
    has_weather_api = bool(os.environ.get("OPENWEATHER_API_KEY"))

    return jsonify({
        "ai_configured": has_gemini or has_groq,
        "ai_provider": get_active_provider(),
        "weather_service": "Connected (OpenWeather)" if has_weather_api else "Manual / Demo Mode (No API key)",
        "weather_configured": has_weather_api,
        "supported_crops_count": len(CROP_PROFILES),
        "supported_crops": list(CROP_PROFILES.keys()),
        "environment": "Production" if os.environ.get("RENDER") else "Development",
        "database": "Persistent SQLite (data/agriagent.db)"
    })


@app.get("/api/stats")
def stats():
    """Aggregate dashboard metrics and recent activity."""
    try:
        data = database.get_dashboard_stats()
        return jsonify(data)
    except Exception as exc:
        return jsonify({"error": f"Failed to retrieve stats: {str(exc)}"}), 500


@app.get("/api/crops")
def get_crops():
    """Return agronomic profiles for all supported crops."""
    return jsonify({
        "crops": CROP_PROFILES,
        "soil_types": list(SOIL_FACTOR.keys())
    })


@app.post("/api/recommend")
def recommend():
    """Calculate deterministic irrigation recommendation and log entry."""
    payload = request.get_json(silent=True) or {}
    
    try:
        crop = str(payload.get("crop", "rice")).strip().lower()
        soil_type = str(payload.get("soil_type", "loamy")).strip().lower()
        
        if crop not in CROP_THRESHOLDS:
            return jsonify({"error": f"Invalid crop '{crop}'. Choose: {', '.join(CROP_THRESHOLDS.keys())}"}), 400
        if soil_type not in SOIL_FACTOR:
            return jsonify({"error": f"Invalid soil type '{soil_type}'. Choose: {', '.join(SOIL_FACTOR.keys())}"}), 400

        try:
            soil_moisture = float(payload.get("soil_moisture", 35))
            temperature = float(payload.get("temperature", 32))
            humidity = float(payload.get("humidity", 55))
            area = float(payload.get("area", 1))
            rainfall = float(payload.get("rainfall", 0) or 0)
        except (ValueError, TypeError):
            return jsonify({"error": "Numerical fields must be valid numbers."}), 400

        field_name = str(payload.get("field_name", "Ad-hoc Field")).strip() or "Ad-hoc Field"

        result = build_irrigation_recommendation(
            crop=crop,
            soil_moisture=soil_moisture,
            temperature=temperature,
            humidity=humidity,
            area=area,
            soil_type=soil_type,
            rainfall=rainfall
        )

        try:
            database.log_recommendation(result, field_name=field_name)
        except Exception as db_err:
            app.logger.warning(f"Could not persist irrigation log: {db_err}")

        return jsonify(result)

    except ValueError as exc:
        return jsonify({"error": f"Validation error: {exc}"}), 400
    except Exception as exc:
        return jsonify({"error": f"Calculation error: {type(exc).__name__}: {exc}"}), 500


@app.post("/api/ask")
def ask_agent():
    """AI Assistant endpoint connected directly to the existing ReAct agent."""
    ip = request.remote_addr or "127.0.0.1"
    if is_rate_limited(ip):
        return jsonify({"error": "Rate limit exceeded. Please wait a minute before sending another query."}), 429

    payload = request.get_json(silent=True) or {}
    query = str(payload.get("query", "")).strip()
    
    if not query:
        return jsonify({"error": "Please provide a question or instruction for AgriAgent."}), 400
    if len(query) > 1000:
        return jsonify({"error": "Query exceeds maximum allowed length of 1000 characters."}), 400

    explicit_dry_run = bool(payload.get("dry_run", False)) or bool(os.environ.get("AGENTX_DRY_RUN"))
    has_key = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY"))

    if not has_key and not explicit_dry_run:
        return jsonify({
            "answer": (
                "No LLM API key was detected on the server. To enable live reasoning with Google Gemini or Groq, "
                "add GEMINI_API_KEY or GROQ_API_KEY to your environment variables (.env file). "
                "You can also check the 'Dry Run Mode' option to test the ReAct tool-execution pipeline with simulated responses."
            ),
            "trace": [],
            "configured": False,
            "suggestion": "Set GEMINI_API_KEY or GROQ_API_KEY in your environment, or toggle Dry Run mode."
        }), 200

    try:
        answer, trace = run_agent(query, dry_run=explicit_dry_run, verbose=False)
        return jsonify({
            "answer": answer,
            "trace": trace,
            "configured": True,
            "dry_run": explicit_dry_run
        })
    except RuntimeError as r_err:
        return jsonify({
            "answer": f"Configuration issue: {r_err}",
            "trace": [],
            "configured": False
        }), 200
    except Exception as exc:
        return jsonify({
            "error": f"Agent reasoning error: {type(exc).__name__}: {str(exc)}"
        }), 500


@app.get("/api/fields")
def list_fields():
    try:
        fields = database.get_fields()
        return jsonify({"fields": fields})
    except Exception as exc:
        return jsonify({"error": f"Failed to retrieve fields: {exc}"}), 500


@app.post("/api/fields")
def create_field():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    crop = str(payload.get("crop", "")).strip().lower()
    soil_type = str(payload.get("soil_type", "")).strip().lower()
    location = str(payload.get("location", "Primary Zone")).strip() or "Primary Zone"

    if not name:
        return jsonify({"error": "Field name is required."}), 400
    if crop not in CROP_THRESHOLDS:
        return jsonify({"error": f"Invalid crop. Choose from: {', '.join(CROP_THRESHOLDS.keys())}"}), 400
    if soil_type not in SOIL_FACTOR:
        return jsonify({"error": f"Invalid soil type. Choose from: {', '.join(SOIL_FACTOR.keys())}"}), 400

    try:
        area = float(payload.get("area", 1.0))
        if area <= 0 or area > 10000:
            return jsonify({"error": "Area must be between 0.01 and 10,000 acres."}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Area must be a valid number."}), 400

    try:
        new_field = database.add_field(name, crop, soil_type, area, location)
        return jsonify({"ok": True, "field": new_field}), 201
    except Exception as exc:
        return jsonify({"error": f"Failed to create field: {exc}"}), 500


@app.delete("/api/fields/<int:field_id>")
def remove_field(field_id):
    try:
        database.delete_field(field_id)
        return jsonify({"ok": True, "id": field_id})
    except Exception as exc:
        return jsonify({"error": f"Failed to delete field: {exc}"}), 500


@app.get("/api/history")
def get_history():
    limit = request.args.get("limit", 50)
    try:
        limit = min(max(1, int(limit)), 200)
    except ValueError:
        limit = 50
    try:
        logs = database.get_history(limit=limit)
        return jsonify({"history": logs})
    except Exception as exc:
        return jsonify({"error": f"Failed to retrieve history: {exc}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV") != "production" and not os.environ.get("RENDER")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
