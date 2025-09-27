from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from typing import List, Dict, Any

app = Flask(__name__)
# Keep CORS enabled for common local dev hosts; adjust when deploying or locking down origins.
CORS(app)


def filter_specialists():
    

@app.route('/api/specialists/search', methods=['GET'])
def search_specialists():
    """Search for specialists based on query parameters"""


@app.route('/api/specialties', methods=['GET'])
def get_specialties():
    """Get list of all available specialties"""




# Legacy endpoint for backward compatibility
@app.route('/api/search')
def search():
    """Legacy search endpoint - redirects to new specialist search"""
    query = request.args.get('q', '')
    return search_specialists()


if __name__ == '__main__':
    # Load specialists data on startup
    app.run(host='0.0.0.0', port=8000, debug=True)
