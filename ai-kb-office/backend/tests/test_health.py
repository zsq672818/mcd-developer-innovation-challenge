"""健康检查与接口冒烟测试（G0 准出验证）。"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["api"] == "/api"


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_readiness():
    resp = client.get("/api/health/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] in ("ok", "degraded")
