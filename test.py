from backend import place_item, can_fit, rearrange_container, add_item_to_container, remove_item_from_container

def test_rearrangement():
    items = [
        {
            "itemId": "001",
            "name": "Food Packet",
            "width": 10,
            "depth": 10,
            "height": 20,
            "priority": 80,
            "preferredZone": "Crew Quarters"
        },
        {
            "itemId": "002",
            "name": "Oxygen Cylinder",
            "width": 15,
            "depth": 15,
            "height": 50,
            "priority": 95,
            "preferredZone": "Airlock"
        }
    ]
    
    containers = [
        {
            "containerId": "contA",
            "zone": "Crew Quarters",
            "width": 100,
            "depth": 85,
            "height": 200,
            "items": [
                {
                    "itemId": "003",
                    "name": "First Aid Kit",
                    "width": 20,
                    "depth": 20,
                    "height": 10,
                    "priority": 70,
                    "preferredZone": "Crew Quarters"
                }
            ]
        },
        {
            "containerId": "contB",
            "zone": "Airlock",
            "width": 50,
            "depth": 85,
            "height": 200,
            "items": []
        }
    ]

    # 🔹 Place the first item (Food Packet)
    placed_container_id = place_item(items[0], containers)
    
    # Ensure the first item is placed in a valid container
    assert placed_container_id in ["contA", "contB"], (
        f"🚨 ERROR: Food Packet should be placed in contA or contB, but got {placed_container_id}"
    )

    print(f"✅ Food Packet placed successfully in {placed_container_id}")

    # Debug: Print container state after placing the first item
    print("📦 After placing Food Packet:")
    for container in containers:
        print(f"➡ Container {container['containerId']} Items: {container['items']}")

    # 🔹 Place the second item (Oxygen Cylinder, requires rearrangement)
    placed_container_id = place_item(items[1], containers)

    # Debug: Print container state after attempting to place the second item
    print("📦 After attempting to place Oxygen Cylinder:")
    for container in containers:
        print(f"➡ Container {container['containerId']} Items: {container['items']}")

    # Ensure the item is placed in a valid container
    if placed_container_id is None:
        raise AssertionError("🚨 ERROR: Oxygen Cylinder could not be placed in any container!")

    assert placed_container_id in ["contA", "contB"], (
        f"🚨 ERROR: Oxygen Cylinder should be placed in contA or contB after rearrangement, but got {placed_container_id}"
    )

    print(f"✅ Oxygen Cylinder placed successfully in {placed_container_id}")

    print("🎉 All tests passed successfully!")

# Run the test
test_rearrangement()