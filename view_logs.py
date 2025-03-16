import requests
import json

# Fetch logs from API
response = requests.get("http://127.0.0.1:8000/api/logs")
logs = response.json()["data"]

# Print logs in a readable format
for log in logs:
    print(f"📝 {log['timestamp']} | {log['actionType'].upper()} | Item ID: {log['itemId']}")
    print(f"   ➡ Details: {json.dumps(log['details'], indent=2)}\n")