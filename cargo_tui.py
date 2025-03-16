from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static, DataTable
from textual.containers import Container, Horizontal
from backend import get_items, retrieve_cargo, mark_waste

class CargoUI(App):
    """Terminal UI for the Voice-Controlled Cargo Manager"""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("📦 Cargo Management System", classes="title")
        
        # Cargo Table
        self.table = DataTable()
        self.table.add_column("Item ID")
        self.table.add_column("Name")
        self.table.add_column("Status")
        self.load_cargo_data()

        yield self.table

        # Action Buttons
        yield Horizontal(
            Button("Retrieve Item", id="retrieve"),
            Button("Mark as Waste", id="waste"),
            classes="buttons"
        )

        yield Footer()

    def load_cargo_data(self):
        """Load cargo items into the table."""
        self.table.clear()
        items = get_items()  # Fetch items from the database
        for item in items:
            self.table.add_row(item["itemId"], item["name"], item["status"])

    def on_button_pressed(self, event):
        """Handle button clicks."""
        if not self.table.cursor_row:
            return  # No item selected
        
        selected_row = self.table.get_row_at(self.table.cursor_row)
        item_id = selected_row[0]  # First column is Item ID

        if event.button.id == "retrieve":
            retrieve_cargo(item_id)  # Retrieve the item
        elif event.button.id == "waste":
            mark_waste(item_id)  # Mark item as waste

        self.load_cargo_data()  # Refresh table after action

if __name__ == "__main__":
    CargoUI().run()