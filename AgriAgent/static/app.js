/**
 * AgriAgent Platform 2.0 Frontend Controller
 * Fully interactive, modern dashboard, animated circular gauge,
 * precision water savings calculator, Chart.js analytics, and ReAct AI assistant.
 */

// Global state
let currentCropsData = {};
let currentFields = [];
let chartInstances = {};

// Helper selector
const $ = (id) => document.getElementById(id);

// ============================================================================
// Initialization
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initLiveClock();
  initRangeSyncing();
  initChatInput();
  
  // Initial data fetches
  loadSystemStatus();
  loadDashboardStats();
  loadCrops();
  loadFields();
  loadHistory();
  updateSavingsCalc();

  // Setup mobile menu toggle
  const mobileToggle = $("mobileToggle");
  const sidebar = $("sidebar");
  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener("click", () => {
      sidebar.classList.toggle("mobile-open");
    });
  }

  // Pre-render water benchmark chart
  renderWaterBenchmarkChart();
});

// ============================================================================
// Live Farm Clock
// ============================================================================
function initLiveClock() {
  const clockEl = $("liveClock");
  if (!clockEl) return;
  const update = () => {
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString() + " Local";
  };
  update();
  setInterval(update, 1000);
}

// ============================================================================
// Navigation & Tab Switching
// ============================================================================
function initNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.getAttribute("data-tab");
      switchTab(tab);
    });
  });
}

function switchTab(tabId) {
  // Update sidebar active state
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
  });

  // Switch tab panes
  document.querySelectorAll(".tab-pane").forEach((pane) => {
    pane.classList.remove("active");
  });
  const targetPane = $(`pane-${tabId}`);
  if (targetPane) {
    targetPane.classList.add("active");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // Close mobile sidebar if open
  const sidebar = $("sidebar");
  if (sidebar && sidebar.classList.contains("mobile-open")) {
    sidebar.classList.remove("mobile-open");
  }

  // Tab specific refreshes
  if (tabId === "overview") {
    loadDashboardStats();
  } else if (tabId === "analytics") {
    loadHistory();
  } else if (tabId === "fields") {
    loadFields();
  } else if (tabId === "crop-advisory") {
    if (Object.keys(currentCropsData).length === 0) loadCrops();
  } else if (tabId === "water-mgmt") {
    renderWaterBenchmarkChart();
    updateSavingsCalc();
  }
}

// ============================================================================
// Sliders, Range Syncing & Gauge
// ============================================================================
function initRangeSyncing() {
  const sync = (sliderId, valId, callback) => {
    const slider = $(sliderId);
    const display = $(valId);
    if (slider && display) {
      slider.addEventListener("input", () => {
        display.textContent = slider.value;
        if (callback) callback(parseFloat(slider.value));
      });
    }
  };

  sync("planMoisture", "valMoisture", (val) => {
    updateGauge(val, getSelectedTargetMoisture());
  });
  sync("planTemp", "valTemp");
  sync("planHumidity", "valHumidity");

  // Dynamic target moisture threshold update on crop select
  const cropSelect = $("planCrop");
  if (cropSelect) {
    cropSelect.addEventListener("change", () => {
      updateTargetMoistureBadge(cropSelect.value);
      updateGauge(parseFloat($("planMoisture").value), getSelectedTargetMoisture());
    });
    updateTargetMoistureBadge(cropSelect.value);
    updateGauge(parseFloat($("planMoisture").value), getSelectedTargetMoisture());
  }

  // Calculate button
  const btnCalculate = $("btnCalculate");
  if (btnCalculate) {
    btnCalculate.addEventListener("click", calculateIrrigation);
  }
}

function getSelectedTargetMoisture() {
  const cropMap = {
    rice: 45, wheat: 35, maize: 40, tomato: 38,
    cotton: 30, sugarcane: 42, groundnut: 32
  };
  const crop = ($("planCrop") ? $("planCrop").value : "tomato").toLowerCase();
  return cropMap[crop] || 38;
}

function updateTargetMoistureBadge(cropKey) {
  const badge = $("targetMoistureBadge");
  if (!badge) return;
  const target = getSelectedTargetMoisture();
  badge.textContent = `${target}%`;
}

