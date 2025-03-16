from pymongo import MongoClient
from datetime import datetime
# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["space_station"]
containers_collection = db["containers"]
items_collection = db["items"]
logs_collection = db["logs"]

# Ensure indexes for faster queries
containers_collection.create_index("containerId", unique=True)
items_collection.create_index("itemId", unique=True)

def get_containers():
    """Fetch all containers from the database."""
    containers = list(containers_collection.find())
    print(f"Fetched containers: {containers}")
    return containers

def get_container_by_id(container_id):
    """Fetch a specific container by ID."""
    container = containers_collection.find_one({"containerId": container_id})
    print(f"Fetched container by ID {container_id}: {container}")
    return container

def update_container(container):
    """Update a container's data in the database."""
    result = containers_collection.update_one(
        {"containerId": container["containerId"]},
        {"$set": container}
    )
    print(f"Updated container {container['containerId']}: {result.matched_count > 0}")
    return result.matched_count > 0  # Returns True if update was successful

def get_items():
    """Fetch all items from the database."""
    items = list(items_collection.find())
    print(f"Fetched items: {items}")
    return items

def get_item_by_id(item_id):
    """Fetch a specific item by its ID."""
    item = items_collection.find_one({"itemId": item_id})
    print(f"Fetched item by ID {item_id}: {item}")
    return item

def update_item(item_id, updates):
    """Update item attributes in the database."""
    result = items_collection.update_one(
        {"itemId": item_id},
        {"$set": updates}
    )
    print(f"Updated item {item_id} with {updates}: {result.matched_count > 0}")
    return result.matched_count > 0

def mark_item_as_waste(item_id, reason="Expired"):
    """Mark an item as waste."""
    result = update_item(item_id, {"status": "waste", "wasteReason": reason})
    print(f"Marked item {item_id} as waste for reason '{reason}': {result}")
    return result

def get_waste_items():
    """Retrieve all items marked as waste."""
    waste_items = list(items_collection.find({"status": "waste"}))
    print(f"Fetched waste items: {waste_items}")
    return waste_items

def log_action(action_type, item_id, details=None):
    """Log an action in the system."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "actionType": action_type,
        "itemId": item_id,
        "details": details or {}
    }
    logs_collection.insert_one(log_entry)
    print(f"Logged action: {log_entry}")
    return log_entry