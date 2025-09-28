from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import json
import os
import time
import re
from typing import List, Dict, Any, Tuple

app = Flask(__name__)
CORS(app)

# Global variables for data
specialists_df = None
topic_keywords = None

def is_valid_medical_query(query):
    """Filter out nonsensical or inappropriate search terms"""
    if not query or len(query.strip()) < 3:
        return False
    
    # List of non-medical terms to reject
    invalid_terms = [
        'skibidi', 'gyatt', 'sigma', 'rizz', 'ohio', 'sus', 'amogus',
        'test', 'asdf', 'qwerty', '123', 'hello', 'hi', 'yo'
    ]
    
    query_lower = query.lower().strip()
    
    # Reject if query is just invalid slang
    if query_lower in invalid_terms:
        return False
    
    # Check if it's mostly random characters
    if len(set(query_lower)) < len(query_lower) * 0.4:
        return False
    
    # Reject obvious gibberish patterns
    gibberish_patterns = [
        r'(.)\1{3,}',  # Same character repeated 4+ times
        r'^[aeiou]+$',  # Just vowels
        r'^[bcdfg-z]+$',  # Just consonants
        r'[qxz]{2,}',   # Multiple rare letters
    ]
    
    for pattern in gibberish_patterns:
        if re.search(pattern, query_lower):
            return False
    
    return True

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

def normalize_text(text: str) -> str:
    """Normalize text for consistent matching"""
    if not isinstance(text, str):
        return ""
    
    text = text.lower().strip()
    text = text.replace("'s", "s")  # parkinson's -> parkinsons
    text = text.replace("'", "")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    
    return text

def score_clusters_by_query(query: str, topic_keywords: Dict) -> List[Tuple]:
    """
    Score each cluster based on how well its keywords match the query.
    Returns list of (cluster_id, score, matching_keywords)
    """
    query_norm = normalize_text(query)
    query_words = set(query_norm.split())
    
    cluster_scores = []
    
    for cluster_id, keywords in topic_keywords.items():
        if cluster_id == '-1':  # Skip outlier cluster
            continue
            
        score = 0
        matching_keywords = []
        
        for keyword in keywords:
            keyword_norm = normalize_text(keyword)
            keyword_words = set(keyword_norm.split())
            
            # Exact match gets highest score
            if query_norm == keyword_norm:
                score += 10
                matching_keywords.append((keyword, 10))
            # Query is contained in keyword
            elif query_norm in keyword_norm:
                score += 7
                matching_keywords.append((keyword, 7))
            # Keyword is contained in query
            elif keyword_norm in query_norm:
                score += 5
                matching_keywords.append((keyword, 5))
            # Word overlap scoring
            else:
                overlap = query_words & keyword_words
                if overlap:
                    overlap_score = len(overlap) * 2 / max(len(query_words), len(keyword_words))
                    score += overlap_score
                    if overlap_score > 0.5:
                        matching_keywords.append((keyword, overlap_score))
        
        if score > 0:
            cluster_scores.append((int(cluster_id), score, matching_keywords))
    
    cluster_scores.sort(key=lambda x: x[1], reverse=True)
    return cluster_scores

