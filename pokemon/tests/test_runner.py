import json
import pytest
from django.test import override_settings

@pytest.mark.django_db
def test_runner_rejects_get(client):
    assert client.get("/api/run-tests/").status_code == 405

@pytest.mark.django_db
def test_runner_rejects_unknown_suite(client):
    response = client.post("/api/run-tests/", data=json.dumps({"suite": "arbitrary-command"}),
                           content_type="application/json")
    assert response.status_code == 400

@pytest.mark.django_db
def test_runner_requires_configuration_when_debug_is_false(client, monkeypatch):
    monkeypatch.delenv("POKETEST_RUNNER_ACCESS_CODE", raising=False)
    with override_settings(DEBUG=False):
        response = client.post("/api/run-tests/", data=json.dumps({"suite": "all"}),
                               content_type="application/json")
    assert response.status_code == 503
    assert "not configured" in response.json()["error"].lower()

@pytest.mark.django_db
def test_runner_rejects_incorrect_access_code(client, monkeypatch):
    monkeypatch.setenv("POKETEST_RUNNER_ACCESS_CODE", "test-secret-code")
    with override_settings(DEBUG=False):
        response = client.post("/api/run-tests/",
            data=json.dumps({"suite": "all", "access_code": "wrong"}),
            content_type="application/json")
    assert response.status_code == 403
    assert "incorrect" in response.json()["error"].lower()
