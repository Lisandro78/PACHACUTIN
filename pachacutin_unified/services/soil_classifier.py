# -*- coding: utf-8 -*-
"""
Clasificador de tipo de suelo (placeholder).
Conecta aquí tu modelo real luego. Por ahora usa brillo promedio.
"""
def classify_soil_from_bgr_image(img_bgr) -> str:
    if img_bgr is None:
        return "Desconocido"
    import cv2
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    mean = float(gray.mean())
    if mean < 60:
        return "Arcilloso"
    elif mean < 120:
        return "Franco"
    elif mean < 180:
        return "Arenoso"
    else:
        return "Gravoso"
