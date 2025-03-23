from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
import time

# MongoDB connection with retry mechanism
def get_mongodb_connection(max_retries=3, retry_delay=2):
    """Establish MongoDB connection with retry mechanism."""
    retries = 0
    while retries < max_retries:
        try:
            client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
            # Test the connection
            client.admin.command('ismaster')
            return client
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            retries += 1
            if retries >= max_retries:
                raise Exception(f"Failed to connect to MongoDB after {max_retries} attempts: {str(e)}")
            print(f"Connection attempt {retries} failed. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

# Initialize database connection
try:
    client = get_mongodb_connection()
    db = client["space_station"]
    containers_collection = db["containers"]
    items_collection = db["items"]
    logs_collection = db["logs"]

    # Ensure indexes for faster queries
    containers_collection.create_index("containerId", unique=True)
    items_collection.create_index("itemId", unique=True)
    print("✅ Successfully connected to MongoDB and created indexes")
except Exception as e:
    print(f"🚨 Failed to initialize MongoDB: {str(e)}")
    # Set up dummy collections for error handling
    class DummyCollection:
        def find(self, *args, **kwargs): return []
        def find_one(self, *args, **kwargs): return None
        def update_one(self, *args, **kwargs): return type('obj', (object,), {'matched_count': 0})
        def insert_one(self, *args, **kwargs): pass
        def create_index(self, *args, **kwargs): pass
    
    containers_collection = DummyCollection()
    items_collection = DummyCollection()
    logs_collection = DummyCollection()

def get_containers():
    """Fetch all containers from the database."""
    try:
        containers = list(containers_collection.find({}, {"_id": 0}))  # Exclude MongoDB _id
        print(f"Fetched {len(containers)} containers")
        return containers
    except Exception as e:
        print(f"🚨 Error fetching containers: {str(e)}")
        return []

def get_container_by_id(container_id):
    """Fetch a specific container by ID."""
    try:
        container = containers_collection.find_one({"containerId": container_id}, {"_id": 0})
        print(f"Fetched container by ID {container_id}: {'Found' if container else 'Not found'}")
        return container
    except Exception as e:
        print(f"🚨 Error fetching container {container_id}: {str(e)}")
        return None

def update_container(container):
    """Update a container's data in the database."""
    try:
        if "containerId" not in container:
            print("🚨 Container ID missing in update request")
            return False
            
        result = containers_collection.update_one(
            {"containerId": container["containerId"]},
            {"$set": container}
        )
        success = result.matched_count > 0
        print(f"Updated container {container['containerId']}: {'Success' if success else 'Failed - not found'}")
        return success
    except Exception as e:
        print(f"🚨 Error updating container: {str(e)}")
        return False

def get_items():
    """Fetch all items from the database."""
    try:
        items = list(items_collection.find({}, {"_id": 0}))  # Exclude MongoDB _id
        print(f"Fetched {len(items)} items")
        return items
    except Exception as e:
        print(f"🚨 Error fetching items: {str(e)}")
        return []

def get_item_by_id(item_id):
    """Fetch a specific item by its ID."""
    try:
        item = items_collection.find_one({"itemId": item_id}, {"_id": 0})
        print(f"Fetched item by ID {item_id}: {'Found' if item else 'Not found'}")
        return item
    except Exception as e:
        print(f"🚨 Error fetching item {item_id}: {str(e)}")
        return None

def update_item(item_id, updates):
    """Update item attributes in the database."""
    try:
        result = items_collection.update_one(
            {"itemId": item_id},
            {"$set": updates}
        )
        success = result.matched_count > 0
        print(f"Updated item {item_id}: {'Success' if success else 'Failed - not found'}")
        return success
    except Exception as e:
        print(f"🚨 Error updating item {item_id}: {str(e)}")
        return False

def mark_item_as_waste(item_id, reason="Expired"):
    """Mark an item as waste."""
    try:
        result = update_item(item_id, {"status": "waste", "wasteReason": reason})
        print(f"Marked item {item_id} as waste: {'Success' if result else 'Failed'}")
        return result
    except Exception as e:
        print(f"🚨 Error marking item {item_id} as waste: {str(e)}")
        return False

def get_waste_items():
    """Retrieve all items marked as waste."""
    try:
        waste_items = list(items_collection.find({"status": "waste"}, {"_id": 0}))
        print(f"Fetched {len(waste_items)} waste items")
        return waste_items
    except Exception as e:
        print(f"🚨 Error fetching waste items: {str(e)}")
        return []

def log_action(action_type, item_id, details=None):
    """Log an action in the system."""
    try:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "actionType": action_type,
            "itemId": item_id,
            "details": details or {}
        }
        logs_collection.insert_one(log_entry)
        print(f"Logged action: {action_type} for item {item_id}")
        return log_entry
    except Exception as e:
        print(f"🚨 Error logging action: {str(e)}")
        return None