// Circular SVG Soil Moisture Gauge Updater
function updateGauge(currentMoisture, targetMoisture) {
  const arc = $("gaugeArc");
  const currentValEl = $("gaugeCurrentVal");
  const targetValEl = $("gaugeTargetVal");
  if (!arc) return;

  const circumference = 314.159; // 2 * PI * 50
  const clampedMoisture = Math.min(Math.max(currentMoisture, 0), 100);
  const offset = circumference - (clampedMoisture / 100) * circumference;

  arc.style.strokeDasharray = `${circumference}`;
  arc.style.strokeDashoffset = `${offset}`;

  // Color dynamics
  if (clampedMoisture < targetMoisture - 8) {
    arc.style.stroke = "#DC2626"; // Severe deficit (Red)
  } else if (clampedMoisture < targetMoisture) {
    arc.style.stroke = "#D97706"; // Moderate deficit (Amber)
  } else if (clampedMoisture <= targetMoisture + 8) {
    arc.style.stroke = "#176B45"; // Ideal target (Forest Green)
  } else {
    arc.style.stroke = "#0284C7"; // Saturated (Blue)
  }

  if (currentValEl) currentValEl.textContent = `${Math.round(clampedMoisture)}%`;
  if (targetValEl) targetValEl.textContent = `Target: ${targetMoisture}%`;
}

function applyPreset(crop, moisture, temp, humidity, area, soil, rainfall) {
  $("planCrop").value = crop;
  $("planMoisture").value = moisture;
  $("valMoisture").textContent = moisture;
  $("planTemp").value = temp;
  $("valTemp").textContent = temp;
  $("planHumidity").value = humidity;
  $("valHumidity").textContent = humidity;
  $("planArea").value = area;
  $("planSoil").value = soil;
  $("planRainfall").value = rainfall;
  updateTargetMoistureBadge(crop);
  updateGauge(moisture, getSelectedTargetMoisture());
  calculateIrrigation();
}

function simulateWeather(temp, humidity, rainfall) {
  $("planTemp").value = temp;
  $("valTemp").textContent = temp;
  $("planHumidity").value = humidity;
  $("valHumidity").textContent = humidity;
  $("planRainfall").value = rainfall;
  showToast(`Simulated conditions loaded: ${temp}°C, ${humidity}% humidity, ${rainfall}mm rain.`, "info");
}

// ============================================================================
// Interactive Water Savings ROI Calculator
// ============================================================================
function updateSavingsCalc() {
  const areaSlider = $("calcArea");
  const cropSelect = $("calcCrop");
  const cyclesInput = $("calcCycles");
  if (!areaSlider || !cropSelect || !cyclesInput) return;

  const area = parseFloat(areaSlider.value) || 5;
  if ($("valCalcArea")) $("valCalcArea").textContent = area;

  const crop = cropSelect.value;
  const cycles = parseInt(cyclesInput.value) || 8;

  // Typical seasonal baseline water demand per acre in Litres
  const cropDemandMap = {
    rice: 350000, wheat: 180000, maize: 220000, tomato: 200000,
    cotton: 260000, sugarcane: 450000, groundnut: 160000
  };

  const baselinePerAcre = cropDemandMap[crop] || 200000;
  // Flood irrigation efficiency ~ 45%, Drip / Micro-irrigation ~ 90% (45% net water savings)
  const savingsRatio = 0.45;
  const totalWaterSaved = Math.round(area * baselinePerAcre * (cycles / 10) * savingsRatio);

  // Energy & Cost metrics (Rough agronomic rule of thumb: ~0.52 kWh per 1000L pumped; ₹0.08 / $0.001 per Litre)
  const energyKwhSaved = Math.round(totalWaterSaved * 0.00052);
  const costSavedInr = Math.round(totalWaterSaved * 0.08);
  const costSavedUsd = Math.round(costSavedInr / 83);

  if ($("calcWaterSaved")) {
    $("calcWaterSaved").textContent = `${totalWaterSaved.toLocaleString()} L`;
  }
  if ($("calcEnergySaved")) {
    $("calcEnergySaved").textContent = `~ ${energyKwhSaved.toLocaleString()} kWh`;
  }
  if ($("calcCostSaved")) {
    $("calcCostSaved").textContent = `₹ ${costSavedInr.toLocaleString()} / $${costSavedUsd}`;
  }
}

