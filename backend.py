from database import items_collection, logs_collection  # Ensure db is imported
from datetime import datetime
import pymongo

def add_cargo(item_id, name, width, depth, height, mass, priority, expiry, usage, zone):
    """
    Add a new cargo item to the inventory.
    """
    if items_collection.find_one({"itemId": item_id}):
        return {"success": False, "message": "❌ Error: Item ID already exists!"}

    new_item = {
        "itemId": item_id,
        "name": name,
        "width": width,
        "depth": depth,
        "height": height,
        "mass": mass,
        "priority": priority,
        "expiry": expiry,
        "usage": usage,
        "preferredZone": zone,
        "status": "available"
    }

    items_collection.insert_one(new_item)
    log_action("add", item_id, {"name": name, "zone": zone})
    return {"success": True, "message": f"✅ {name} added to {zone}"}

def get_items():
    """Fetch all cargo items from the database."""
    items = list(items_collection.find({}, {"_id": 0}))  # Exclude MongoDB ObjectId
    return {"success": True, "data": [serialize_item(item) for item in items]}

def search_cargo(name):
    """
    Search for cargo items by name.
    """
    items = list(items_collection.find({"name": {"$regex": name, "$options": "i"}}, {"_id": 0}))
    return {"success": True, "data": [serialize_item(item) for item in items]}

def retrieve_cargo(item_id):
    """
    Retrieve an item from the inventory.
    """
    item = items_collection.find_one({"itemId": item_id})
    if not item:
        return {"success": False, "message": "❌ Item not found!"}

    if item["status"] == "waste":
        return {"success": False, "message": "🚮 Item is marked as waste and cannot be retrieved."}

    new_usage = max(0, item["usage"] - 1)
    update_data = {"usage": new_usage}

    if new_usage == 0:
        update_data["status"] = "waste"
        log_action("waste", item_id, {"status": "waste"})
    else:
        log_action("retrieve", item_id, {"new_usage": new_usage})

    items_collection.update_one({"itemId": item_id}, {"$set": update_data})
    return {"success": True, "message": f"📦 Item {item_id} retrieved. Remaining usage: {new_usage}", "new_usesLeft": new_usage}

def mark_waste(item_id):
    """
    Mark an item as waste.
    """
    item = items_collection.find_one({"itemId": item_id})
    if not item:
        return {"success": False, "message": "❌ Item not found!"}

    items_collection.update_one({"itemId": item_id}, {"$set": {"status": "waste"}})
    log_action("waste", item_id, {"status": "waste"})
    return {"success": True, "message": f"🚮 Item {item_id} marked as waste"}

def get_waste_items():
    """Retrieve all items marked as waste."""
    waste_items = list(items_collection.find({"status": "waste"}, {"_id": 0}))  
    return {"success": True, "data": [serialize_item(item) for item in waste_items]}

def log_action(action_type, item_id, details):
    """
    Log actions like add, retrieve, or waste.
    """
    if "logs" not in db.list_collection_names():
        db.create_collection("logs")  # Ensure logs collection exists

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "actionType": action_type,
        "itemId": item_id,
        "details": details or {}
    }

    db["logs"].insert_one(log_entry)  
    return {"success": True, "message": f"📝 Action '{action_type}' logged for Item {item_id}"}

def serialize_item(item):
    """
    Convert MongoDB item format into a readable format.
    """
    return {key: str(value) if isinstance(value, pymongo.ObjectId) else value for key, value in item.items()}