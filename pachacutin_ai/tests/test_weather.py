from pachacutin_ai.app.weather_reader import get_weather


def test_weather():
    """Probar que el API del clima devuelve datos válidos."""
    data = get_weather()
    print("🌤️ Datos recibidos del API de clima:", data)

    # Validar que no haya error
    assert "error" not in data

    # Validar que existan los campos esperados
    assert "temperatura" in data
    assert "humedad_aire" in data
