from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import json
import re

app = Flask(__name__)
CORS(app)

# Load data on startup
specialists_df = None
topic_info = None

def load_data():
    global specialists_df, topic_info
    try:
        # Get the directory where this script is located
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load specialists data
        parquet_path = os.path.join(script_dir, 'data', 'specialists_with_topics_final.parquet')
        specialists_df = pd.read_parquet(parquet_path)
        print(f"Loaded {len(specialists_df)} specialists")
        
        # Load topic information
        topic_path = os.path.join(script_dir, 'data', 'clustering key', 'topic_info.json')
        with open(topic_path, 'r') as f:
            topic_info = json.load(f)
        print(f"Loaded {len(topic_info)} topics")
        
        return True
    except Exception as e:
        print(f"Error loading data: {e}")
        return False



@app.route('/', methods=['GET'])
def home():
    print("Home route accessed")
    return jsonify({"message": "Backend is running!", "data_loaded": specialists_df is not None})

@app.route('/api/search', methods=['GET'])
def search_specialists():
    print(f"Search route accessed with args: {request.args}")
    query = request.args.get('query', '').strip()
    
    if not query:
        return jsonify([])
    
    if specialists_df is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    specialists = filter_specialists(query)
    
    return jsonify(specialists)

@app.route('/api/topics', methods=['GET'])
def get_topics():
    """Debug endpoint to see available topics"""
    print(f"Topics route accessed with args: {request.args}")
    query = request.args.get('query', '').strip()
    
    if not query:
        return jsonify([])
    
    relevant_topics = search_relevant_topics(query)
    return jsonify(relevant_topics)

if __name__ == '__main__':
    print("Loading data...")
    if load_data():
        print("Data loaded successfully!")
        print("Starting Flask server on http://localhost:5002")
        app.run(host='127.0.0.1', port=5002, debug=True)
    else:
        print("Failed to load data. Please check file paths.")
        exit(1)