// ============================================================================
// System Status & Health Check
// ============================================================================
async function loadSystemStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) throw new Error("Status API error");
    const data = await res.json();

    // Topbar Pill
    const systemStatusText = $("systemStatusText");
    if (systemStatusText) {
      systemStatusText.textContent = "Backend: Online";
    }

    const providerText = $("providerText");
    if (providerText) {
      providerText.textContent = data.ai_configured ? data.ai_provider : "AI: Dry-Run / Manual Mode";
    }

    // Weather card info
    const weatherStatusMsg = $("weatherStatusMsg");
    if (weatherStatusMsg) {
      if (data.weather_configured) {
        weatherStatusMsg.textContent = "External meteorological service linked. Real-time atmospheric conditions available.";
        $("weatherModeBadge").textContent = "Live Telemetry";
        $("weatherModeBadge").className = "badge badge-success";
      } else {
        weatherStatusMsg.textContent = "No external weather API key is linked in .env. Operating in manual sensor parameter mode for hackathon demonstrations.";
        $("weatherModeBadge").textContent = "Manual Mode";
        $("weatherModeBadge").className = "badge badge-warning";
      }
    }

    // Settings diagnostics list
    if ($("diagProvider")) $("diagProvider").textContent = data.ai_provider;
    if ($("diagWeather")) $("diagWeather").textContent = data.weather_service;
    if ($("diagEnv")) $("diagEnv").textContent = data.environment;
    if ($("statProviderName")) $("statProviderName").textContent = data.ai_configured ? data.ai_provider : "ReAct Agent (Offline Mode)";

  } catch (err) {
    if ($("systemStatusText")) $("systemStatusText").textContent = "Backend: Offline";
    console.warn("Could not retrieve system status:", err);
  }
}

// ============================================================================
// Dashboard Stats & Overview
// ============================================================================
async function loadDashboardStats() {
  try {
    const res = await fetch("/api/stats");
    if (!res.ok) throw new Error("Failed to load statistics");
    const data = await res.json();

    if ($("statFieldsCount")) $("statFieldsCount").textContent = data.total_fields;
    if ($("statTotalArea")) $("statTotalArea").textContent = `Tracking ${data.total_area_acres} total acres`;
    if ($("statAvgMoisture")) $("statAvgMoisture").textContent = `${data.avg_soil_moisture}%`;
    if ($("statTotalWater")) $("statTotalWater").textContent = `${Number(data.total_water_litres).toLocaleString()} L`;
    if ($("statRecCount")) $("statRecCount").textContent = `Based on ${data.total_recommendations} recommendations`;

    // Render Recent Activities feed
    renderActivityFeed(data.recent_activities || []);

    // Render Crop Water Distribution Chart
    renderCropWaterChart(data.crop_usage || []);

  } catch (err) {
    console.error("Dashboard stats error:", err);
  }
}

function renderActivityFeed(activities) {
  const container = $("activityFeed");
  if (!container) return;
  if (!activities || activities.length === 0) {
    container.innerHTML = '<div class="empty-state">No irrigation activities logged yet.</div>';
    return;
  }

  container.innerHTML = activities.map((item) => {
    const prioClass = (item.priority || "low").toLowerCase();
    const litresFormatted = Number(item.water_litres || 0).toLocaleString();
    return `
      <div class="activity-item">
        <div class="activity-dot ${prioClass}"></div>
        <div class="activity-details">
          <div class="activity-title">${escapeHtml(item.field_name || "Plot")} — ${escapeHtml(item.crop)} (${item.priority} Priority)</div>
          <div class="activity-meta">${litresFormatted} L (${item.water_mm} mm) · ${escapeHtml(item.created_at)}</div>
        </div>
      </div>
    `;
  }).join("");
}

function renderCropWaterChart(cropData) {
  const canvas = $("cropWaterChart");
  if (!canvas || !window.Chart) return;

  if (chartInstances.cropWater) {
    chartInstances.cropWater.destroy();
  }

  const labels = cropData.map((d) => d.crop);
  const values = cropData.map((d) => d.total_litres);

  if (labels.length === 0) {
    labels.push("No Data");
    values.push(0);
  }

  chartInstances.cropWater = new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Water Volume (L)",
        data: values,
        backgroundColor: "#176B45",
        borderRadius: 8,
        hoverBackgroundColor: "#0F4D31"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (val) => val >= 1000 ? `${val / 1000}k L` : `${val} L`,
            font: { family: "DM Sans", size: 10 }
          },
          grid: { color: "rgba(223, 232, 226, 0.6)" }
        },
        x: {
          ticks: { font: { family: "DM Sans", size: 11, weight: "bold" } },
          grid: { display: false }
        }
      }
    }
  });
}

