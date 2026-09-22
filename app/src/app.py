from flask import Flask, jsonify

from src.config import Config

app = Flask(__name__)

config = Config()
app.config.from_mapping(
    SERVICE_NAME=config.SERVICE_NAME,
    APP_VERSION=config.APP_VERSION,
    ENVIRONMENT=config.ENVIRONMENT,
    CHAOS_MODE=config.CHAOS_MODE,
)

@app.get("/")
def home():
    return jsonify(
        {
            "service": app.config["SERVICE_NAME"],
            "message": "DevOps showcase API",
        }
    )


@app.get("/health")
def health():
    if app.config.get("CHAOS_MODE", False):
        return jsonify({"status": "chaos_failure"}), 503

    return jsonify({"status": "healthy"})


@app.get("/api/version")
def version():
    return jsonify(
        {
            "service": app.config["SERVICE_NAME"],
            "version": app.config["APP_VERSION"],
            "environment": app.config["ENVIRONMENT"],
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
