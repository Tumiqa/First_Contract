import requests

try:
    url = 'https://aloo-backend-api.onrender.com/api/admin/withdraw'
    print(f"Testing {url}...")
    headers = {"Content-Type": "application/json"}
    
    # Send empty POST request as payload is not expected
    res = requests.post(url, headers=headers)
    
    print(f"Status Code: {res.status_code}")
    print(f"Response Body: {res.text}")
except Exception as e:
    print(f"Request failed: {e}")
