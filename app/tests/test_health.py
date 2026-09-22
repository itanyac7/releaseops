from src.app import app


def test_health():
    client = app.test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "healthy"}


def test_version_defaults():
    client = app.test_client()
    response = client.get("/api/version")

    assert response.status_code == 200
    assert response.json == {
        "service": "releaseops",
        "version": "0.1.0",
        "environment": "development",
    }

def test_version_uses_runtime_environment_variables(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "0.2.0")
    monkeypatch.setenv("ENVIRONMENT", "staging")

    from src.config import Config

    config = Config()

    assert config.APP_VERSION == "0.2.0"
    assert config.ENVIRONMENT == "staging"

def test_health_returns_503_when_chaos_mode_enabled(monkeypatch):
    monkeypatch.setenv("CHAOS_MODE", "true")

    from src.config import Config

    config = Config()
    assert config.CHAOS_MODE is True

def test_health_endpoint_fails_when_chaos_mode_enabled():
    from src.app import app

    app.config["CHAOS_MODE"] = True

    client = app.test_client()
    response = client.get("/health")

    assert response.status_code == 503
    assert response.json == {"status": "chaos_failure"}

    app.config["CHAOS_MODE"] = False
