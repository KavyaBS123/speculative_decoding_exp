from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_run_experiment():
    r = client.post("/api/experiment/run", json={"random_seed": 1, "num_requests": 2, "output_tokens_per_request": 32})
    assert r.status_code == 200
    body = r.json()
    assert "results" in body
    assert "standard" in body["results"]
    assert body["meta"]["disclaimer"].startswith("SIMULATED")


def test_invalid_config_rejected():
    r = client.post("/api/experiment/run", json={"base_acceptance": 2.0})
    assert r.status_code == 422
