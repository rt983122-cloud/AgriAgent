"""Thin wrapper over the free LLM APIs. Picks Gemini or Groq from your environment."""
import json
import os
import time

import config


class LLM:
    def __init__(self, provider=None):
        self.provider = provider or os.environ.get("AGENTX_PROVIDER") or (
            "gemini" if os.environ.get("GEMINI_API_KEY") else "groq" if os.environ.get("GROQ_API_KEY") else None)
        if self.provider is None:
            raise RuntimeError("No API key found. Set GEMINI_API_KEY or GROQ_API_KEY in .env (both are free).")
        if self.provider == "gemini":
            from google import genai
            self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        else:
            from groq import Groq
            self.client = Groq(api_key=os.environ["GROQ_API_KEY"])

    def generate(self, system, messages):
        """messages: list of {"role": "user"|"assistant", "content": str}. Returns text. Retries on 429."""
        for attempt in range(4):
            try:
                return self._call(system, messages)
            except Exception as e:
                converted = self._native_tool_call_as_json(e)
                if converted:
                    return converted
                # rate limit: back off and retry, otherwise surface the error
                if attempt < 3 and ("429" in str(e) or "rate" in str(e).lower() or "quota" in str(e).lower()):
                    time.sleep(2 * 2 ** attempt)
                    continue
                raise

    @staticmethod
    def _native_tool_call_as_json(e):
        """Groq's gpt-oss sometimes emits a native tool call, which the API rejects (400 tool_use_failed).
        Turn that into our JSON action so the agent loop keeps going (unknown tool names are reported back)."""
        try:
            body = e.response.json()["error"]
            if body.get("code") != "tool_use_failed":
                return None
            call = json.loads(body["failed_generation"])
            return json.dumps({"thought": "(native tool call)", "action": str(call["name"]).split(".")[-1],
                               "args": call.get("arguments") or {}})
        except Exception:
            return None

    def _call(self, system, messages):
        if self.provider == "gemini":
            from google.genai import types
            text = "\n\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
            r = self.client.models.generate_content(
                model=config.GEMINI_MODEL, contents=text,
                config=types.GenerateContentConfig(system_instruction=system, temperature=config.TEMPERATURE))
            return r.text or ""
        r = self.client.chat.completions.create(
            model=config.GROQ_MODEL, temperature=config.TEMPERATURE,
            messages=[{"role": "system", "content": system}] + messages)
        msg = r.choices[0].message
        # some Groq reasoning models (gpt-oss) leave `content` empty and put the reply in `reasoning`
        return msg.content or getattr(msg, "reasoning", None) or ""


class DryRunLLM:
    """Scripted stand-in so you can test your setup with NO API key: python main.py --dry-run "..." """

    def __init__(self):
        self.step = 0

    def generate(self, system, messages):
        self.step += 1
        first_query = (messages[0]["content"] if messages and "content" in messages[0] else "").lower()

        crops = ["rice", "wheat", "maize", "tomato", "cotton", "sugarcane", "groundnut"]
        detected_crop = next((c for c in crops if c in first_query), None)
        is_agri_query = detected_crop is not None or any(w in first_query for w in ["water", "irrigation", "soil", "crop", "moisture", "productivity"])

        if is_agri_query:
            soils = ["sandy", "clayey", "loamy"]
            detected_soil = next((s for s in soils if s in first_query), "loamy")
            target_crop = detected_crop or ("tomato" if "sandy" in first_query else "rice")

            if self.step == 1:
                return json.dumps({
                    "thought": f"Look up agronomic profile, optimal thresholds, and water management guidelines for {target_crop}.",
                    "action": "crop_guide",
                    "args": {"crop": target_crop}
                })
            if self.step == 2:
                return json.dumps({
                    "thought": f"Calculate baseline irrigation requirements for {target_crop} with {detected_soil} soil parameters.",
                    "action": "irrigation_advisor",
                    "args": {
                        "crop": target_crop,
                        "soil_moisture": 25.0 if "low" in first_query else 30.0,
                        "temperature": 32.0,
                        "humidity": 55.0,
                        "area": 1.0,
                        "soil_type": detected_soil
                    }
                })

            # Formulate tailored response based on specific question intent
            if "sandy" in first_query:
                specific_insight = (
                    f"**Recommended Method for Sandy Soil**: Sandy soil has large pore spaces and rapid drainage (permeability factor 1.20x). "
                    f"**Drip irrigation or micro-sprinklers** are best suited. Avoid flood irrigation, as water quickly percolates past the root zone, wasting water and leaching essential fertilizers."
                )
            elif "wastage" in first_query or "reduce" in first_query:
                specific_insight = (
                    "**How to Cut Water Wastage by 30-50%**:\n"
                    "1. **Switch to Micro-Irrigation**: Drip systems achieve 90% application efficiency compared to 45% in open flooding.\n"
                    "2. **Soil Mulching**: 5-10 cm of organic residue or plastic mulch cuts surface evaporation by up to 35%.\n"
                    "3. **Twilight Scheduling**: Irrigate before 8:00 AM or after 6:00 PM to eliminate midday evaporative losses."
                )
            elif "low" in first_query:
                specific_insight = (
                    "**Impact of Low Soil Moisture**:\n"
                    "When moisture drops below critical thresholds, plants experience osmotic shock and stomatal closure to prevent dehydration. "
                    "This halts carbon dioxide uptake and photosynthesis, leading to blossom drop, leaf curling, stunted root growth, and irreversible yield loss."
                )
            elif "productivity" in first_query or "improve" in first_query:
                specific_insight = (
                    "**Actionable Strategies to Improve Crop Productivity**:\n"
                    "1. **Maintain Target Moisture Band**: Prevent cyclic drought and waterlogging swings.\n"
                    "2. **Fertigation**: Inject soluble nitrogen, phosphorus, and potassium directly through drip lines at root level.\n"
                    "3. **Timely Interventions**: Focus irrigation during critical growth stages (crown root initiation for wheat, tasseling for maize, pegging for groundnut)."
                )
            else:
                specific_insight = (
                    f"**Moisture Management for {target_crop.capitalize()}**:\n"
                    f"Ensure soil moisture stays near optimal target threshold. Apply scheduled irrigation in controlled cycles to balance root respiration and water uptake."
                )

            return json.dumps({
                "thought": f"Synthesize agronomic guidance and irrigation recommendations for {target_crop}.",
                "final_answer": (
                    f"**AgriAgent Agronomic Consultation ({target_crop.capitalize()} · ReAct Autonomous Trace)**:\n\n"
                    f"{specific_insight}\n\n"
                    f"**Deterministic Calculation**: Based on the `irrigation_advisor` tool evaluation for {target_crop.capitalize()} in {detected_soil} soil, "
                    f"irrigation priority is determined by moisture deficit, ambient evaporative demand, and soil drainage properties."
                )
            })

        if self.step == 1:
            return '{"thought": "See which data files exist.", "action": "list_files", "args": {}}'
        if self.step == 2:
            return '{"thought": "Check a calculation.", "action": "calculator", "args": {"expression": "2 + 2 * 10"}}'
        return '{"thought": "I have enough.", "final_answer": "Dry run OK: tools executed (list_files, calculator)."}'

