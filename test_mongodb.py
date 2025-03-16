from mongodb import get_containers, get_items, log_action

# Test fetching containers
print("🚀 Fetching all containers:")
print(get_containers())

# Test fetching items
print("\n📦 Fetching all items:")
print(get_items())

# Test logging an action
print("\n📝 Logging an action:")
log_action("retrieval", "001", {"user": "astronaut1"})
print("✅ Action logged successfully.")