def get_weighted_keywords(top_clusters: List[Tuple], topic_keywords: Dict, query: str) -> Dict[str, float]:
    """
    Extract and weight keywords from top clusters
    """
    weighted_keywords = {}
    query_norm = normalize_text(query)
    
    for cluster_rank, (cluster_id, cluster_score, matching_keywords) in enumerate(top_clusters):
        # Cluster weight decreases with rank
        cluster_weight = 1.0 - (cluster_rank * 0.1)
        
        # Get all keywords for this cluster
        all_cluster_keywords = topic_keywords.get(str(cluster_id), [])
        
        # Score each keyword
        keyword_scores = []
        for kw in all_cluster_keywords:
            kw_norm = normalize_text(kw)
            
            # Calculate keyword-query similarity
            if query_norm == kw_norm:
                kw_score = 1.0
            elif query_norm in kw_norm or kw_norm in query_norm:
                kw_score = 0.8
            else:
                query_words = set(query_norm.split())
                kw_words = set(kw_norm.split())
                overlap = query_words & kw_words
                kw_score = len(overlap) / max(len(query_words), len(kw_words)) if overlap else 0.1
            
            keyword_scores.append((kw, kw_score))
        
        # Sort and keep top 50%
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        cutoff = max(5, len(keyword_scores) // 2)
        top_keywords = keyword_scores[:cutoff]
        
        # Add to weighted keywords
        for kw, kw_score in top_keywords:
            position = all_cluster_keywords.index(kw) if kw in all_cluster_keywords else len(all_cluster_keywords)
            position_weight = 1.0 - (position / len(all_cluster_keywords)) * 0.3
            
            final_weight = cluster_weight * kw_score * position_weight
            
            if kw in weighted_keywords:
                weighted_keywords[kw] = max(weighted_keywords[kw], final_weight)
            else:
                weighted_keywords[kw] = final_weight
    
    return weighted_keywords

def filter_specialists(query: str, location: str = None, max_results: int = 20) -> List[Dict]:
    """Advanced filtering with cluster-based relevancy scoring"""
    if specialists_df is None or topic_keywords is None:
        return []
    
    start_time = time.time()
    
    # Step 1: Score all clusters and get top 10
    cluster_scores = score_clusters_by_query(query, topic_keywords)
    top_clusters = cluster_scores[:10]
    
    if not top_clusters:
        # No matching clusters, fallback to basic search
        return []
    
    # Step 2: Get weighted keywords from top clusters
    weighted_keywords = get_weighted_keywords(top_clusters, topic_keywords, query)
    
    # Step 3: Filter specialists by location first
    if location:
        location_norm = normalize_text(location)
        filtered_df = specialists_df[
            specialists_df['state'].fillna('').apply(normalize_text).str.contains(location_norm, na=False) |
            specialists_df['city'].fillna('').apply(normalize_text).str.contains(location_norm, na=False)
        ].copy()
    else:
        filtered_df = specialists_df.copy()
    
    # Step 4: Score specialists based on weighted keywords
    specialist_scores = []
    
    for idx, row in filtered_df.iterrows():
        score = 0
        
        # Define field importance weights
        profile_fields = {
            'rare_diseases_treated': 1.5,
            'research_interests': 1.2,
            'clinical_focus': 1.0,
            'specialty': 0.8,
            'subspecialty': 0.6
        }
        
        for field_name, field_weight in profile_fields.items():
            field_text = normalize_text(str(row.get(field_name, '')))
            if not field_text:
                continue
            
            # Check each weighted keyword
            for keyword, kw_weight in weighted_keywords.items():
                keyword_norm = normalize_text(keyword)
                
                if keyword_norm in field_text:
                    match_quality = 1.0 if keyword_norm == field_text else 0.8
                    contribution = kw_weight * field_weight * match_quality
                    score += contribution
        
        # Bonus for being in a top cluster
        specialist_cluster = row.get('topic_cluster', -1)
        cluster_ids = [c[0] for c in top_clusters]
        if specialist_cluster in cluster_ids:
            cluster_rank = cluster_ids.index(specialist_cluster)
            score += (10 - cluster_rank) * 0.5
        
        # Include existing relevancy score
        if 'relevancy_score' in row and pd.notna(row['relevancy_score']):
            score += float(row['relevancy_score']) * 0.3
        
        if score > 0:
            specialist_scores.append((idx, score))
    
    # Sort by score and get top results
    specialist_scores.sort(key=lambda x: x[1], reverse=True)
    top_specialist_indices = [idx for idx, _ in specialist_scores[:max_results]]
    
    if not top_specialist_indices:
        return []
    
    results_df = filtered_df.loc[top_specialist_indices]
    
    search_time = (time.time() - start_time) * 1000
    print(f"Advanced search for '{query}' completed in {search_time:.1f}ms, found {len(results_df)} results")
    
    # Format results
    formatted_results = []
    for idx in top_specialist_indices:
        row = filtered_df.loc[idx]
        score = next(s for i, s in specialist_scores if i == idx)
        
        specialist = {
            'id': str(idx),
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
                'total_score': round(score, 2),
                'search_score': round(score, 2),
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
        
        # Validate medical query
        if not is_valid_medical_query(query):
            return jsonify({
                'success': False,
                'error': 'Please enter a valid medical condition or disease name',
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