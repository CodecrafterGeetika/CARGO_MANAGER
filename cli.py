import click
import requests
import json

API_URL = "http://127.0.0.1:8000/api"  # Update this if the API is running on another port

@click.group()
def cli():
    """🚀 Cargo Management System for ISS"""
    pass

### ✅ **Helper Function to Handle API Requests Safely**
def send_request(method, endpoint, data=None, params=None):
    """Handles API requests with error handling."""
    try:
        url = f"{API_URL}/{endpoint}"
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError("Invalid HTTP method")

        # ✅ Ensure the API returned a success response
        if response.status_code != 200:
            return {"success": False, "message": f"❌ Error {response.status_code}: {response.text}"}

        return response.json()
    
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "❌ Error: Unable to connect to API. Is Flask running?"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"❌ API request failed: {str(e)}"}

### ✅ **Add Cargo**
@cli.command()
@click.option('--id', required=True, help='Item ID')
@click.option('--name', required=True, help='Item Name')
@click.option('--width', required=True, type=int, help='Item Width (cm)')
@click.option('--depth', required=True, type=int, help='Item Depth (cm)')
@click.option('--height', required=True, type=int, help='Item Height (cm)')
@click.option('--mass', required=True, type=int, help='Item Mass (kg)')
@click.option('--priority', required=True, type=int, help='Item Priority (1-100)')
@click.option('--expiry', required=True, help='Expiry Date (YYYY-MM-DD)')
@click.option('--usage', required=True, type=int, help='Usage Limit')
@click.option('--zone', required=True, help='Preferred Zone')
def add(id, name, width, depth, height, mass, priority, expiry, usage, zone):
    """➕ Add new cargo item"""
    data = {
        "id": id, "name": name, "width": width, "depth": depth,
        "height": height, "mass": mass, "priority": priority,
        "expiry": expiry, "usage": usage, "zone": zone
    }

    response = send_request("POST", "add", data=data)
    click.echo(response["message"])

### ✅ **Search Cargo**
@cli.command()
@click.option('--name', required=True, help='Item Name')
def search(name):
    """🔍 Search for an item"""
    response = send_request("GET", "search", params={"name": name})

    if response.get("success"):
        for item in response.get("data", []):
            click.echo(json.dumps(item, indent=2))
    else:
        click.echo(response["message"])

### ✅ **Retrieve Cargo**
@cli.command()
@click.option('--id', required=True, help='Item ID')
def retrieve(id):
    """📦 Retrieve an item"""
    response = send_request("POST", "retrieve", data={"id": id})
    click.echo(response["message"])

### ✅ **Mark Cargo as Waste**
@cli.command()
@click.option('--id', required=True, help='Item ID')
def waste(id):
    """🚮 Mark an item as waste"""
    response = send_request("POST", "waste", data={"id": id})
    click.echo(response["message"])

### ✅ **View Logs**
@cli.command()
@click.option('--action', required=False, help='Filter logs by action type (e.g., retrieval, add, waste)')
def logs(action):
    """📜 Fetch and display logs from API"""
    
    response = send_request("GET", "logs", params={"actionType": action} if action else None)

    if not response.get("success"):
        click.echo(response["message"])
        return

    logs = response.get("data", [])
    if not logs:
        click.echo("📜 No logs available.")
        return

    # ✅ Display logs in a readable format
    for log in logs:
        click.echo(f"📝 {log['timestamp']} | {log['actionType'].upper()} | Item ID: {log['itemId']}")
        click.echo(f"   ➡ Details: {json.dumps(log['details'], indent=2)}\n")

if __name__ == '__main__':
    cli()