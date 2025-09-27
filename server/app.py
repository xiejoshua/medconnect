from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import json
import os
import time
from typing import List, Dict, Any

app = Flask(__name__)
CORS(app)

# Global variables for data
specialists_df = None
topic_keywords = None

def load_data():
    """Load specialist data and topic keywords on startup"""
    global specialists_df, topic_keywords
    
    try:
        # Try to load parquet file from data folder
        parquet_files = [
            'data/specialists_final_with_npi.parquet',
            'data/specialists_with_topics_final.parquet', 
            'data/npi_enhanced_specialists.parquet',
            'data/main_dataset.parquet'  # From your drive download folder
        ]
        
        for filename in parquet_files:
            if os.path.exists(filename):
                print(f"Loading specialists from {filename}...")
                specialists_df = pd.read_parquet(filename)
                break
        
        if specialists_df is None:
            print("Warning: No parquet file found. Search will not work.")
            return False
        
        # Load topic keywords from data folder
        topic_files = [
            'data/topic_keywords.json',
            'data/disease_tracking.json'  # Alternative location
        ]
        for filename in topic_files:
            if os.path.exists(filename):
                print(f"Loading topic keywords from {filename}...")
                with open(filename, 'r') as f:
                    topic_keywords = json.load(f)
                break
        
        if topic_keywords is None:
            print("Warning: No topic keywords found. Search will be slower.")
            topic_keywords = {}
        
        print(f"Successfully loaded {len(specialists_df)} specialists")
        print(f"Found {len(topic_keywords)} topic clusters")
        return True
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return False

def filter_specialists(query: str, location: str = None, max_results: int = 20) -> List[Dict]:
    """Filter specialists based on search criteria"""
    if specialists_df is None:
        return []
    
    start_time = time.time()
    
    # Find matching topics first
    matching_topics = []
    query_lower = query.lower()
    
    for topic_id, keywords in topic_keywords.items():
        if topic_id == '-1':  # Skip outlier topic
            continue
        for keyword in keywords:
            if query_lower in keyword.lower() or keyword.lower() in query_lower:
                try:
                    matching_topics.append(int(topic_id))
                    break
                except ValueError:
                    continue
    
    # Filter by matching topics if found
    if matching_topics:
        filtered_df = specialists_df[specialists_df['topic_cluster'].isin(matching_topics)].copy()
    else:
        filtered_df = specialists_df.copy()
    
    # Location filtering
    if location:
        location_lower = location.lower()
        location_mask = (
            filtered_df['state'].str.lower().str.contains(location_lower, na=False) |
            filtered_df['city'].str.lower().str.contains(location_lower, na=False)
        )
        filtered_df = filtered_df[location_mask]
    
    # Text-based scoring
    scores = []
    for _, row in filtered_df.iterrows():
        score = 0
        text_fields = [
            str(row.get('rare_diseases_treated', '')),
            str(row.get('research_interests', '')),
            str(row.get('specialty', '')),
            str(row.get('clinical_focus', ''))
        ]
        
        for field in text_fields:
            field_lower = field.lower()
            if query_lower in field_lower:
                score += 2  # Exact substring match
            # Check for partial word matches
            query_words = query_lower.split()
            for word in query_words:
                if word in field_lower:
                    score += 1
        
        scores.append(score)
    
    filtered_df['search_score'] = scores
    
    # Sort by score, then by relevancy score
    results = filtered_df[filtered_df['search_score'] > 0].copy()
    if len(results) == 0:
        # Fallback - return top specialists from filtered set
        if 'relevancy_score' in filtered_df.columns:
            results = filtered_df.nlargest(max_results, 'relevancy_score')
        else:
            results = filtered_df.head(max_results)
    else:
        sort_columns = ['search_score']
        if 'relevancy_score' in results.columns:
            sort_columns.append('relevancy_score')
        results = results.nlargest(max_results, sort_columns)
    
    search_time = (time.time() - start_time) * 1000
    print(f"Search for '{query}' completed in {search_time:.1f}ms, found {len(results)} results")
    
    # Format results for API response
    formatted_results = []
    for _, row in results.head(max_results).iterrows():
        specialist = {
            'id': str(row.name),  # Use DataFrame index as ID
            'name': f"{row.get('first_name', '')} {row.get('last_name', '')}".strip(),
            'first_name': row.get('first_name', ''),
            'last_name': row.get('last_name', ''),
            'hospital': row.get('hospital_affiliation', 'N/A'),
            'specialty': row.get('rare_diseases_treated', 'N/A'),
            'research_interests': row.get('research_interests', 'N/A'),
            'location': {
                'city': row.get('city', ''),
                'state': row.get('state', ''),
                'country': row.get('country', '')
            },
            'contact': {
                'email': row.get('email', ''),
                'phone': row.get('phone', '') or row.get('verified_phone', ''),
                'website': row.get('website', '')
            },
            'scores': {
                'search_score': int(row.get('search_score', 0)),
                'relevancy_score': float(row.get('relevancy_score', 0)),
                'topic_confidence': float(row.get('topic_confidence', 0))
            },
            'topic_cluster': int(row.get('topic_cluster', -1)),
            'npi': row.get('npi', ''),
            'verified_data': {
                'city': row.get('verified_city', ''),
                'state': row.get('verified_state', ''),
                'phone': row.get('verified_phone', ''),
                'specialty': row.get('verified_specialty', '')
            }
        }
        formatted_results.append(specialist)
    
    return formatted_results

