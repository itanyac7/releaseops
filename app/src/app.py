from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def home():
    return jsonify(
        {
            "service": "releaseops",
            "message": "DevOps showcase API",
        }
    )


@app.get("/health")
def health():
    return jsonify({"status": "healthy"})


@app.get("/api/version")
def version():
    return jsonify(
        {
            "service": "releaseops",
            "version": "0.1.0",
            "environment": "development",
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)