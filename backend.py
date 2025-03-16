from pymongo.errors import DuplicateKeyError
from mongodb import items_collection, logs_collection
from datetime import datetime

### ✅ **Add Cargo (Handles Duplicates)**
def add_cargo(id, name, width, depth, height, mass, priority, expiry, usage, zone):
    """Add a new cargo item to MongoDB, preventing duplicates."""
    cargo_item = {
        "itemId": id,
        "name": name,
        "width": width,
        "depth": depth,
        "height": height,
        "mass": mass,
        "priority": priority,
        "expiry": expiry,
        "usage": usage,
        "zone": zone,
        "status": "available"
    }
    
    try:
        items_collection.insert_one(cargo_item)
        log_action("add", id, {"name": name, "zone": zone})
        print(f"✅ Item {id} added successfully!")
        return {"success": True, "message": f"Item {id} added successfully!"}
    except DuplicateKeyError:
        print(f"🚨 Item with ID {id} already exists in the database!")
        return {"success": False, "message": f"Item {id} already exists!"}

### ✅ **Search Cargo**
def search_cargo(name):
    """Search for cargo by name."""
    results = list(items_collection.find({"name": {"$regex": name, "$options": "i"}}, {"_id": 0}))
    if results:
        return results
    else:
        return {"message": "No items found."}

### ✅ **Retrieve Cargo (Decreases Usage Count)**
def retrieve_cargo(id):
    """Retrieve an item and decrease its usage count."""
    item = items_collection.find_one({"itemId": id})
    
    if not item:
        return None  # Item not found
    
    if item["usage"] > 0:
        new_usage = item["usage"] - 1
        items_collection.update_one({"itemId": id}, {"$set": {"usage": new_usage}})
        log_action("retrieve", id, {"new_usage": new_usage})
        return {"itemId": id, "new_usesLeft": new_usage}
    else:
        return {"message": f"Item {id} has no remaining uses."}

### ✅ **Mark Cargo as Waste**
def mark_waste(id):
    """Mark an item as waste if it's expired or has no usage left."""
    item = items_collection.find_one({"itemId": id})
    
    if not item:
        return None  # Item not found
    
    items_collection.update_one({"itemId": id}, {"$set": {"status": "waste"}})
    log_action("waste", id, {"status": "waste"})
    return {"message": f"Item {id} marked as waste."}

### ✅ **Fetch All Waste Items**
def get_waste_items():
    """Retrieve all waste items."""
    return list(items_collection.find({"status": "waste"}, {"_id": 0}))

### ✅ **Log System Actions (Stores Logs in MongoDB)**
def log_action(action_type, item_id, details=None):
    """Log an action in the system."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "actionType": action_type,
        "itemId": item_id,
        "details": details or {}
    }
    logs_collection.insert_one(log_entry)  # ✅ Ensure logs are stored properly
    return log_entry