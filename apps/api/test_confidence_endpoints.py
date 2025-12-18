"""Test confidence scoring API endpoints."""
import requests
import json

BASE_URL = "http://localhost:8000"

# First, let's get a valid token and bot_id
# You'll need to replace these with actual values from your database

def test_query_endpoint():
    """Test the confidence-based query endpoint."""
    
    # Get auth token (replace with your actual credentials)
    print("1. Getting authentication token...")
    auth_response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "email": "test@example.com",  # Replace with real email
            "password": "testpassword"     # Replace with real password
        }
    )
    
    if auth_response.status_code != 200:
        print(f"❌ Auth failed: {auth_response.status_code}")
        print(f"Response: {auth_response.text}")
        print("\nSkipping to direct endpoint test with mock data...")
        test_with_mock_bot()
        return
    
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get list of bots to find a valid bot_id
    print("\n2. Getting list of bots...")
    bots_response = requests.get(f"{BASE_URL}/api/v1/bots", headers=headers)
    
    if bots_response.status_code != 200:
        print(f"❌ Failed to get bots: {bots_response.status_code}")
        print(f"Response: {bots_response.text}")
        return
    
    bots = bots_response.json()
    if not bots:
        print("❌ No bots found. Create a bot first.")
        return
    
    bot_id = bots[0]["id"]
    print(f"✓ Using bot_id: {bot_id}")
    
    # Test the confidence query endpoint
    print("\n3. Testing confidence-based query endpoint...")
    query_data = {
        "query": "What is the company policy on remote work?",
        "confidence_threshold": 0.7,
        "include_sources": True
    }
    
    query_response = requests.post(
        f"{BASE_URL}/api/v1/bots/{bot_id}/query",
        headers=headers,
        json=query_data
    )
    
    print(f"\nStatus Code: {query_response.status_code}")
    print(f"Response:\n{json.dumps(query_response.json(), indent=2)}")
    
    if query_response.status_code == 200:
        response_data = query_response.json()
        
        if response_data.get("status") == "hitl_required":
            print("\n✓ Query routed to HITL (confidence below threshold)")
            print(f"  Query ID: {response_data.get('query_id')}")
            print(f"  Confidence: {response_data.get('confidence', {}).get('overall_confidence')}")
        else:
            print("\n✓ Query auto-sent (confidence above threshold)")
            print(f"  Answer: {response_data.get('answer', '')[:100]}...")
            confidence = response_data.get("confidence_score", {})
            print(f"  Overall Confidence: {confidence.get('overall_confidence')}")
            print(f"  Routing Decision: {response_data.get('routing_info', {}).get('decision')}")


def test_with_mock_bot():
    """Test endpoint structure without auth."""
    print("\n🔍 Testing endpoint availability...")
    
    # Try to access docs
    docs_response = requests.get(f"{BASE_URL}/docs")
    if docs_response.status_code == 200:
        print("✓ API docs available at http://localhost:8000/docs")
    
    # Try to access openapi.json to see registered endpoints
    openapi_response = requests.get(f"{BASE_URL}/openapi.json")
    if openapi_response.status_code == 200:
        openapi_data = openapi_response.json()
        paths = openapi_data.get("paths", {})
        
        # Check if our new endpoints are registered
        query_endpoint = "/api/v1/bots/{bot_id}/query"
        stream_endpoint = "/api/v1/bots/{bot_id}/query/stream"
        
        if query_endpoint in paths:
            print(f"✓ Endpoint registered: POST {query_endpoint}")
            print(f"  Methods: {list(paths[query_endpoint].keys())}")
        else:
            print(f"❌ Endpoint NOT found: {query_endpoint}")
            
        if stream_endpoint in paths:
            print(f"✓ Endpoint registered: POST {stream_endpoint}")
            print(f"  Methods: {list(paths[stream_endpoint].keys())}")
        else:
            print(f"❌ Endpoint NOT found: {stream_endpoint}")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Confidence Scoring API Endpoints")
    print("=" * 60)
    
    try:
        test_query_endpoint()
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
