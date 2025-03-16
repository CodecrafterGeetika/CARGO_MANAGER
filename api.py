from flask import Flask, request, jsonify
from backend import add_cargo, search_cargo, retrieve_cargo, mark_waste, get_waste_items, log_action
from mongodb import get_containers, get_items

app = Flask(__name__)

### ✅ **API: Add Cargo**
@app.route('/api/add', methods=['POST'])
def api_add():
    """API to add cargo items."""
    data = request.json
    if not all(key in data for key in ["id", "name", "width", "depth", "height", "mass", "priority", "expiry", "usage", "zone"]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    add_cargo(
        data["id"], data["name"], data["width"], data["depth"],
        data["height"], data["mass"], data["priority"], data["expiry"], data["usage"], data["zone"]
    )
    log_action("add", data["id"], {"name": data["name"]})
    return jsonify({"success": True, "message": f"{data['name']} added to {data['zone']}"}), 200

### ✅ **API: Search Cargo**
@app.route('/api/search', methods=['GET'])
def api_search():
    """API to search for an item."""
    name = request.args.get("name")
    if not name:
        return jsonify({"success": False, "message": "Item name is required"}), 400

    result = search_cargo(name)
    return jsonify({"success": True, "data": result}), 200

### ✅ **API: Retrieve Cargo**
@app.route('/api/retrieve', methods=['POST'])
def api_retrieve():
    """API to retrieve an item."""
    data = request.json
    if "id" not in data:
        return jsonify({"success": False, "message": "Item ID is required"}), 400

    result = retrieve_cargo(data["id"])
    if result:
        log_action("retrieve", data["id"], {"new_usesLeft": result["new_usesLeft"]})
        return jsonify({"success": True, "message": f"Item {data['id']} retrieved", "usesLeft": result["new_usesLeft"]}), 200
    return jsonify({"success": False, "message": "Item not found"}), 404

### ✅ **API: Mark Waste**
@app.route('/api/waste', methods=['POST'])
def api_waste():
    """API to mark an item as waste."""
    data = request.json
    if "id" not in data:
        return jsonify({"success": False, "message": "Item ID is required"}), 400

    result = mark_waste(data["id"])
    if result:
        log_action("waste", data["id"], {"status": "waste"})
        return jsonify({"success": True, "message": f"Item {data['id']} marked as waste"}), 200
    return jsonify({"success": False, "message": "Item not found"}), 404

### ✅ **API: Get All Waste Items**
@app.route('/api/waste/items', methods=['GET'])
def api_get_waste_items():
    """API to retrieve all waste items."""
    result = get_waste_items()
    return jsonify({"success": True, "data": result}), 200

### ✅ **API: Fetch All Containers**
@app.route('/api/containers', methods=['GET'])
def api_get_containers():
    """API to get all containers."""
    result = get_containers()
    return jsonify({"success": True, "data": result}), 200

### ✅ **API: Fetch All Items**
@app.route('/api/items', methods=['GET'])
def api_get_items():
    """API to get all items."""
    result = get_items()
    return jsonify({"success": True, "data": result}), 200

### ✅ **API: Fetch Logs**
@app.route('/api/logs', methods=['GET'])
def api_get_logs():
    """API to get all logs."""
    action_type = request.args.get("actionType")
    query = {} if not action_type else {"actionType": action_type}
    
    
    from mongodb import logs_collection
    logs = list(logs_collection.find(query, {"_id": 0}))  # Fetch logs without MongoDB _id
    return jsonify({"success": True, "data": logs}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)