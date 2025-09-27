from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Keep CORS enabled for common local dev hosts; adjust when deploying or locking down origins.
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"])


@app.route('/api/search')
def search():
    """Placeholder search endpoint.

    Returns an empty list while the real data import / clustering pipeline is being prepared.
    Do not add seed data here — import will populate a database or index later.
    """
    # intentionally return an empty array for now
    return jsonify([])


@app.route('/health')
def health():
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
