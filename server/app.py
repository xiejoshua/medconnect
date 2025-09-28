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
# Precomputed normalized keywords for fast medical query detection
normalized_keyword_set = set()

def load_data():
    """Load specialist data and topic keywords on startup"""
    global specialists_df, topic_keywords, normalized_keyword_set
    
    try:
        # Try to load parquet file from data folder
        parquet_files = [
            'data/specialists_with_topics_final.parquet'
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
            'data/topic_keywords.json'
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
        
        # Precompute a normalized keyword set for simple medical query checks
        normalized_keyword_set = set()
        try:
            for _, keywords in topic_keywords.items():
                for kw in keywords:
                    nk = normalize_text(kw)
                    if nk:
                        # Add the full phrase and also individual words
                        normalized_keyword_set.add(nk)
                        for w in nk.split():
                            if len(w) > 2:
                                normalized_keyword_set.add(w)
        except Exception as e:
            print(f"Warning: failed to precompute normalized keywords: {e}")
        
        print(f"Successfully loaded {len(specialists_df)} specialists")
        print(f"Found {len(topic_keywords)} topic clusters")
        return True
    except Exception as e:
        print(f"Error loading data: {e}")
        return False

def is_medical_query(query: str) -> bool:
    """Heuristic: determine if the query appears medical by checking against known keywords."""
    if not query:
        return False
    qn = normalize_text(query)
    if not qn:
        return False
    # If any word or the whole query overlaps with our known medical keywords, accept.
    if qn in normalized_keyword_set:
        return True
    for w in qn.split():
        if len(w) > 2 and w in normalized_keyword_set:
            return True
    return False

def normalize_text(text: str) -> str:
    """Normalize text for consistent matching
    
    Handles case insensitivity, punctuation, possessives, and common variations
    in medical terminology like Parkinson's vs Parkinsons.
    """
    import re
    if not isinstance(text, str):
        return ""
        
    # Convert to lowercase and strip
    text = text.lower().strip()
    
    # First, normalize specific medical terms with possessives before general processing
    # This ensures proper handling of conditions like "parkinson's disease"
    text = text.replace("parkinson's", "parkinson")
    text = text.replace("parkinsons", "parkinson")
    text = text.replace("alzheimer's", "alzheimer") 
    text = text.replace("alzheimers", "alzheimer")
    text = text.replace("huntington's", "huntington")
    text = text.replace("huntingtons", "huntington")
    text = text.replace("crohn's", "crohn")
    text = text.replace("crohns", "crohn")
    
    # Handle general apostrophes in possessives and contractions
    text = text.replace("'s", "s")  # general possessives -> plurals
    text = text.replace("'", "")   # Remove remaining apostrophes
    
    # Remove other punctuation and normalize whitespace
    text = re.sub(r"[^\w\s]", " ", text)  # Keep only alphanumeric and whitespace
    text = re.sub(r"\s+", " ", text).strip()  # Normalize multiple spaces
    
    # Handle common medical terminology variations
    text = text.replace("disease", "").replace("diseases", "")
    text = text.replace("syndrome", "").replace("syndromes", "")
    text = text.replace("condition", "").replace("conditions", "")
    text = text.replace("disorder", "").replace("disorders", "")
    
    return text.strip()

def filter_specialists(query: str, location: str = None, max_results: int = 20) -> List[Dict]:
    """Filter specialists based on search criteria"""
    if specialists_df is None:
        return []

    start_time = time.time()

    # Normalize query for better matching
    query_normalized = normalize_text(query)
    query_words = query_normalized.split()
    
    print(f"Debug: Original query: '{query}' -> Normalized: '{query_normalized}' -> Words: {query_words}")

    # Find matching topics first
    matching_topics = []
    topic_relevance_scores = {}
    
    for topic_id, keywords in topic_keywords.items():
        if topic_id == '-1':  # Skip outlier topic
            continue
        
        topic_relevance = 0
        for keyword in keywords:
            keyword_normalized = normalize_text(keyword)
            
            # Multiple levels of matching for better coverage
            if query_normalized == keyword_normalized:
                topic_relevance += 10  # Exact match gets highest score
            elif query_normalized in keyword_normalized or keyword_normalized in query_normalized:
                topic_relevance += 8   # Substring match
            else:
                # Check if any query word matches any keyword word
                query_words_set = set(query_normalized.split())
                keyword_words_set = set(keyword_normalized.split())
                overlap = len(query_words_set.intersection(keyword_words_set))
                if overlap > 0:
                    # Higher weight for more word overlap
                    topic_relevance += overlap * 3
                else:
                    # Check for partial word matches (for medical terms like "parkinson" matching "parkinsonian")
                    for qword in query_words_set:
                        for kword in keyword_words_set:
                            if len(qword) > 3 and len(kword) > 3:  # Only for longer words
                                if qword in kword or kword in qword:
                                    topic_relevance += 1
        
        if topic_relevance > 0:
            try:
                topic_int = int(topic_id)
                matching_topics.append(topic_int)
                topic_relevance_scores[topic_int] = topic_relevance
            except ValueError:
                continue
    
    print(f"Debug: Found {len(matching_topics)} matching topics with scores: {topic_relevance_scores}")

    # Filter by matching topics if found
    if matching_topics:
        filtered_df = specialists_df[specialists_df['topic_cluster'].isin(matching_topics)].copy()
    else:
        filtered_df = specialists_df.copy()

    # Location filtering with normalized comparison
    if location:
        location_norm = normalize_text(location)
        location_mask = (
            filtered_df['state'].fillna('').apply(normalize_text).str.contains(location_norm, na=False) |
            filtered_df['city'].fillna('').apply(normalize_text).str.contains(location_norm, na=False)
        )
        filtered_df = filtered_df[location_mask]

    # Sort by BERTopic relevancy scores (topic-based semantic matching)
    results = filtered_df.copy()
    
    # Add custom relevancy scoring based on topic matching
    if matching_topics and topic_relevance_scores:
        # Create a relevancy score based on topic matching
        def calculate_relevancy(row):
            topic_cluster = row.get('topic_cluster', -1)
            base_relevancy = float(row.get('relevancy_score', 0))
            topic_conf = float(row.get('topic_confidence', 0))
            
            # If this specialist is in a matching topic, boost their score
            if topic_cluster in topic_relevance_scores:
                topic_boost = topic_relevance_scores[topic_cluster] / 10.0  # Normalize
                return base_relevancy + topic_boost + topic_conf
            else:
                return base_relevancy + topic_conf
        
        results['combined_relevancy'] = results.apply(calculate_relevancy, axis=1)
        sort_columns = ['combined_relevancy']
    else:
        # Fallback to existing scores
        sort_columns = []
        if 'relevancy_score' in results.columns:
            sort_columns.append('relevancy_score')
        if 'topic_confidence' in results.columns:
            sort_columns.append('topic_confidence')
    
    # If we found matching topics, we have relevant results
    if len(results) == 0:
        # No matches in topic clusters
        return []
    else:
        if sort_columns:
            results = results.nlargest(max_results, sort_columns)
        else:
            # Fallback if no BERTopic scores available
            results = results.head(max_results)
    
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
                'error': 'Specialist data not loaded',
                'results': []
            }), 500
        
        # Reject clearly non-medical queries early
        invalid_query = not is_medical_query(query)
        if invalid_query:
            return jsonify({
                'success': True,
                'query': query,
                'location': location or None,
                'invalid_query': True,
                'message': 'Your search does not appear to be a medical condition or specialty.',
                'total_results': 0,
                'results': []
            })

        # Perform search
        results = filter_specialists(query, location, max_results)
        if not results:
            return jsonify({
                'success': True,
                'query': query,
                'location': location or None,
                'invalid_query': False,
                'total_results': 0,
                'results': []
            })

        return jsonify({
            'success': True,
            'query': query,
            'location': location or None,
            'invalid_query': False,
            'total_results': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'results': []
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