// ============================================================================
// Smart Irrigation Planner
// ============================================================================
async function calculateIrrigation() {
  const btn = $("btnCalculate");
  const emptyState = $("emptyResultState");
  const calcState = $("calculatedResultState");

  const crop = $("planCrop").value;
  const soilType = $("planSoil").value;
  const moisture = parseFloat($("planMoisture").value);
  const temp = parseFloat($("planTemp").value);
  const humidity = parseFloat($("planHumidity").value);
  const area = parseFloat($("planArea").value);
  const rainfall = parseFloat($("planRainfall").value || "0");
  const fieldSelect = $("planFieldSelect");
  const fieldName = fieldSelect && fieldSelect.value ? fieldSelect.options[fieldSelect.selectedIndex].text : "Custom Field";

  if (isNaN(area) || area <= 0) {
    showToast("Please enter a valid field area greater than 0.", "error");
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<span>Evaluating agronomic conditions...</span><span class="btn-arrow">⏳</span>';

  try {
    const res = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        crop: crop,
        soil_type: soilType,
        soil_moisture: moisture,
        temperature: temp,
        humidity: humidity,
        area: area,
        rainfall: rainfall,
        field_name: fieldName
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Calculation failed");

    // Render results
    emptyState.classList.add("hidden");
    calcState.classList.remove("hidden");

    const prio = data.priority.toLowerCase();
    $("resPriority").textContent = `${data.priority} Priority`;
    $("resPriority").className = `badge-priority ${prio}`;

    $("resStatus").textContent = data.status;
    $("resCropTag").textContent = data.crop;
    $("resLitres").textContent = `${Number(data.estimated_water_litres).toLocaleString()} L`;
    $("resMm").textContent = `${data.estimated_water_mm} mm`;
    $("resDeficit").textContent = `${data.deficit}%`;
    $("resMoistureRatio").textContent = `${data.soil_moisture}% / ${data.target_moisture}% target`;
    $("resSoilType").textContent = `${data.soil_type} texture`;

    // Tanker truck human scale comparison (~30,000L standard tanker)
    const tankers = (data.estimated_water_litres / 30000).toFixed(1);
    $("resTankerEquiv").textContent = `≈ ${tankers} Tankers (30,000L)`;

    const soilFactorMap = { sandy: "1.20x (+20%)", loamy: "1.00x (Balanced)", clayey: "0.85x (-15%)" };
    $("resSoilFactor").textContent = soilFactorMap[soilType.toLowerCase()] || "1.00x";

    if ($("resDeficitText")) $("resDeficitText").textContent = `${data.deficit}%`;
    if ($("resTargetText")) $("resTargetText").textContent = `${data.target_moisture}%`;
    if ($("resFactorText")) $("resFactorText").textContent = soilFactorMap[soilType.toLowerCase()] || "1.00x";

    $("resAction").textContent = data.action;
    $("resWeatherNote").textContent = data.weather_note;
    $("resWaterTip").textContent = data.water_saving_tip || "Use localized micro-irrigation to maximize water productivity.";
    $("resDisclaimer").textContent = `* ${data.disclaimer}`;

    // Update circular gauge
    updateGauge(data.soil_moisture, data.target_moisture);

    showToast("Irrigation plan successfully calculated and logged.", "success");

    // Refresh history and stats in background
    loadDashboardStats();
    loadHistory();

  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>Calculate Irrigation Plan</span><span class="btn-arrow">→</span>';
  }
}

// ============================================================================
// AI Farm Assistant (ReAct Loop)
// ============================================================================
function initChatInput() {
  const input = $("chatInput");
  const sendBtn = $("btnSendQuestion");

  if (input) {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendQuestion();
      }
    });
  }

  if (sendBtn) {
    sendBtn.addEventListener("click", sendQuestion);
  }
}

function askPreset(promptText) {
  $("chatInput").value = promptText;
  sendQuestion();
}

