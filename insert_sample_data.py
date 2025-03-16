from mongodb import containers_collection, items_collection

# Sample containers
containers = [
    {"containerId": "contA", "zone": "Crew Quarters", "width": 100, "depth": 85, "height": 200, "items": []},
    {"containerId": "contB", "zone": "Airlock", "width": 50, "depth": 85, "height": 200, "items": []}
]

# Sample items
items = [
    {"itemId": "001", "name": "Food Packet", "width": 10, "depth": 10, "height": 20, "priority": 80, "preferredZone": "Crew Quarters", "status": "available"},
    {"itemId": "002", "name": "Oxygen Cylinder", "width": 15, "depth": 15, "height": 50, "priority": 95, "preferredZone": "Airlock", "status": "available"}
]

# Insert data into MongoDB
containers_collection.insert_many(containers)
items_collection.insert_many(items)

print("✅ Sample data inserted successfully!")