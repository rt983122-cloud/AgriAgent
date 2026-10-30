"""Deterministic irrigation calculations and crop knowledge tools for AgriAgent.

Provides:
- build_irrigation_recommendation: core calculation engine
- CROP_PROFILES: comprehensive agronomic metadata for supported crops
- IrrigationAdvisor: ReAct agent tool for calculating water needs
- CropGuide: ReAct agent tool for crop threshold and management lookup
"""
from tools import Tool

# Illustrative crop target soil moisture thresholds (%) and profiles for hackathon demo
CROP_PROFILES = {
    "rice": {
        "name": "Rice (Paddy)",
        "target_moisture": 45,
        "soil_suitability": ["clayey", "loamy"],
        "water_demand": "High (1200 - 1500 mm / season)",
        "growing_period": "120 - 150 days",
        "optimal_temp_c": "22 - 32",
        "description": "Requires saturated or near-saturated soil during vegetative and reproductive stages.",
        "irrigation_methods": ["Alternate Wetting and Drying (AWD)", "Controlled Flooding"],
        "water_saving_tips": "Implement Alternate Wetting and Drying (AWD) to cut water usage up to 30% without yield loss."
    },
    "wheat": {
        "name": "Wheat",
        "target_moisture": 35,
        "soil_suitability": ["loamy", "clayey"],
        "water_demand": "Medium (450 - 650 mm / season)",
        "growing_period": "100 - 130 days",
        "optimal_temp_c": "15 - 25",
        "description": "Sensitive to waterlogging; critical stages are crown root initiation (CRI), flowering, and grain filling.",
        "irrigation_methods": ["Sprinkler Irrigation", "Border Strip", "Furrow"],
        "water_saving_tips": "Target CRI (21 days post-sowing) and heading stages to maximize water-use efficiency."
    },
    "maize": {
        "name": "Maize (Corn)",
        "target_moisture": 40,
        "soil_suitability": ["loamy", "sandy"],
        "water_demand": "Medium (500 - 800 mm / season)",
        "growing_period": "90 - 120 days",
        "optimal_temp_c": "18 - 30",
        "description": "Tasseling and silking are moisture-critical stages. Requires well-drained fertile soil.",
        "irrigation_methods": ["Drip Irrigation", "Furrow Irrigation"],
        "water_saving_tips": "Use subsurface drip to prevent weed competition and reduce evaporation losses by 25%."
    },
    "tomato": {
        "name": "Tomato",
        "target_moisture": 38,
        "soil_suitability": ["loamy", "sandy"],
        "water_demand": "Medium-High (400 - 600 mm / season)",
        "growing_period": "90 - 140 days",
        "optimal_temp_c": "20 - 28",
        "description": "Consistent moisture prevents blossom end rot and fruit cracking. Susceptible to foliar fungal diseases.",
        "irrigation_methods": ["Drip Irrigation with Mulch", "Micro-sprinklers"],
        "water_saving_tips": "Combine drip irrigation with organic or plastic mulch to conserve root-zone moisture."
    },
    "cotton": {
        "name": "Cotton",
        "target_moisture": 30,
        "soil_suitability": ["clayey", "loamy"],
        "water_demand": "Medium (700 - 1000 mm / season)",
        "growing_period": "150 - 180 days",
        "optimal_temp_c": "21 - 35",
        "description": "Deep-rooted crop; critical water demand peaks during flowering and boll development.",
        "irrigation_methods": ["Alternate Furrow Irrigation", "Drip Irrigation"],
        "water_saving_tips": "Alternate furrow irrigation cuts water by 30-40% while preserving boll yields."
    },
    "sugarcane": {
        "name": "Sugarcane",
        "target_moisture": 42,
        "soil_suitability": ["loamy", "clayey"],
        "water_demand": "Very High (1500 - 2500 mm / season)",
        "growing_period": "300 - 365 days",
        "optimal_temp_c": "24 - 35",
        "description": "Long-duration crop with heavy biomass production requiring steady moisture replenishment.",
        "irrigation_methods": ["Trash Mulching + Drip", "Ring Basin", "Paired Row Drip"],
        "water_saving_tips": "Trash mulching retains up to 40% soil moisture and reduces canopy evaporation."
    },
    "groundnut": {
        "name": "Groundnut (Peanut)",
        "target_moisture": 32,
        "soil_suitability": ["sandy", "loamy"],
        "water_demand": "Low-Medium (400 - 550 mm / season)",
        "growing_period": "100 - 120 days",
        "optimal_temp_c": "22 - 30",
        "description": "Pegging and pod development stages are highly sensitive to drought; prefers loose, well-aerated soil.",
        "irrigation_methods": ["Sprinkler Irrigation", "Border Furrow"],
        "water_saving_tips": "Avoid excess moisture during early vegetative growth to encourage deep taproot development."
    }
}