async function sendQuestion() {
  const input = $("chatInput");
  const query = input.value.trim();
  if (!query) return;

  const thread = $("chatThread");
  const sendBtn = $("btnSendQuestion");
  const dryRun = $("dryRunToggle").checked;

  // Append user bubble
  appendUserMessage(query);
  input.value = "";

  // Append loading assistant bubble
  const loadingId = "loading-" + Date.now();
  appendLoadingMessage(loadingId);
  sendBtn.disabled = true;

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query, dry_run: dryRun })
    });

    const data = await res.json();
    removeLoadingMessage(loadingId);

    if (!res.ok) throw new Error(data.error || "Agent request failed");

    appendAssistantMessage(data.answer, data.trace || [], data.configured);

  } catch (err) {
    removeLoadingMessage(loadingId);
    appendAssistantMessage(
      `An error occurred while communicating with the agent: ${err.message}. If running locally without an API key, check 'Dry Run Mode' to test the tool execution pipeline.`,
      [],
      false
    );
  } finally {
    sendBtn.disabled = false;
    thread.scrollTop = thread.scrollHeight;
  }
}

function appendUserMessage(text) {
  const thread = $("chatThread");
  const bubble = document.createElement("div");
  bubble.className = "chat-bubble user-bubble";
  bubble.innerHTML = `
    <div class="bubble-avatar">FM</div>
    <div class="bubble-content">
      <div class="bubble-header-row">
        <span class="bubble-author">You</span>
        <span class="bubble-time">Just now</span>
      </div>
      <p>${escapeHtml(text)}</p>
    </div>
  `;
  thread.appendChild(bubble);
  thread.scrollTop = thread.scrollHeight;
}

function appendLoadingMessage(id) {
  const thread = $("chatThread");
  const bubble = document.createElement("div");
  bubble.id = id;
  bubble.className = "chat-bubble assistant-bubble";
  bubble.innerHTML = `
    <div class="bubble-avatar">✧</div>
    <div class="bubble-content">
      <div class="bubble-header-row">
        <span class="bubble-author">AgriAgent System</span>
        <span class="bubble-time">Thinking...</span>
      </div>
      <p><i>Evaluating agronomic context, formulating reasoning steps, and invoking tools...</i></p>
    </div>
  `;
  thread.appendChild(bubble);
  thread.scrollTop = thread.scrollHeight;
}

function removeLoadingMessage(id) {
  const el = $(id);
  if (el) el.remove();
}

function appendAssistantMessage(answerText, trace, isConfigured) {
  const thread = $("chatThread");
  const bubble = document.createElement("div");
  bubble.className = "chat-bubble assistant-bubble";

  let traceHtml = "";
  if (trace && trace.length > 0) {
    const traceItemsHtml = trace.map((t, idx) => `
      <div class="trace-item">
        <span class="trace-step-badge">Step ${idx + 1} ReAct Node</span>
        <div class="trace-thought">Thought: ${escapeHtml(t.thought || "Evaluate problem and invoke appropriate tool")}</div>
        <div class="trace-call">Action: <b>${escapeHtml(t.tool)}</b>(${escapeHtml(JSON.stringify(t.args))})</div>
        <div class="trace-observation">Observation: ${escapeHtml(t.observation || "")}</div>
      </div>
    `).join("");

    traceHtml = `
      <details class="trace-accordion">
        <summary class="trace-summary">
          <span>🛠 ReAct Autonomous Trace (${trace.length} tool executions)</span>
        </summary>
        ${traceItemsHtml}
      </details>
    `;
  }

  const bubbleId = "bubble-" + Date.now();
  bubble.innerHTML = `
    <div class="bubble-avatar">✧</div>
    <div class="bubble-content" id="${bubbleId}">
      <div class="bubble-header-row">
        <span class="bubble-author">AgriAgent System</span>
        <button class="btn btn-sm btn-ghost" onclick="copyAnswerText('${bubbleId}')" style="padding: 2px 8px; font-size: 10px;">📋 Copy</button>
      </div>
      <div class="answer-body">${formatMarkdown(answerText)}</div>
      ${traceHtml}
    </div>
  `;
  thread.appendChild(bubble);
}

function copyAnswerText(containerId) {
  const el = $(containerId);
  if (!el) return;
  const body = el.querySelector(".answer-body");
  if (body) {
    navigator.clipboard.writeText(body.innerText).then(() => {
      showToast("Answer copied to clipboard.", "info");
    });
  }
}

