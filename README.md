# AgriAgent — AI-Powered Smart Agriculture & Irrigation Platform

[![Build Status](https://img.shields.io/badge/tests-28%20passed-brightgreen.svg)](#test-suite)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Flask Version](https://img.shields.io/badge/flask-3.1%2B-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)
[![Hackathon Evaluation](https://img.shields.io/badge/CLI%20Judging%20Contract-100%25%20Verified-success)](#judging-contract--cli-verification)

AgriAgent is an enterprise-grade, modern agricultural decision-support and smart irrigation platform built for the **AgentX Hackathon 2026**. It merges a full-stack web dashboard with an autonomous Python ReAct AI agent (Thought → Action → Observation → Decision) to help growers, agronomists, and farming operators make data-backed irrigation decisions, eliminate water wastage, and monitor crop health.

---

## Table of Contents

- [1. Project Objectives](#1-project-objectives)
- [2. System Architecture](#2-system-architecture)
- [3. Key Features & Modules](#3-key-features--modules)
- [4. Technology Stack](#4-technology-stack)
- [5. Hackathon Judging Contract & CLI Verification](#5-hackathon-judging-contract--cli-verification)
- [6. Deterministic Irrigation Model](#6-deterministic-irrigation-model)
- [7. REST API Documentation](#7-rest-api-documentation)
- [8. Local Installation & Execution Guide](#8-local-installation--execution-guide)
- [9. Production Deployment on Render](#9-production-deployment-on-render)
- [10. Test Suite](#10-test-suite)
- [11. Agronomic Assumptions & Disclaimers](#11-agronomic-assumptions--disclaimers)

---

## 1. Project Objectives

1. **Make Better Irrigation Decisions**: Calculate crop-specific moisture deficits and precise water volumes rather than relying on guesswork.
2. **Eliminate Water Wastage**: Calibrate irrigation depths against soil permeability and account for recent rainfall to prevent over-watering.
3. **Autonomous Agronomic Consultation**: Provide an AI Farm Assistant powered by a real ReAct reasoning loop that invokes registered tools to ground answers in agronomic data.
4. **Holistic Field Tracking**: Track multiple farming plots, historical irrigation recommendations, and water consumption analytics over time.
5. **Preserve Hackathon Judging Compatibility**: Maintain 100% compatibility with the original evaluation harness (`main.py --json`), offline test suites, and environment-based LLM providers (Gemini & Groq).

---

## 2. System Architecture

AgriAgent couples a responsive, modern SaaS dashboard with a modular Flask REST backend and the underlying ReAct agent loop:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       AGRIAGENT WEB DASHBOARD                               │
│  HTML5 · Modern Forest Green CSS (#176B45) · Chart.js Analytics · Vanilla JS│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ JSON REST APIs
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLASK WEB SERVICE                                 │
│  app.py: Rate Limiting · Request Validation · Database ORM · Health Probes  │
└──────────────┬───────────────────────────────────────────────┬──────────────┘
               │                                               │
               ▼                                               ▼
┌──────────────────────────────┐              ┌───────────────────────────────┐
│     DETERMINISTIC ENGINE     │              │        REACT AI AGENT         │
│     tools/irrigation.py      │              │ agent/core.py + agent/llm.py  │
│ - Soil moisture deficit      │              │ - Thought -> Action -> Obs    │
│ - Effective rainfall offset  │              │ - Gemini / Groq API wrapper   │
│ - Soil texture factor        │              │ - Fallback & repeat guards    │
│ - Volume (L) and depth (mm)  │              └───────────────┬───────────────┘
└──────────────┬───────────────┘                              │
               │                                              ▼
               │                              ┌───────────────────────────────┐
               │                              │         TOOL REGISTRY         │
               │                              │ - irrigation_advisor (NEW)    │
               │                              │ - crop_guide (NEW)            │
               │                              │ - calculator                  │
               │                              │ - sql_query / read_file       │
               │                              │ - list_files                  │
               │                              │ - web_search (DuckDuckGo)     │
               │                              └───────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PERSISTENT STORAGE & AUDIT                             │
│       SQLite (data/agriagent.db): Registered Fields · Irrigation Logs       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Key Features & Modules

### 1. Modern SaaS Overview Dashboard
- **Live Metrics**: Total fields monitored, cumulative acres tracked, average soil moisture, and total water volume recommended.
- **Crop Surveillance**: Quick summary of active parcels with one-click irrigation planning shortcuts.
- **Water Consumption Breakdown**: Chart.js bar visualization aggregating historical irrigation demands by crop.
- **Hardware & Weather API Status**: Explicit telemetry status indicating whether live weather API keys are configured, operating cleanly in transparent manual parameter mode without fabricating false sensor data.
- **Audit Trail**: Real-time activity feed tracking recent irrigation runs.

### 2. Smart Irrigation Planner
- **Interactive Inputs**: Crop type, soil texture, soil moisture slider (with 2-way display binding), ambient temperature, humidity, field acreage, and optional recent rainfall.
- **Supported Crops**: Rice (Paddy), Wheat, Maize (Corn), Tomato, Cotton, Sugarcane, and Groundnut (Peanut).
- **Comprehensive Outputs**:
  - Net water volume in **Litres (L)**.
  - Irrigation depth in **Millimetres (mm)**.
  - Soil moisture deficit and target threshold comparison.
  - Soil permeability factor adjustment (sandy +20%, clayey -15%, loamy 1.00x).
  - Priority badge (**High**, **Moderate**, **Low**) with actionable agronomic next steps.
  - Weather advisory & timing guidance (e.g., night/twilight scheduling under high heat).
  - Crop-specific water conservation strategy.
- **Field Preset Selector**: Pre-populate values from any saved parcel.
- **Scenario Presets**: Instant one-click tests for drought stress, rainy scenarios, and paddy flooding.

### 3. AI Farm Assistant
- Powered directly by the repository's native Python ReAct loop (`agent/core.py`).
- **Interactive Chat Interface**: Farmers can ask open-ended questions about water requirements, soil preparation, pest cycles, or conservation methods.
- **Inspectable Reasoning Trace**: Expandable ReAct trace showing each execution step: `Thought` → `Action: tool(args)` → `Observation`.
- **Pre-configured Prompts**: Quick-start prompt chips for common farmer queries.
- **Dry-Run Capability**: Toggleable offline mode allowing judges and developers to test the ReAct tool-invocation pipeline without an external API key.

### 4. Crop Advisory Knowledge Base
- In-depth agronomic catalog covering all 7 supported crops.
- Specifics include target moisture thresholds, seasonal water demand ranges, typical growing periods, optimal temperature zones, and soil compatibility.
- Interactive soil filter (Loamy, Sandy, Clayey).
- Direct "Plan Irrigation for this Crop" routing button.

### 5. Water Management & Benchmarks
- Seasonal water demand benchmark chart comparing crop requirements against FAO standards.
- Irrigation method efficiency benchmarks (Drip 85-95%, Sprinkler 70-80%, AWD 65-75%, Furrow 55-65%, Flood 40-50%).
- Practical conservation principles: Organic mulching, night scheduling, and managed deficit irrigation.

### 6. Field Management
- Full CRUD parcel inventory stored in SQLite (`data/agriagent.db`).
- Track field name, crop, soil type, acreage, and location/zone.
- Automatic integration into the Smart Irrigation planner dropdown.

### 7. Analytics & History
- Priority distribution doughnut chart.
- Chronological recommended irrigation depth line chart.
- Complete tabular historical audit log with timestamps, crop data, water volumes, and status.

### 8. System & Diagnostics
- Active LLM provider probe (Gemini / Groq / Dry-Run).
- Environment variable configuration guide.
- CLI verification commands for hackathon judges.

---

## 4. Technology Stack

- **Frontend**: HTML5, CSS3 (Modern custom design system, Forest Green palette `#176B45`, `#22875A`, `#F5F8F5`), Vanilla JavaScript (ES6+), Chart.js (v4.4.1).
- **Backend**: Python 3.10+, Flask 3.1+, SQLite3.
- **Production Server**: Gunicorn WSGI.
- **AI / LLM Integration**: Google GenAI SDK (`google-genai`), Groq SDK (`groq`), Python ReAct autonomous agent framework.
- **Search & Tools**: DuckDuckGo Search (`duckduckgo-search`), custom Python AST arithmetic calculator, CSV SQL engine.

---

## 5. Hackathon Judging Contract & CLI Verification

AgriAgent **preserves the exact original CLI interface and JSON output contract** required by the AgentX evaluation harness.

### 1. Test Single JSON Output Contract (Judges' Harness)
The evaluation harness runs `main.py --json`:
```bash
python main.py --json --dry-run "Evaluate wheat water requirements"
```
**Output (Single JSON line to stdout, logs to stderr):**
```json
{"answer": "Dry run OK: tools executed (list_files, calculator).", "trace": [{"thought": "See which data files exist.", "tool": "list_files", "args": {}, "observation": "agriagent.db, scores.csv"}, {"thought": "Check a calculation.", "tool": "calculator", "args": {"expression": "2 + 2 * 10"}, "observation": "22"}]}
```

### 2. Test Human-Readable CLI
```bash
python main.py --dry-run "How much water does rice require?"
```

### 3. Run Offline Test Suite
All 28 unit and integration tests run offline with zero API keys required:
```bash
python -m unittest discover tests
```
**Result:**
```text
Ran 28 tests in 0.896s
OK
```

---

## 6. Deterministic Irrigation Model

All irrigation calculations are executed in Python (`tools/irrigation.py`), ensuring deterministic, explainable, and testable outputs:

1. **Target Soil Moisture ($M_{target}$)**:
   - Rice: 45% · Wheat: 35% · Maize: 40% · Tomato: 38% · Cotton: 30% · Sugarcane: 42% · Groundnut: 32%
2. **Deficit Calculation**:
   $$\text{Deficit} = \max(0, M_{target} - M_{current})$$
3. **Evaporative Demand Adjustments**:
   - Temperature factor ($F_{temp}$): $1.0 + \max(0, T - 30.0) \times 0.025$
   - Humidity factor ($F_{humidity}$): $\max(0.75, 1.0 - \max(0, H - 60.0) \times 0.004)$
4. **Soil Permeability Factor ($F_{soil}$)**:
   - Sandy: $1.20$ (Rapid drainage requires higher volume)
   - Loamy: $1.00$ (Optimal balanced retention)
   - Clayey: $0.85$ (High moisture retention requires less volume)
5. **Gross Water Depth ($D_{gross}$)**:
   $$D_{gross} = \text{Deficit} \times 0.35 \times F_{temp} \times F_{humidity} \times F_{soil}$$
6. **Effective Rainfall Offset**:
   $$D_{net} = \max(0, D_{gross} - (\text{Rainfall} \times 0.75))$$
7. **Volume in Litres**:
   $$\text{Litres} = D_{net} \times \text{Area (Acres)} \times 4046.86$$

---

## 7. REST API Documentation

### `GET /api/health`
Health check for cloud host load balancers and container monitors.
```json
{
  "ai_provider": "none",
  "database": "sqlite_ready",
  "ok": true,
  "service": "AgriAgent",
  "status": "healthy",
  "version": "1.0.0"
}
```

### `POST /api/recommend`
Computes irrigation water demand and logs to persistent database.
- **Request Body**:
```json
{
  "crop": "tomato",
  "soil_type": "loamy",
  "soil_moisture": 25.0,
  "temperature": 32.0,
  "humidity": 50.0,
  "area": 2.5,
  "rainfall": 0.0,
  "field_name": "Sunny Valley Plot"
}
```
- **Response**:
```json
{
  "action": "Soil moisture is significantly below target. Apply recommended 4.8 mm in scheduled intervals.",
  "area_acres": 2.5,
  "crop": "Tomato",
  "deficit": 13.0,
  "disclaimer": "Demo estimate based on illustrative agronomic heuristics, not live sensor data or an official agronomic prescription.",
  "estimated_water_litres": 48562,
  "estimated_water_mm": 4.8,
  "humidity": 50.0,
  "priority": "High",
  "rainfall_mm": 0.0,
  "soil_moisture": 25.0,
  "soil_type": "Loamy",
  "status": "Irrigation recommended",
  "target_moisture": 38,
  "temperature": 32.0,
  "water_saving_tip": "Combine drip irrigation with organic or plastic mulch to conserve root-zone moisture.",
  "weather_note": "Optimal conditions: adjust application based on real-time field observation."
}
```

### `POST /api/ask`
Interacts with the ReAct AI Agent.
- **Request Body**:
```json
{
  "query": "What irrigation method is best for sandy soil?",
  "dry_run": false
}
```
- **Response**:
```json
{
  "answer": "For sandy soil, drip or micro-sprinkler irrigation is recommended...",
  "trace": [
    {
      "thought": "Check crop and soil recommendations.",
      "tool": "crop_guide",
      "args": {"crop": "tomato"},
      "observation": "..."
    }
  ],
  "configured": true
}
```

### `GET /api/fields` & `POST /api/fields` & `DELETE /api/fields/<id>`
Full CRUD endpoints for parcel management.

### `GET /api/history`
Returns historical irrigation audit entries for charts and reporting.

---

## 8. Local Installation & Execution Guide

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.14
- Git

### Step-by-Step Setup (Windows PowerShell)

```powershell
# 1. Clone repository
git clone https://github.com/rt983122-cloud/AgriAgent.git
cd AgriAgent

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
Copy-Item .env.example .env
# Open .env and add your GEMINI_API_KEY or GROQ_API_KEY (optional for dry-run)

# 5. Verify judging test suite
python -m unittest discover tests

# 6. Run the Flask Web Dashboard
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

---

## 9. Production Deployment on Render

AgriAgent is configured for 1-click deployment on [Render](https://render.com) using the included `render.yaml` and `Procfile`.

### Render Web Service Settings

| Setting | Value |
|---|---|
| **Environment** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn --workers 1 --threads 4 --timeout 120 app:app` |
| **Health Check Path** | `/api/health` |
| **Environment Variables** | `FLASK_ENV=production`<br>`GEMINI_API_KEY=<your_key>`<br>`GROQ_API_KEY=<your_key>` |

### Deploy via GitHub Repository
1. Push your changes to GitHub:
   ```bash
   git add .
   git commit -m "Complete AgriAgent modern web dashboard and ReAct tools"
   git push origin main
   ```
2. In the Render Dashboard, click **New +** → **Web Service**.
3. Connect your repository: `https://github.com/rt983122-cloud/AgriAgent`.
4. Enter the build command `pip install -r requirements.txt` and start command `gunicorn --workers 1 --threads 4 --timeout 120 app:app`.
5. Under **Environment Variables**, add `GEMINI_API_KEY` or `GROQ_API_KEY`.
6. Click **Deploy Web Service**. Render will bind to `0.0.0.0:$PORT` and monitor `/api/health`.

---

## 10. Test Suite

AgriAgent includes a test suite covering the ReAct core, mathematical bounds, input validation, and REST routes.

To run all tests:
```bash
python -m unittest discover tests
```

Tests include:
- `tests/test_agent.py`: ReAct loop verification, repeat guards, step iteration caps, SQL queries, and CLI contract.
- `tests/test_irrigation.py`: Deficit math, soil factors, rainfall offsets, boundary checks, and tool executions.
- `tests/test_app.py`: Web dashboard routes, API health, recommendation inputs, agent dry runs, and parcel CRUD.

---

## 11. Agronomic Assumptions & Disclaimers

> [!IMPORTANT]
> - **Illustrative Heuristics**: Crop target moisture thresholds and water demand multipliers in this application are illustrative models designed for hackathon demonstration. They do not constitute official agronomic prescriptions.
> - **Telemetry Integrity**: AgriAgent explicitly reports weather telemetry as manual mode when live meteorological API keys are not supplied. The platform never fabricates live sensor readings or weather reports.
> - **Field Deployment**: Real-world agricultural deployment requires calibration against local soil field capacity tests, meteorological stations, and certified agricultural extension service advisories.

---

**Built with pride for the AgentX Hackathon 2026.**
