from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Button, DataTable, Label, Input, Static
import requests
import json

API_URL = "http://127.0.0.1:8000/api"  # Ensure your Flask API is running

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
    Input {
        width: 30;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the UI layout"""
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
            Static(id="form_area"),  # Input area for prompts
            Footer(),
        )

    async def on_mount(self):
        """Setup UI elements when the app starts"""
        self.table = self.query_one("#data_table", DataTable)
        self.table.add_columns("Item ID", "Name", "Zone", "Priority", "Status")

    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button clicks"""
        print(f"🔘 Button Clicked: {event.button.id}")  # Debugging Clicks

        if event.button.id == "view":
            await self.update_table("items")
        elif event.button.id == "add":
            await self.show_add_form()  # Show input form for adding cargo
        elif event.button.id == "retrieve":
            await self.show_retrieve_form()  # Show input form for retrieving cargo
        elif event.button.id == "waste":
            await self.show_waste_form()  # Show input form for marking waste
        elif event.button.id == "logs":
            await self.update_table("logs")

    async def update_table(self, mode: str):
        """Fetch and update table with cargo or logs"""
        print(f"📡 Fetching {mode}...")  # Debugging
        self.table.clear()
        endpoint = "logs" if mode == "logs" else "items"
        try:
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
                            item["itemId"], item["name"], item.get("preferredZone", "Unknown"),
                            str(item["priority"]), item.get("status", "available")
                        )
            else:
                self.notify("❌ Failed to fetch data!", severity="error")
        except Exception as e:
            self.notify(f"❌ Error: {str(e)}", severity="error")

    async def show_add_form(self):
        """Show input form for adding cargo"""
        form = self.query_one("#form_area", Static)
        form.update(
            "Enter Cargo Details:\n"
            "Item ID: [Press Enter]\n"
            "Item Name: [Press Enter]\n"
            "Zone: [Press Enter]\n"
        )

        id_input = Input(placeholder="Enter Item ID", id="add_id")
        name_input = Input(placeholder="Enter Item Name", id="add_name")
        zone_input = Input(placeholder="Enter Zone", id="add_zone")

        form.mount(id_input, name_input, zone_input, Button("Submit", id="submit_add"))
        self.query_one("#submit_add").on("click", self.add_cargo)

    async def add_cargo(self):
        """Handle adding cargo"""
        id_input = self.query_one("#add_id").value
        name_input = self.query_one("#add_name").value
        zone_input = self.query_one("#add_zone").value

        if not id_input or not name_input or not zone_input:
            self.notify("❌ Missing required fields!", severity="error")
            return

        data = {
            "id": id_input, "name": name_input, "width": 10,
            "depth": 10, "height": 10, "mass": 5, "priority": 50,
            "expiry": "2026-01-01", "usage": 10, "zone": zone_input
        }

        try:
            response = requests.post(f"{API_URL}/add", json=data).json()
            self.notify(response.get("message", "✅ Cargo Added!"), severity="info")
            await self.update_table("items")  # Refresh table
        except Exception as e:
            self.notify(f"❌ Error: {str(e)}", severity="error")

    async def show_retrieve_form(self):
        """Show input form for retrieving cargo"""
        form = self.query_one("#form_area", Static)
        form.update("Enter Item ID to Retrieve:")

        id_input = Input(placeholder="Enter Item ID", id="retrieve_id")
        form.mount(id_input, Button("Submit", id="submit_retrieve"))
        self.query_one("#submit_retrieve").on("click", self.retrieve_cargo)

    async def retrieve_cargo(self):
        """Handle retrieving cargo"""
        id_input = self.query_one("#retrieve_id").value

        if not id_input:
            self.notify("❌ Item ID required!", severity="error")
            return

        try:
            response = requests.post(f"{API_URL}/retrieve", json={"id": id_input}).json()
            if response.get("success"):
                self.notify(response.get("message", "📦 Item Retrieved!"), severity="success")
            else:
                self.notify(response.get("message", "❌ Item Not Found!"), severity="error")
            await self.update_table("items")
        except Exception as e:
            self.notify(f"❌ Error: {str(e)}", severity="error")

    async def show_waste_form(self):
        """Show input form for marking cargo as waste"""
        form = self.query_one("#form_area", Static)
        form.update("Enter Item ID to Mark as Waste:")

        id_input = Input(placeholder="Enter Item ID", id="waste_id")
        form.mount(id_input, Button("Submit", id="submit_waste"))
        self.query_one("#submit_waste").on("click", self.mark_waste)

    async def mark_waste(self):
        """Handle marking an item as waste"""
        id_input = self.query_one("#waste_id").value

        if not id_input:
            self.notify("❌ Item ID required!", severity="error")
            return

        try:
            response = requests.post(f"{API_URL}/waste", json={"id": id_input}).json()
            if response.get("success"):
                self.notify(response.get("message", "🚮 Item Marked as Waste!"), severity="warning")
            else:
                self.notify(response.get("message", "❌ Item Not Found!"), severity="error")
            await self.update_table("items")
        except Exception as e:
            self.notify(f"❌ Error: {str(e)}", severity="error")

if __name__ == "__main__":
    CargoManagerTUI().run()