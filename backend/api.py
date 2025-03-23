from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import csv
import io
from database import (
    db, 
    items_collection, 
    logs_collection, 
    containers_collection,
    log_action,
    mark_item_as_waste,
    get_waste_items
)
from placement import SpatialPlacement
from retrieve import RetrievalSystem
import uuid

app = FastAPI(title="ISS Cargo Management System")

# Initialize core systems
placement_system = SpatialPlacement()
retrieval_system = RetrievalSystem()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

### ✅ Data Models
class ItemRequest(BaseModel):
    itemId: str
    name: str
    width: float
    depth: float
    height: float
    mass: float
    priority: int
    expiryDate: Optional[str] = None
    usageLimit: int
    preferredZone: str

class ContainerRequest(BaseModel):
    containerId: str
    zone: str
    width: float
    depth: float
    height: float
    maxWeight: float

class RetrievalRequest(BaseModel):
    itemId: str
    userId: str

class SimulationRequest(BaseModel):
    numDays: int
    itemsUsedPerDay: List[str]

### ✅ Core API Endpoints
@app.post("/api/placement", response_model=dict)
async def optimize_placement():
    """Handle placement optimization with uploaded data"""
    try:
        # Get all available items and containers
        items = list(items_collection.find({"status": "pending"}, {"_id": 0}))
        containers = list(containers_collection.find({}, {"_id": 0}))

        if not items:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "No items to place"}
            )

        # Run placement optimization
        result = placement_system.find_optimal_placement(items)
        
        if not result["success"]:
            return JSONResponse(
                status_code=400,
                content=result
            )

        # Update database with placements
        for placement in result["placements"]:
            items_collection.update_one(
                {"itemId": placement["itemId"]},
                {"$set": {
                    "status": "stored",
                    "position": placement["position"],
                    "containerId": placement["containerId"]
                }}
            )

        return JSONResponse(content=result)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Placement error: {str(e)}"}
        )

@app.get("/api/search", response_model=dict)
async def search_item(
    itemName: str = Query(..., min_length=1),
    userId: Optional[str] = None
):
    """Find optimal item to retrieve"""
    try:
        item = retrieval_system.find_optimal_item(itemName)
        if not item:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Item not found"}
            )

        # Get retrieval path
        path = retrieval_system.get_retrieval_path(item["itemId"])
        
        # Log search action
        log_action(
            action_type="search",
            item_id=item["itemId"],
            user_id=userId,
            details={
                "name": itemName,
                "retrievalSteps": len(path["steps"])
            }
        )

        return JSONResponse(content={
            "success": True,
            "item": item,
            "retrievalSteps": path["steps"]
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Search error: {str(e)}"}
        )

@app.post("/api/retrieve", response_model=dict)
async def retrieve_item(request: RetrievalRequest):
    """Execute item retrieval"""
    try:
        # Validate item exists
        item = items_collection.find_one({"itemId": request.itemId})
        if not item:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Item not found"}
            )

        # Execute retrieval
        success = retrieval_system.execute_retrieval(
            item["itemId"],
            request.userId
        )
        
        if not success:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Retrieval failed"}
            )

        # Update usage count
        new_usage = item["usageLimit"] - 1
        update_data = {
            "usageLimit": new_usage,
            "lastAccessed": datetime.utcnow()
        }

        if new_usage <= 0:
            mark_item_as_waste(item["itemId"], "Usage exhausted")
            update_data["status"] = "waste"

        items_collection.update_one(
            {"itemId": request.itemId},
            {"$set": update_data}
        )

        return JSONResponse(content={
            "success": True,
            "remainingUses": new_usage
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Retrieval error: {str(e)}"}
        )

@app.post("/api/simulate/day", response_model=dict)
async def simulate_time(request: SimulationRequest):
    """Advance simulation time"""
    try:
        current_date = datetime.utcnow()
        
        for day in range(request.numDays):
            # Process daily usage
            for item_id in request.itemsUsedPerDay:
                items_collection.update_one(
                    {"itemId": item_id},
                    {"$inc": {"usageLimit": -1}}
                )

            # Check expirations
            items_collection.update_many(
                {"expiryDate": {"$lt": current_date}},
                {"$set": {"status": "waste"}}
            )

            current_date += timedelta(days=1)

        # Update system date
        db.metadata_collection.update_one(
            {"_id": "system_date"},
            {"$set": {"value": current_date}},
            upsert=True
        )

        return JSONResponse(content={
            "success": True,
            "newDate": current_date.isoformat()
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Simulation error: {str(e)}"}
        )

@app.get("/api/waste/identify", response_model=dict)
async def identify_waste():
    """List all waste items"""
    try:
        waste_items = get_waste_items()
        return JSONResponse(content={
            "success": True,
            "wasteItems": waste_items
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Waste identification error: {str(e)}"}
        )

### ✅ Data Import/Export Endpoints
@app.post("/api/import/items")
async def import_items(file: UploadFile = File(...)):
    """Import items from CSV"""
    try:
        contents = await file.read()
        decoded = contents.decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))
        
        imported = 0
        errors = []
        
        for idx, row in enumerate(reader, start=1):
            try:
                # Validate required fields
                required = ["Item ID", "Name", "Width", "Depth", "Height"]
                if not all(field in row for field in required):
                    raise ValueError("Missing required fields")

                # Create item document
                item = {
                    "itemId": row["Item ID"],
                    "name": row["Name"],
                    "width": float(row["Width"]),
                    "depth": float(row["Depth"]),
                    "height": float(row["Height"]),
                    "mass": float(row.get("Mass", 0)),
                    "priority": int(row.get("Priority", 50)),
                    "expiryDate": row.get("Expiry Date"),
                    "usageLimit": int(row.get("Usage Limit", 1)),
                    "preferredZone": row.get("Preferred Zone", "General"),
                    "status": "pending"
                }

                items_collection.insert_one(item)
                imported += 1
            
            except Exception as e:
                errors.append({"row": idx, "message": str(e)})

        return JSONResponse(content={
            "success": True,
            "imported": imported,
            "errors": errors
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Import error: {str(e)}"}
        )

@app.get("/api/export/arrangement")
async def export_arrangement():
    """Export current arrangement as CSV"""
    try:
        items = items_collection.find({"status": "stored"})
        
        csv_data = "Item ID,Container ID,Start W,Start D,Start H,End W,End D,End H\n"
        for item in items:
            pos = item.get("position", {})
            start = pos.get("startCoordinates", {})
            end = pos.get("endCoordinates", {})
            
            csv_data += (
                f"{item['itemId']},"
                f"{item.get('containerId', 'N/A')},"
                f"{start.get('width', 0)},"
                f"{start.get('depth', 0)},"
                f"{start.get('height', 0)},"
                f"{end.get('width', 0)},"
                f"{end.get('depth', 0)},"
                f"{end.get('height', 0)}\n"
            )

        return JSONResponse(content={
            "success": True,
            "csvData": csv_data
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Export error: {str(e)}"}
        )

### ✅ UI Endpoints
@app.get("/", include_in_schema=False)
async def serve_ui():
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)