CROP_THRESHOLDS = {crop: data["target_moisture"] for crop, data in CROP_PROFILES.items()}
SOIL_FACTOR = {"sandy": 1.20, "loamy": 1.00, "clayey": 0.85}


def build_irrigation_recommendation(crop, soil_moisture, temperature, humidity, area, soil_type, rainfall=0.0):
    """Calculate soil moisture deficit, water depth (mm), and volume (litres).
    
    Includes temperature/humidity evaporative adjustments, soil permeability factors,
    and optional rainfall offset.
    """
    crop_key = str(crop).lower().strip()
    soil_key = str(soil_type).lower().strip()

    if crop_key not in CROP_THRESHOLDS:
        raise ValueError("Choose rice, wheat, maize, tomato, cotton, sugarcane or groundnut.")
    if soil_key not in SOIL_FACTOR:
        raise ValueError("Soil type must be sandy, loamy or clayey.")
    if not (0.0 <= soil_moisture <= 100.0):
        raise ValueError("Soil moisture must be between 0 and 100%.")
    if not (-5.0 <= temperature <= 60.0):
        raise ValueError("Temperature must be between -5 and 60 °C.")
    if not (0.0 <= humidity <= 100.0):
        raise ValueError("Humidity must be between 0 and 100%.")
    if not (0.01 <= area <= 10000.0):
        raise ValueError("Area must be between 0.01 and 10,000 acres.")

    rainfall = float(rainfall or 0.0)
    if rainfall < 0:
        raise ValueError("Rainfall cannot be negative.")

    target = CROP_THRESHOLDS[crop_key]
    profile = CROP_PROFILES[crop_key]

    # Deficit calculation
    deficit = max(0.0, target - soil_moisture)
    
    # Evaporative demand adjustment factors
    heat_factor = 1.0 + max(0.0, temperature - 30.0) * 0.025
    humidity_factor = max(0.75, 1.0 - max(0.0, humidity - 60.0) * 0.004)
    soil_factor = SOIL_FACTOR[soil_key]

    gross_water_mm = deficit * 0.35 * heat_factor * humidity_factor * soil_factor

    # Effective rainfall offset (assuming ~75% percolation efficiency for light to moderate rain)
    effective_rain = round(rainfall * 0.75, 1) if rainfall > 0 else 0.0
    net_water_mm = max(0.0, gross_water_mm - effective_rain)
    water_mm = round(net_water_mm, 1)

    # 1 mm of water over 1 acre = 4,046.86 Litres
    water_litres = int(round(water_mm * area * 4046.86, 0))

    # Priority and action determination
    if deficit <= 0 or water_mm <= 0:
        if rainfall > 0 and gross_water_mm > 0:
            status = "No irrigation needed (Rainfall sufficient)"
            action = f"Recent rainfall of {rainfall:.1f} mm covers estimated crop moisture need. Monitor drainage."
        else:
            status = "No irrigation needed now"
            action = "Current moisture satisfies target threshold. Recheck soil moisture in 2-3 days."
        priority = "Low"
    elif deficit < 10:
        status = "Light irrigation recommended"
        action = f"Apply a controlled light irrigation cycle ({water_mm} mm) and recheck soil moisture."
        priority = "Moderate"
    else:
        status = "Irrigation recommended"
        action = f"Soil moisture is significantly below target. Apply recommended {water_mm} mm in scheduled intervals."
        priority = "High"

    # Weather-specific notes
    if temperature >= 38:
        weather_note = "High heat alert: irrigate early morning (before 9 AM) or evening to prevent evaporation loss."
    elif humidity >= 80:
        weather_note = "High ambient humidity: watch for fungal conditions and avoid overwatering."
    elif rainfall > 0:
        weather_note = f"Recorded rainfall: {rainfall:.1f} mm. Subtracted {effective_rain:.1f} mm effective rain from baseline demand."
    else:
        weather_note = "Optimal conditions: adjust application based on real-time field observation."

    # Water-saving advice for the selected crop
    tip = profile.get("water_saving_tips", "Use localized micro-irrigation to maximize water productivity.")

    return {
        "crop": profile["name"],
        "crop_key": crop_key,
        "soil_type": soil_key.title(),
        "soil_moisture": round(soil_moisture, 1),
        "target_moisture": target,
        "deficit": round(deficit, 1),
        "temperature": round(temperature, 1),
        "humidity": round(humidity, 1),
        "rainfall_mm": round(rainfall, 1),
        "area_acres": round(area, 2),
        "priority": priority,
        "status": status,
        "action": action,
        "estimated_water_mm": water_mm,
        "estimated_water_litres": water_litres,
        "weather_note": weather_note,
        "water_saving_tip": tip,
        "disclaimer": "Demo estimate based on illustrative agronomic heuristics, not live sensor data or an official agronomic prescription."
    }