// ============================================================================
// Crop Advisory Module
// ============================================================================
async function loadCrops() {
  const container = $("cropCardsGrid");
  if (!container) return;
  container.innerHTML = '<div class="empty-state">Loading crop advisory database...</div>';

  try {
    const res = await fetch("/api/crops");
    if (!res.ok) throw new Error("Failed to load crop knowledge base");
    const data = await res.json();
    currentCropsData = data.crops || {};
    renderCropCards("all");

    // Soil filter listener
    const filterSelect = $("cropFilterSoil");
    if (filterSelect) {
      filterSelect.addEventListener("change", () => {
        renderCropCards(filterSelect.value);
      });
    }

  } catch (err) {
    container.innerHTML = `<div class="empty-state">Could not load crops: ${err.message}</div>`;
  }
}

function renderCropCards(soilFilter) {
  const container = $("cropCardsGrid");
  if (!container) return;

  const crops = Object.entries(currentCropsData);
  const filtered = crops.filter(([key, crop]) => {
    if (soilFilter === "all") return true;
    return (crop.soil_suitability || []).includes(soilFilter);
  });

  if (filtered.length === 0) {
    container.innerHTML = '<div class="empty-state">No crops found matching the selected soil filter.</div>';
    return;
  }

  container.innerHTML = filtered.map(([key, crop]) => `
    <div class="crop-card">
      <div class="crop-card-top">
        <div class="crop-name">${escapeHtml(crop.name)}</div>
        <div class="target-badge">${crop.target_moisture}% Target</div>
      </div>
      <p class="crop-desc">${escapeHtml(crop.description)}</p>
      <div class="crop-specs">
        <div class="spec-item">
          <small>Water Demand</small>
          <strong>${escapeHtml(crop.water_demand)}</strong>
        </div>
        <div class="spec-item">
          <small>Growing Cycle</small>
          <strong>${escapeHtml(crop.growing_period)}</strong>
        </div>
        <div class="spec-item">
          <small>Optimal Temperature</small>
          <strong>${escapeHtml(crop.optimal_temp_c)} °C</strong>
        </div>
        <div class="spec-item">
          <small>Soil Suitability</small>
          <strong>${(crop.soil_suitability || []).map(s => s.toUpperCase()).join(", ")}</strong>
        </div>
      </div>
      <div class="tip-box" style="margin-bottom: 14px;">
        <div class="tip-icon">💡</div>
        <div class="tip-text">
          <small>CONSERVATION ADVICE</small>
          <p>${escapeHtml(crop.water_saving_tips)}</p>
        </div>
      </div>
      <div class="crop-card-actions">
        <button class="btn btn-sm btn-primary full-width" onclick="planForCrop('${key}')">Plan Irrigation for this Crop →</button>
      </div>
    </div>
  `).join("");
}

function planForCrop(cropKey) {
  switchTab("irrigation");
  const cropSelect = $("planCrop");
  if (cropSelect) {
    cropSelect.value = cropKey;
    updateTargetMoistureBadge(cropKey);
    updateGauge(parseFloat($("planMoisture").value), getSelectedTargetMoisture());
  }
}

