# pachacutin_ai/app/recommender.py

import time
from pachacutin_ai.config import client
from openai import APIConnectionError, APIError, RateLimitError

def _build_messages(snapshot: dict) -> list:
    soil = snapshot.get("soil_type") or "desconocido"
    sm   = snapshot.get("soil_moisture")
    ah   = snapshot.get("air_humidity")
    tc   = snapshot.get("temperature")

    seeds = snapshot.get("allowed_seeds") or []
    # Nombres “bonitos” para el prompt
    seed_list = "; ".join([f"{s['common']} ({s['latin']})" for s in seeds]) or \
                "Pallar (Phaseolus lunatus); Ají amarillo (Capsicum baccatum); Camote (Ipomoea batatas); Algarrobo (Prosopis pallida)"

    user = (
        "Contexto: Callao (costa del Perú), clima templado costero.\n"
        f"Datos: suelo={soil}, humedad_suelo={sm}%, temperatura={tc}°C, humedad_aire={ah}%.\n"
        "Opciones permitidas (elige EXACTAMENTE UNA): " + seed_list + ".\n"
        "Responde en ESPAÑOL en como máximo 3 líneas:\n"
        "1) Semilla sugerida: <una de la lista>\n"
        "2) Motivo breve (≤12 palabras)\n"
        "3) Riego: pauta concisa"
    )
    return [
        {"role": "system", "content": "Eres un asistente agro práctico, preciso y muy conciso."},
        {"role": "user", "content": user},
    ]

def _fallback_pick(snapshot: dict) -> str:
    """Elige UNA de las 4 semillas y redacta ≤3 líneas."""
    s     = (snapshot.get("soil_type") or "").lower()
    sm    = float(snapshot.get("soil_moisture") or 0)
    tc    = float(snapshot.get("temperature") or 0)

    if "arid" in s or "sand" in s or "arenoso" in s or sm < 30:
        seed = "Algarrobo (huarango)"
        motivo = "Tolera sequía y suelos arenosos"
        riego = "Riego inicial 5–8 L semanal; luego espaciar"
    elif sm > 60:
        seed = "Camote"
        motivo = "Rinde en suelos con buena humedad"
        riego = "0.5–1 L por punto, 2–3 veces/semana"
    elif 18 <= tc <= 28:
        seed = "Ají amarillo"
        motivo = "Se adapta al clima costero templado"
        riego = "0.3–0.5 L, 2 veces/semana; evitar encharque"
    else:
        seed = "Pallar (lima bean)"
        motivo = "Leguminosa costeña, mejora el suelo"
        riego = "0.4–0.6 L, 2 veces/semana"

    return f"Semilla sugerida: {seed}\nMotivo: {motivo}\nRiego: {riego}"

def get_recommendation(snapshot: dict, timeout_s: float) -> dict:
    """
    Devuelve: {"text": str, "source": "openai|fallback", "took_ms": int}
    """
    t0 = time.time()
    try:
        api_timeout = max(5, min(20, int(timeout_s - 3)))
        resp = client.with_options(timeout=api_timeout).chat.completions.create(
            model="gpt-4o-mini",
            messages=_build_messages(snapshot),
            temperature=0.25,
            max_tokens=150,
        )
        text = (resp.choices[0].message.content or "").strip()
        # Seguridad: si el modelo se pasa de largo, recortamos a 3 líneas.
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        text = "\n".join(lines[:3])
        if not text:
            raise RuntimeError("Respuesta vacía")
        return {"text": text, "source": "openai", "took_ms": int((time.time() - t0) * 1000)}
    except (APIConnectionError, APIError, RateLimitError, Exception):
        text = _fallback_pick(snapshot)
        return {"text": text, "source": "fallback", "took_ms": int((time.time() - t0) * 1000)}