class IrrigationAdvisor(Tool):
    name = "irrigation_advisor"
    description = (
        "Estimate irrigation water requirements and priority given crop, soil moisture, "
        "temperature, humidity, field area, soil type, and optional rainfall. "
        "Returns transparent demo estimates with litres and millimetres."
    )
    args_doc = '{"crop":"rice|wheat|maize|tomato|cotton|sugarcane|groundnut","soil_moisture":0-100,"temperature":-5-60,"humidity":0-100,"area":0.01-10000,"soil_type":"sandy|loamy|clayey","rainfall":0.0}'

    def execute(self, crop="rice", soil_moisture=35, temperature=32, humidity=55, area=1, soil_type="loamy", rainfall=0.0):
        return build_irrigation_recommendation(
            crop=crop,
            soil_moisture=float(soil_moisture),
            temperature=float(temperature),
            humidity=float(humidity),
            area=float(area),
            soil_type=soil_type,
            rainfall=float(rainfall or 0.0)
        )


class CropGuide(Tool):
    name = "crop_guide"
    description = (
        "Look up agronomic profile, target moisture threshold, recommended irrigation methods, "
        "and water-saving advice for a supported crop."
    )
    args_doc = '{"crop":"rice|wheat|maize|tomato|cotton|sugarcane|groundnut"}'

    def execute(self, crop="rice"):
        key = str(crop).lower().strip()
        if key not in CROP_PROFILES:
            supported = ", ".join(CROP_PROFILES.keys())
            return f"Unknown crop '{crop}'. Supported crops: {supported}"
        p = CROP_PROFILES[key]
        return (
            f"Crop: {p['name']}\n"
            f"Target Moisture: {p['target_moisture']}%\n"
            f"Water Demand: {p['water_demand']}\n"
            f"Growing Duration: {p['growing_period']}\n"
            f"Soil Suitability: {', '.join(p['soil_suitability'])}\n"
            f"Recommended Irrigation: {', '.join(p['irrigation_methods'])}\n"
            f"Water Saving Tip: {p['water_saving_tips']}\n"
            f"Description: {p['description']}"
        )