@app.route('/api/specialists/search', methods=['GET'])
def search_specialists():
    """Search for specialists based on query parameters"""
    try:
        # Get query parameters
        query = request.args.get('q', '').strip()
        location = request.args.get('location', '').strip()
        max_results = min(int(request.args.get('limit', 20)), 50)  # Cap at 50 results
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter "q" is required',
                'results': []
            }), 400
        
        if specialists_df is None:
            return jsonify({
                'success': False,
                'error': 'Specialist data not loaded',
                'results': []
            }), 500
        
        # Perform search
        results = filter_specialists(query, location, max_results)
        
        return jsonify({
            'success': True,
            'query': query,
            'location': location or None,
            'total_results': len(results),
            'results': results
        })
        
    except Exception as e:
        print(f"Error in search_specialists: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'results': []
        }), 500

@app.route('/api/specialties', methods=['GET'])
def get_specialties():
    """Get list of all available specialties"""
    try:
        if specialists_df is None:
            return jsonify({
                'success': False,
                'error': 'Specialist data not loaded',
                'specialties': []
            }), 500
        
        # Get unique rare diseases treated
        all_diseases = []
        for diseases in specialists_df['rare_diseases_treated'].dropna():
            if pd.notna(diseases) and diseases:
                # Split on common delimiters
                disease_list = str(diseases).replace(';', ',').replace('|', ',').split(',')
                for disease in disease_list:
                    disease = disease.strip()
                    if disease and disease not in all_diseases:
                        all_diseases.append(disease)
        
        # Sort alphabetically
        all_diseases.sort()
        
        return jsonify({
            'success': True,
            'total_specialties': len(all_diseases),
            'specialties': all_diseases[:100]  # Limit to first 100 for performance
        })
        
    except Exception as e:
        print(f"Error in get_specialties: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'specialties': []
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dataset statistics"""
    try:
        if specialists_df is None:
            return jsonify({
                'success': False,
                'error': 'Specialist data not loaded'
            }), 500
        
        stats = {
            'total_specialists': len(specialists_df),
            'topic_clusters': int(specialists_df['topic_cluster'].nunique()),
            'us_specialists': len(specialists_df[specialists_df['country'].str.upper() == 'UNITED STATES']) if 'country' in specialists_df.columns else 0,
            'with_npi': int(specialists_df['npi'].notna().sum()) if 'npi' in specialists_df.columns else 0,
            'with_contact_info': int((specialists_df['email'].notna() | specialists_df['phone'].notna()).sum()),
            'top_topics': []
        }
        
        # Get top 5 topic clusters
        topic_counts = specialists_df['topic_cluster'].value_counts().head(5)
        for topic, count in topic_counts.items():
            topic_info = {
                'topic_id': int(topic),
                'specialist_count': int(count),
                'keywords': topic_keywords.get(str(topic), [])[:5]  # First 5 keywords
            }
            stats['top_topics'].append(topic_info)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"Error in get_stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Legacy endpoint for backward compatibility
@app.route('/api/search')
def search():
    """Legacy search endpoint - redirects to new specialist search"""
    query = request.args.get('query', request.args.get('q', ''))
    if query:
        # Redirect to new endpoint with proper parameters
        return search_specialists()
    else:
        return jsonify([])  # Return empty array for backward compatibility

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "data_loaded": specialists_df is not None,
        "specialists_count": len(specialists_df) if specialists_df is not None else 0,
        "topics_loaded": len(topic_keywords) if topic_keywords else 0
    })

if __name__ == '__main__':
    # Load specialists data on startup
    print("Loading specialist data...")
    if load_data():
        print("✅ Data loaded successfully! Starting Flask server...")
    else:
        print("❌ Failed to load data. Server will start but search won't work.")
    
    app.run(host='0.0.0.0', port=8000, debug=True)