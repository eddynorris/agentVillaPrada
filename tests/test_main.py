"""
Tests para endpoints FastAPI y Webhooks de Villa Prada.
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_cotizar():
    payload = {
        "tipo_evento": "boda",
        "paquete": "premium",
        "nro_invitados": 120,
        "horas_extras": 1
    }
    response = client.post("/api/cotizar", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["nro_invitados"] == 120
    assert data["precio_unitario_pax"] == 120.0
    assert data["horas_extras_monto"] == 300.0
    assert data["total_general"] == 14700.0


def test_webhook_whatsapp_simulacion():
    payload = {
        "phone": "987654321",
        "message": "Hola, quiero cotizar un quinceañero para 150 personas"
    }
    response = client.post("/webhook/whatsapp", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["reply"]) > 0