// ============================================================================
// Water Management & Benchmarks Chart
// ============================================================================
function renderWaterBenchmarkChart() {
  const canvas = $("cropBenchmarkChart");
  if (!canvas || !window.Chart) return;

  if (chartInstances.benchmark) {
    chartInstances.benchmark.destroy();
  }

  chartInstances.benchmark = new Chart(canvas, {
    type: "bar",
    data: {
      labels: ["Rice", "Sugarcane", "Cotton", "Maize", "Wheat", "Tomato", "Groundnut"],
      datasets: [
        {
          label: "Min Demand (mm)",
          data: [1200, 1500, 700, 500, 450, 400, 400],
          backgroundColor: "#83BCA2",
          borderRadius: 6
        },
        {
          label: "Max Demand (mm)",
          data: [1500, 2500, 1000, 800, 650, 600, 550],
          backgroundColor: "#176B45",
          borderRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top" }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (v) => `${v} mm`,
            font: { family: "DM Sans", size: 10 }
          },
          grid: { color: "rgba(223, 232, 226, 0.6)" }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

// ============================================================================
// Field Management
// ============================================================================
async function loadFields() {
  try {
    const res = await fetch("/api/fields");
    if (!res.ok) throw new Error("Could not retrieve fields");
    const data = await res.json();
    currentFields = data.fields || [];

    renderFieldsGrid(currentFields);
    renderOverviewFieldsTable(currentFields);
    populatePlannerFieldSelect(currentFields);

  } catch (err) {
    console.warn("Field loading warning:", err);
  }
}

function renderFieldsGrid(fields) {
  const container = $("fieldsContainer");
  if (!container) return;

  if (fields.length === 0) {
    container.innerHTML = '<div class="empty-state">No fields registered yet. Click "Register New Field" to add one.</div>';
    return;
  }

  container.innerHTML = fields.map((f) => `
    <div class="field-card">
      <div class="field-card-header">
        <div class="field-name">${escapeHtml(f.name)}</div>
        <span class="badge badge-platform">${escapeHtml(f.crop.toUpperCase())}</span>
      </div>
      <div class="field-location">📍 ${escapeHtml(f.location || "Primary Zone")}</div>
      <div class="field-metrics-row">
        <div class="field-metric-item">
          <small>Area</small>
          <strong>${f.area} ac</strong>
        </div>
        <div class="field-metric-item">
          <small>Soil</small>
          <strong>${escapeHtml(f.soil_type)}</strong>
        </div>
        <div class="field-metric-item">
          <small>Created</small>
          <strong>${escapeHtml(f.created_at ? f.created_at.split(" ")[0] : "Recent")}</strong>
        </div>
      </div>
      <div class="field-card-actions">
        <button class="btn btn-sm btn-ghost" onclick="deleteField(${f.id})">Delete</button>
        <button class="btn btn-sm btn-secondary" onclick="planForField(${f.id})">Plan Irrigation →</button>
      </div>
    </div>
  `).join("");
}

function renderOverviewFieldsTable(fields) {
  const tbody = $("overviewFieldsBody");
  if (!tbody) return;

  if (fields.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center empty-state">No fields registered yet.</td></tr>';
    return;
  }

  tbody.innerHTML = fields.slice(0, 5).map((f) => `
    <tr>
      <td><b>${escapeHtml(f.name)}</b></td>
      <td><span class="badge badge-platform">${escapeHtml(f.crop)}</span></td>
      <td>${escapeHtml(f.soil_type)}</td>
      <td>${f.area} acres</td>
      <td>${escapeHtml(f.location || "Main")}</td>
      <td><button class="btn btn-sm btn-ghost" onclick="planForField(${f.id})">Plan →</button></td>
    </tr>
  `).join("");
}

function populatePlannerFieldSelect(fields) {
  const select = $("planFieldSelect");
  if (!select) return;

  select.innerHTML = '<option value="">-- Manual Custom Entry --</option>' +
    fields.map((f) => `<option value="${f.id}">${escapeHtml(f.name)} (${f.crop}, ${f.area} ac)</option>`).join("");

  select.onchange = () => {
    const selectedId = parseInt(select.value);
    const field = fields.find(f => f.id === selectedId);
    if (field) {
      $("planCrop").value = field.crop;
      $("planSoil").value = field.soil_type;
      $("planArea").value = field.area;
      updateTargetMoistureBadge(field.crop);
      updateGauge(parseFloat($("planMoisture").value), getSelectedTargetMoisture());
    }
  };
}

function planForField(fieldId) {
  const field = currentFields.find(f => f.id === fieldId);
  if (!field) return;

  switchTab("irrigation");
  const select = $("planFieldSelect");
  if (select) select.value = field.id;
  $("planCrop").value = field.crop;
  $("planSoil").value = field.soil_type;
  $("planArea").value = field.area;
  updateTargetMoistureBadge(field.crop);
  updateGauge(parseFloat($("planMoisture").value), getSelectedTargetMoisture());
}

// Modal handling
function openFieldModal() {
  const modal = $("fieldModal");
  if (modal) modal.classList.remove("hidden");
}

function closeFieldModal() {
  const modal = $("fieldModal");
  if (modal) modal.classList.add("hidden");
}

async function submitFieldForm(event) {
  event.preventDefault();
  const name = $("newFieldName").value.trim();
  const crop = $("newFieldCrop").value;
  const soil = $("newFieldSoil").value;
  const area = parseFloat($("newFieldArea").value);
  const location = $("newFieldLocation").value.trim();

  if (!name || isNaN(area) || area <= 0) {
    showToast("Please provide a valid field name and area.", "error");
    return;
  }

  try {
    const res = await fetch("/api/fields", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, crop, soil_type: soil, area, location })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Failed to create field");

    showToast("Field created successfully.", "success");
    closeFieldModal();
    $("newFieldForm").reset();
    loadFields();
    loadDashboardStats();

  } catch (err) {
    showToast(err.message, "error");
  }
}

async function deleteField(fieldId) {
  if (!confirm("Are you sure you want to remove this field?")) return;
  try {
    const res = await fetch(`/api/fields/${fieldId}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to delete field");
    showToast("Field deleted.", "info");
    loadFields();
    loadDashboardStats();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ============================================================================
// Analytics & History
// ============================================================================
async function loadHistory() {
  const tbody = $("historyTableBody");
  if (!tbody) return;

  try {
    const res = await fetch("/api/history?limit=30");
    if (!res.ok) throw new Error("Failed to load historical data");
    const data = await res.json();
    const logs = data.history || [];

    if ($("historyCounter")) $("historyCounter").textContent = `${logs.length} Logs Recorded`;

    if (logs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" class="text-center empty-state">No recommendations logged yet.</td></tr>';
      return;
    }

    tbody.innerHTML = logs.map((log) => {
      const prioClass = (log.priority || "low").toLowerCase();
      const litresFormatted = Number(log.water_litres).toLocaleString();
      return `
        <tr>
          <td><small>${escapeHtml(log.created_at)}</small></td>
          <td><b>${escapeHtml(log.field_name || "Plot")}</b></td>
          <td>${escapeHtml(log.crop)}</td>
          <td>${escapeHtml(log.soil_type)}</td>
          <td>${log.soil_moisture}%</td>
          <td><b>${litresFormatted} L</b></td>
          <td>${log.water_mm} mm</td>
          <td><span class="badge-priority ${prioClass}">${escapeHtml(log.priority)}</span></td>
          <td><small>${escapeHtml(log.action)}</small></td>
        </tr>
      `;
    }).join("");

    renderAnalyticsCharts(logs);

  } catch (err) {
    console.warn("History load error:", err);
  }
}

function renderAnalyticsCharts(logs) {
  if (!window.Chart) return;

  // 1. Priority Doughnut Chart
  const priorityCanvas = $("priorityChart");
  if (priorityCanvas) {
    if (chartInstances.priority) chartInstances.priority.destroy();

    const prioCounts = { High: 0, Moderate: 0, Low: 0 };
    logs.forEach(l => {
      if (prioCounts[l.priority] !== undefined) prioCounts[l.priority]++;
    });

    chartInstances.priority = new Chart(priorityCanvas, {
      type: "doughnut",
      data: {
        labels: ["High Priority", "Moderate", "Low Priority"],
        datasets: [{
          data: [prioCounts.High, prioCounts.Moderate, prioCounts.Low],
          backgroundColor: ["#DC2626", "#D97706", "#176B45"],
          borderWidth: 2,
          borderColor: "#FFFFFF"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom" } }
      }
    });
  }

  // 2. Depth History Chart
  const depthCanvas = $("depthHistoryChart");
  if (depthCanvas) {
    if (chartInstances.depth) chartInstances.depth.destroy();

    const chronological = [...logs].reverse().slice(-10);
    const labels = chronological.map(l => l.crop);
    const values = chronological.map(l => l.water_mm);

    chartInstances.depth = new Chart(depthCanvas, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Depth (mm)",
          data: values,
          borderColor: "#176B45",
          backgroundColor: "rgba(23, 107, 69, 0.12)",
          fill: true,
          tension: 0.35,
          pointBackgroundColor: "#176B45",
          pointRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { callback: v => `${v} mm` },
            grid: { color: "rgba(223, 232, 226, 0.6)" }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }
}

// ============================================================================
// Utilities
// ============================================================================
function showToast(message, type = "info") {
  const container = $("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(12px)";
    toast.style.transition = "all 0.25s ease";
    setTimeout(() => toast.remove(), 250);
  }, 4000);
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatMarkdown(text) {
  if (!text) return "";
  let escaped = escapeHtml(text);
  // Bold **text**
  escaped = escaped.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  // Bullet points
  escaped = escaped.replace(/^\s*-\s+(.*)$/gm, "<li>$1</li>");
  escaped = escaped.replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>");
  // Newlines to breaks
  escaped = escaped.replace(/\n\n/g, "</p><p>").replace(/\n/g, "<br>");
  return `<p>${escaped}</p>`;
}
