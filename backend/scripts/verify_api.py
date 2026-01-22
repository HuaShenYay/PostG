import requests
import json

try:
    print("Testing /api/visual/stats...")
    # Note: Assumes server is running. If not, this will fail.
    # If it fails, I'll know I should maybe start it or I can just test the function directly by importing app.
    
    # Method 2: Import app and test directly (safer if server not running)
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from app import app, db
    
    with app.app_context():
        # Mock request
        with app.test_client() as client:
            rv = client.get('/api/visual/stats')
            data = rv.get_json()
            
            print("Status Code:", rv.status_code)
            
            radar = data.get('radar_data', {})
            indicators = radar.get('indicator', [])
            values = radar.get('value', [])
            
            print("Radar Indicators:", [i['name'] for i in indicators])
            print("Radar Values:", values)
            
            # Check for new keys
            has_ping = any('Ping' in i['name'] or '平' in i['name'] for i in indicators)
            has_ze = any('Ze' in i['name'] or '仄' in i['name'] for i in indicators)
            
            if has_ping and has_ze:
                print("SUCCESS: Found Ping/Ze rhythm data in response.")
            else:
                print("FAILURE: Did not find Ping/Ze data.")

except Exception as e:
    print(f"Error: {e}")
