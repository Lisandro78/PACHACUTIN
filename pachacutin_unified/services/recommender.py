# -*- coding: utf-8 -*-
from pachacutin_unified.config import OPENAI_API_KEY, OPENAI_MODEL

def rule_based_rec(payload: dict) -> str:
    soil = (payload.get("soil_type") or "").lower()
    hum  = int(payload.get("soil_moisture") or 0)
    temp = float(payload.get("temperature") or 0)
    if "aren" in soil and 25 <= temp <= 35 and hum >= 30:
        return "Siembra algarrobo; suelo arenoso con buena temperatura y humedad."
    if hum < 20:
        return "Riega primero; la humedad del suelo es muy baja para sembrar."
    if "arcill" in soil:
        return "Siembra molle costeño; tolera suelos arcillosos."
    return "Siembra huarango o faique; condiciones generales aceptables."

def openai_rec(payload: dict) -> str:
    if not OPENAI_API_KEY:
        return rule_based_rec(payload)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        content = (
            "Eres un asistente agrícola. Con los siguientes datos sugiere UNA sola semilla a sembrar "
            "en costa árida del Perú (Callao), y una breve razón (≤15 palabras). "
            f"Datos: soil_type={payload.get('soil_type')}, soil_moisture={payload.get('soil_moisture')}%, "
            f"air_humidity={payload.get('air_humidity')}%, temperature={payload.get('temperature')}°C."
        )
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role":"system","content":"Eres un agrónomo experto."},
                      {"role":"user","content":content}],
            temperature=0.2,
            max_tokens=70,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return rule_based_rec(payload)

def get_recommendation(payload: dict) -> str:
    return openai_rec(payload)
