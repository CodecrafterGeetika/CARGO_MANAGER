from mongodb import get_containers, get_container_by_id, update_container, get_items, get_item_by_id, update_item, mark_item_as_waste, get_waste_items, log_action

# Test the functions
get_containers()
get_container_by_id("contA")
update_container({"containerId": "contA", "zone": "Crew Quarters", "width": 100, "depth": 85, "height": 200, "items": []})
get_items()
get_item_by_id("001")
update_item("001", {"name": "Updated Item"})
mark_item_as_waste("001", "Expired")
get_waste_items()
log_action("test_action", "001", {"detail": "test detail"})