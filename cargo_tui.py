from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Button, DataTable, Label, Input
import requests
import json

API_URL = "http://127.0.0.1:8000/api"  # Ensure your Flask API is running
def show_items():
    try:
        from backend import get_items  # Import inside function to avoid circular import
        items = get_items()
        print(items)  
    except Exception as e:
        print(f"❌ Error fetching items: {e}")   
class CargoManagerTUI(App):
    """🚀 Interactive Cargo Manager for ISS"""

    CSS = """
    Screen {
        align: center middle;
    }
    Button {
        width: 30;
        height: 3;
        margin: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("📦 Cargo Management System", id="title"),
            Horizontal(
                Button("🔍 View Cargo", id="view"),
                Button("➕ Add Cargo", id="add"),
                Button("📦 Retrieve Cargo", id="retrieve"),
                Button("🚮 Mark Waste", id="waste"),
                Button("📜 View Logs", id="logs"),
            ),
            DataTable(id="data_table"),
            Footer(),
        )

    async def on_mount(self):
        self.table = self.query_one("#data_table", DataTable)
        self.table.add_columns("Item ID", "Name", "Zone", "Priority", "Status")

    async def on_button_pressed(self, event: Button.Pressed):
        """Handles button clicks"""
        if event.button.id == "view":
            await self.update_table("items")  # ✅ Fetch items correctly
        elif event.button.id == "add":
            await self.add_cargo()
        elif event.button.id == "retrieve":
            await self.retrieve_cargo()
        elif event.button.id == "waste":
            await self.mark_waste()
        elif event.button.id == "logs":
            await self.update_table("logs")  # ✅ Fetch logs correctly

    async def update_table(self, mode: str):
        """Fetch and update table with cargo or logs"""
        self.table.clear()
        endpoint = "logs" if mode == "logs" else "items"  # ✅ Correct API endpoint
        response = requests.get(f"{API_URL}/{endpoint}").json()

        if response.get("success"):
            for item in response.get("data", []):
                if mode == "logs":
                    self.table.add_row(
                        item["timestamp"], item["actionType"],
                        item["itemId"], json.dumps(item["details"])
                    )
                else:
                    self.table.add_row(
                        item["itemId"], item["name"], item["preferredZone"],
                        str(item["priority"]), item.get("status", "available")
                    )

    async def add_cargo(self):
        """Prompt user to add a cargo item"""
        id_input = Input("Enter Item ID:")
        name_input = Input("Enter Item Name:")
        zone_input = Input("Enter Preferred Zone:")

        await self.push_screen(id_input)
        await self.push_screen(name_input)
        await self.push_screen(zone_input)

        data = {
            "id": id_input.value, "name": name_input.value, "width": 10,
            "depth": 10, "height": 10, "mass": 5, "priority": 50,
            "expiry": "2026-01-01", "usage": 10, "zone": zone_input.value
        }

        response = requests.post(f"{API_URL}/add", json=data).json()
        self.notify(response.get("message", "Cargo Added!"), severity="info")

    async def retrieve_cargo(self):
        """Prompt user to retrieve a cargo item"""
        id_input = Input("Enter Item ID to Retrieve:")
        await self.push_screen(id_input)

        response = requests.post(f"{API_URL}/retrieve", json={"id": id_input.value}).json()
        self.notify(response.get("message", "Item Retrieved!"), severity="success")

    async def mark_waste(self):
        """Prompt user to mark an item as waste"""
        id_input = Input("Enter Item ID to Mark as Waste:")
        await self.push_screen(id_input)

        response = requests.post(f"{API_URL}/waste", json={"id": id_input.value}).json()
        self.notify(response.get("message", "Item Marked as Waste!"), severity="warning")

if __name__ == "__main__":
    CargoManagerTUI().run()
