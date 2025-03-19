class Item:
    def __init__(self, item_id, name, width, depth, height, mass, priority, expiry_date, usage_limit, preferred_zone):
        self.item_id = item_id
        self.name = name
        self.width = width
        self.depth = depth
        self.height = height
        self.mass = mass
        self.priority = priority
        self.expiry_date = expiry_date  # datetime object
        self.usage_limit = usage_limit
        self.preferred_zone = preferred_zone
        self.remaining_uses = usage_limit
        self.is_waste = False
        
    def mark_as_used(self):
        if self.remaining_uses > 0:
            self.remaining_uses -= 1
            if self.remaining_uses == 0:
                self.is_waste = True
        return self.remaining_uses
    
    def check_expiry(self, current_date):
        if self.expiry_date and current_date > self.expiry_date:
            self.is_waste = True
            return True
        return False
    
    # For 3D rotation possibilities
    def get_possible_orientations(self):
        # Return all 6 possible orientations (width, depth, height)
        return [
            (self.width, self.depth, self.height),
            (self.width, self.height, self.depth),
            (self.depth, self.width, self.height),
            (self.depth, self.height, self.width),
            (self.height, self.width, self.depth),
            (self.height, self.depth, self.width)
        ]


class Position:
    def __init__(self, start_width, start_depth, start_height, end_width, end_depth, end_height):
        self.start_coordinates = {"width": start_width, "depth": start_depth, "height": start_height}
        self.end_coordinates = {"width": end_width, "depth": end_depth, "height": end_height}
    
    def overlaps(self, other_position):
        # Check if this position overlaps with another position
        return not (
            self.end_coordinates["width"] <= other_position.start_coordinates["width"] or
            self.start_coordinates["width"] >= other_position.end_coordinates["width"] or
            self.end_coordinates["depth"] <= other_position.start_coordinates["depth"] or
            self.start_coordinates["depth"] >= other_position.end_coordinates["depth"] or
            self.end_coordinates["height"] <= other_position.start_coordinates["height"] or
            self.start_coordinates["height"] >= other_position.end_coordinates["height"]
        )
    
    def is_visible_from_open_face(self, container_depth):
        # An item is visible if it touches the open face (depth = 0)
        return self.start_coordinates["depth"] == 0
    
    def volume(self):
        return (
            (self.end_coordinates["width"] - self.start_coordinates["width"]) *
            (self.end_coordinates["depth"] - self.start_coordinates["depth"]) *
            (self.end_coordinates["height"] - self.start_coordinates["height"])
        )


class Container:
    def __init__(self, container_id, zone, width, depth, height):
        self.container_id = container_id
        self.zone = zone
        self.width = width
        self.depth = depth
        self.height = height
        self.items = {}  # item_id -> (item, position)
        
        # Efficient data structure for tracking space usage
        # This is a 3D grid representation for quick collision detection
        # In a real implementation, we might use a more sophisticated spatial index
        self.space_grid = {}  # (x, y, z) -> item_id for occupied spaces
        
        # For quick retrieval path calculation
        self.depth_profile = {}  # (width, height) -> max_depth
        
    def can_fit(self, item, position):
        # Check if item can fit at the given position
        # 1. Within container bounds
        if (position.end_coordinates["width"] > self.width or
            position.end_coordinates["depth"] > self.depth or
            position.end_coordinates["height"] > self.height):
            return False
            
        # 2. No overlap with existing items
        for existing_item_id, (_, existing_position) in self.items.items():
            if position.overlaps(existing_position):
                return False
                
        return True
    
    def place_item(self, item, position):
        self.items[item.item_id] = (item, position)
        
        # Update space grid and depth profile
        for w in range(position.start_coordinates["width"], position.end_coordinates["width"]):
            for d in range(position.start_coordinates["depth"], position.end_coordinates["depth"]):
                for h in range(position.start_coordinates["height"], position.end_coordinates["height"]):
                    self.space_grid[(w, d, h)] = item.item_id
                    
        # Update depth profile for retrieval calculations
        for w in range(position.start_coordinates["width"], position.end_coordinates["width"]):
            for h in range(position.start_coordinates["height"], position.end_coordinates["height"]):
                current_depth = self.depth_profile.get((w, h), 0)
                self.depth_profile[(w, h)] = max(current_depth, position.end_coordinates["depth"])
    
    def remove_item(self, item_id):
        if item_id not in self.items:
            return None
            
        item, position = self.items[item_id]
        del self.items[item_id]
        
        # Update space grid and depth profile
        for w in range(position.start_coordinates["width"], position.end_coordinates["width"]):
            for d in range(position.start_coordinates["depth"], position.end_coordinates["depth"]):
                for h in range(position.start_coordinates["height"], position.end_coordinates["height"]):
                    if (w, d, h) in self.space_grid:
                        del self.space_grid[(w, d, h)]
        
        # Recalculate depth profile
        self.depth_profile = {}
        for _, (_, pos) in self.items.items():
            for w in range(pos.start_coordinates["width"], pos.end_coordinates["width"]):
                for h in range(pos.start_coordinates["height"], pos.end_coordinates["height"]):
                    current_depth = self.depth_profile.get((w, h), 0)
                    self.depth_profile[(w, h)] = max(current_depth, pos.end_coordinates["depth"])
                    
        return item, position
    
    def get_retrieval_steps(self, item_id):
        """Calculate steps needed to retrieve an item"""
        if item_id not in self.items:
            return None
            
        target_item, target_position = self.items[item_id]
        
        # If item is already at the open face (depth=0), no steps needed
        if target_position.is_visible_from_open_face(self.depth):
            return []
            
        # Find blocking items
        blocking_items = []
        for blocking_id, (blocking_item, blocking_position) in self.items.items():
            if blocking_id == item_id:
                continue
                
            # Check if this item blocks the path to the target item
            blocks_path = False
            
            # An item blocks if it's in the same width/height range and has a smaller depth
            width_overlap = (
                blocking_position.start_coordinates["width"] < target_position.end_coordinates["width"] and
                blocking_position.end_coordinates["width"] > target_position.start_coordinates["width"]
            )
            
            height_overlap = (
                blocking_position.start_coordinates["height"] < target_position.end_coordinates["height"] and
                blocking_position.end_coordinates["height"] > target_position.start_coordinates["height"]
            )
            
            depth_blocks = (
                blocking_position.start_coordinates["depth"] < target_position.start_coordinates["depth"]
            )
            
            if width_overlap and height_overlap and depth_blocks:
                blocks_path = True
                
            if blocks_path:
                blocking_items.append((blocking_id, blocking_item, blocking_position))
        
        # Sort blocking items by depth (items closer to the opening first)
        blocking_items.sort(key=lambda x: x[2].start_coordinates["depth"])
        
        # Generate retrieval steps
        steps = []
        for step, (block_id, block_item, _) in enumerate(blocking_items):
            steps.append({
                "step": step + 1,
                "action": "remove",
                "itemId": block_id,
                "itemName": block_item.name
            })
            
        # The actual retrieval step
        steps.append({
            "step": len(steps) + 1,
            "action": "retrieve",
            "itemId": item_id,
            "itemName": target_item.name
        })
        
        # Place back steps in reverse order
        for step, (block_id, block_item, _) in enumerate(reversed(blocking_items)):
            steps.append({
                "step": len(steps) + 1,
                "action": "placeBack",
                "itemId": block_id,
                "itemName": block_item.name
            })
            
        return steps
    
    def remaining_space(self):
        """Calculate remaining volume in the container"""
        total_volume = self.width * self.depth * self.height
        used_volume = sum(pos.volume() for _, pos in self.items.values())
        return total_volume - used_volume
    
    def get_skyline(self):
        """
        Get the current skyline/profile of the container
        Returns list of potential placement positions at the "skyline"
        """
        # This is a simplified approach - a real implementation would use a more
        # sophisticated algorithm to track the "skyline" of the packing
        candidate_positions = []
        
        # Start with the origin position
        if not self.items:
            candidate_positions.append(Position(0, 0, 0, 0, 0, 0))
            return candidate_positions
            
        # Find all possible corner positions
        # For each item, consider its "shadow" in each direction
        for item_id, (_, position) in self.items.items():
            # Position to the right
            candidate_positions.append(Position(
                position.end_coordinates["width"],
                position.start_coordinates["depth"],
                position.start_coordinates["height"],
                position.end_coordinates["width"],
                position.end_coordinates["depth"],
                position.end_coordinates["height"]
            ))
            
            # Position to the back
            candidate_positions.append(Position(
                position.start_coordinates["width"],
                position.end_coordinates["depth"],
                position.start_coordinates["height"],
                position.end_coordinates["width"],
                position.end_coordinates["depth"],
                position.end_coordinates["height"]
            ))
            
            # Position on top
            candidate_positions.append(Position(
                position.start_coordinates["width"],
                position.start_coordinates["depth"],
                position.end_coordinates["height"],
                position.end_coordinates["width"],
                position.end_coordinates["depth"],
                position.end_coordinates["height"]
            ))
        
        return candidate_positions


class CargoManager:
    def __init__(self):
        self.containers = {}  # container_id -> Container
        self.items = {}  # item_id -> Item
        self.current_date = datetime.now()
        self.logs = []
        
    def add_container(self, container_id, zone, width, depth, height):
        self.containers[container_id] = Container(container_id, zone, width, depth, height)
        
    def add_item(self, item):
        self.items[item.item_id] = item
        
    def get_container_by_zone(self, zone):
        """Get all containers in a given zone"""
        return [c for c_id, c in self.containers.items() if c.zone == zone]
        
    def find_optimal_placement(self, items_to_place):
        """
        Find optimal placement for a list of items
        Returns a list of (item, container, position) placements
        """
        # Sort items by priority (highest first)
        sorted_items = sorted(items_to_place, key=lambda x: x.priority, reverse=True)
        
        placements = []
        unplaced_items = []
        
        for item in sorted_items:
            # Try preferred zone first
            preferred_containers = self.get_container_by_zone(item.preferred_zone)
            other_containers = [c for c_id, c in self.containers.items() 
                                if c.zone != item.preferred_zone]
            
            all_containers = preferred_containers + other_containers
            
            best_placement = None
            best_score = float('-inf')
            best_container = None
            
            # Try all possible orientations of the item
            orientations = item.get_possible_orientations()
            
            for container in all_containers:
                for w, d, h in orientations:
                    # Consider all candidate positions
                    candidates = container.get_skyline()
                    
                    for candidate in candidates:
                        # Create a position with the item's dimensions
                        pos = Position(
                            candidate.start_coordinates["width"],
                            candidate.start_coordinates["depth"],
                            candidate.start_coordinates["height"],
                            candidate.start_coordinates["width"] + w,
                            candidate.start_coordinates["depth"] + d,
                            candidate.start_coordinates["height"] + h
                        )
                        
                        if container.can_fit(item, pos):
                            # Calculate placement score
                            # Factors:
                            # 1. Priority accessibility (lower depth is better for high priority)
                            # 2. Preferred zone match
                            # 3. Space utilization
                            
                            # Accessibility score (0-1): 0 is best (at front), 1 is worst (at back)
                            accessibility = pos.start_coordinates["depth"] / container.depth
                            
                            # Priority factor (0-1): 1 is highest priority, 0 is lowest
                            priority_factor = item.priority / 100
                            
                            # Zone match: 1 if preferred, 0 if not
                            zone_match = 1 if container.zone == item.preferred_zone else 0
                            
                            # Space utilization: higher is better
                            volume_factor = pos.volume() / (container.width * container.depth * container.height)
                            
                            # Combined score:
                            # Priority items should be accessible: (1-accessibility) * priority
                            # Preferred zone adds a bonus
                            # Volume utilization is a small factor
                            score = (
                                (1 - accessibility) * priority_factor * 10 +  # Accessibility for high priority
                                zone_match * 5 +                             # Zone match bonus
                                volume_factor * 2                            # Space utilization
                            )
                            
                            if score > best_score:
                                best_score = score
                                best_placement = pos
                                best_container = container
            
            if best_placement:
                placements.append((item, best_container, best_placement))
                # Actually place the item
                best_container.place_item(item, best_placement)
            else:
                unplaced_items.append(item)
        
        return placements, unplaced_items
    
    def suggest_rearrangement(self, unplaced_items):
        """
        Suggest rearrangement to fit unplaced items
        Returns a list of movement operations
        """
        # This is a simplified approach
        # A real implementation would use more sophisticated algorithms
        
        # Sort unplaced items by priority * volume (most important first)
        sorted_unplaced = sorted(
            unplaced_items, 
            key=lambda x: x.priority * x.width * x.depth * x.height,
            reverse=True
        )
        
        rearrangements = []
        
        for item in sorted_unplaced:
            # Find lowest priority items that could be moved
            # Start with items in non-preferred zones
            all_placed_items = []
            for container_id, container in self.containers.items():
                for item_id, (placed_item, position) in container.items.items():
                    all_placed_items.append((
                        placed_item, 
                        container, 
                        position,
                        placed_item.priority
                    ))
            
            # Sort by priority (lowest first)
            all_placed_items.sort(key=lambda x: x[3])
            
            # Try removing items to make space
            for placed_item, container, position, _ in all_placed_items:
                # Skip if higher priority
                if placed_item.priority >= item.priority:
                    continue
                    
                # Remove item and see if our unplaced item fits
                container.remove_item(placed_item.item_id)
                
                # Try to place our item
                placements, still_unplaced = self.find_optimal_placement([item])
                
                if not still_unplaced:
                    # Success! Record the rearrangement
                    item_placement = placements[0]
                    
                    # Now find a new home for the displaced item
                    new_placements, new_unplaced = self.find_optimal_placement([placed_item])
                    
                    if not new_unplaced:
                        # Complete success
                        new_item_placement = new_placements[0]
                        
                        # Record the movements
                        rearrangements.append({
                            "step": len(rearrangements) + 1,
                            "action": "move",
                            "itemId": placed_item.item_id,
                            "fromContainer": container.container_id,
                            "fromPosition": position,
                            "toContainer": new_item_placement[1].container_id,
                            "toPosition": new_item_placement[2]
                        })
                        
                        break
                    else:
                        # Put the original item back - we need to try something else
                        container.place_item(placed_item, position)
                else:
                    # Put the original item back - it didn't help
                    container.place_item(placed_item, position)
        
        return rearrangements
    
    def search_item(self, item_id=None, item_name=None):
        """
        Search for an item by ID or name
        Returns item details and retrieval steps
        """
        result = {
            "success": False,
            "found": False,
            "item": None,
            "retrievalSteps": []
        }
        
        # Find the item
        target_item = None
        if item_id and item_id in self.items:
            target_item = self.items[item_id]
        elif item_name:
            # Find all items with matching name
            matching_items = [item for item_id, item in self.items.items() 
                             if item.name == item_name]
            
            if matching_items:
                # If multiple matches, select based on:
                # 1. Ease of retrieval (fewer steps)
                # 2. Closer to expiry
                # 3. Higher priority
                
                best_item = None
                best_score = float('inf')
                best_container = None
                best_position = None
                best_steps = None
                
                for item in matching_items:
                    # Find which container it's in
                    for container_id, container in self.containers.items():
                        if item.item_id in container.items:
                            item_obj, position = container.items[item.item_id]
                            
                            # Calculate retrieval steps
                            steps = container.get_retrieval_steps(item.item_id)
                            
                            # Calculate days until expiry
                            days_until_expiry = float('inf')
                            if item.expiry_date:
                                delta = (item.expiry_date - self.current_date).days
                                days_until_expiry = max(0, delta)
                            
                            # Calculate score (lower is better)
                            # Steps have highest weight
                            # Then priority (inverted, so high priority = low score)
                            # Then expiry (sooner = lower score)
                            score = (
                                len(steps) * 10 +                 # Steps weight
                                (100 - item.priority) * 0.05 +   # Priority weight
                                days_until_expiry * 0.1          # Expiry weight
                            )
                            
                            if score < best_score:
                                best_score = score
                                best_item = item
                                best_container = container
                                best_position = position
                                best_steps = steps
                
                if best_item:
                    target_item = best_item
                    
                    # Set result details
                    result["found"] = True
                    result["success"] = True
                    result["item"] = {
                        "itemId": best_item.item_id,
                        "name": best_item.name,
                        "containerId": best_container.container_id,
                        "zone": best_container.zone,
                        "position": {
                            "startCoordinates": best_position.start_coordinates,
                            "endCoordinates": best_position.end_coordinates
                        }
                    }
                    result["retrievalSteps"] = best_steps
        
        # If not found by this point, return not found
        if not result["found"]:
            result["success"] = True  # Operation successful, but item not found
            
        return result
    
    def retrieve_item(self, item_id, user_id, timestamp):
        """
        Mark an item as retrieved/used
        Returns success status
        """
        if item_id not in self.items:
            return {"success": False}
            
        item = self.items[item_id]
        
        # Decrement usage count
        item.mark_as_used()
        
        # Log the retrieval
        self.logs.append({
            "timestamp": timestamp,
            "userId": user_id,
            "actionType": "retrieval",
            "itemId": item_id,
            "details": {
                "fromContainer": None,  # Would be filled with actual container
                "toContainer": None,
                "reason": "Use"
            }
        })
        
        return {"success": True}
    
    def place_item(self, item_id, user_id, timestamp, container_id, position):
        """
        Place an item in a specific container at a specific position
        Returns success status
        """
        if item_id not in self.items or container_id not in self.containers:
            return {"success": False}
            
        item = self.items[item_id]
        container = self.containers[container_id]
        
        # Create position object
        pos = Position(
            position["startCoordinates"]["width"],
            position["startCoordinates"]["depth"],
            position["startCoordinates"]["height"],
            position["endCoordinates"]["width"],
            position["endCoordinates"]["depth"],
            position["endCoordinates"]["height"]
        )
        
        # Check if position is valid
        if not container.can_fit(item, pos):
            return {"success": False}
            
        # Place the item
        container.place_item(item, pos)
        
        # Log the placement
        self.logs.append({
            "timestamp": timestamp,
            "userId": user_id,
            "actionType": "placement",
            "itemId": item_id,
            "details": {
                "fromContainer": None,
                "toContainer": container_id,
                "reason": "Storage"
            }
        })
        
        return {"success": True}
    
    def identify_waste(self):
        """
        Identify items that are expired or out of uses
        Returns a list of waste items
        """
        waste_items = []
        
        for item_id, item in self.items.items():
            if item.is_waste:
                # Find which container it's in
                for container_id, container in self.containers.items():
                    if item_id in container.items:
                        _, position = container.items[item_id]
                        
                        waste_items.append({
                            "itemId": item_id,
                            "name": item.name,
                            "reason": "Expired" if item.expiry_date and self.current_date > item.expiry_date else "Out of Uses",
                            "containerId": container_id,
                            "position": {
                                "startCoordinates": position.start_coordinates,
                                "endCoordinates": position.end_coordinates
                            }
                        })
                        break
        
        return {
            "success": True,
            "wasteItems": waste_items
        }
    
    def generate_return_plan(self, undocking_container_id, undocking_date, max_weight):
        """
        Generate a plan for returning waste items
        Returns a return plan with steps
        """
        if undocking_container_id not in self.containers:
            return {"success": False}
            
        undocking_container = self.containers[undocking_container_id]
        
        # Get all waste items
        waste_result = self.identify_waste()
        waste_items = waste_result["wasteItems"]
        
        # Sort by priority (lowest first)
        waste_items.sort(key=lambda x: self.items[x["itemId"]].priority)
        
        # Calculate total weight of waste
        total_weight = sum(self.items[item["itemId"]].mass for item in waste_items)
        
        # If total weight exceeds max, prioritize highest priority items
        if total_weight > max_weight:
            # Re-sort by priority (highest first)
            waste_items.sort(key=lambda x: self.items[x["itemId"]].priority, reverse=True)
            
            # Take items until we reach max weight
            selected_items = []
            current_weight = 0
            
            for item in waste_items:
                item_weight = self.items[item["itemId"]].mass
                if current_weight + item_weight <= max_weight:
                    selected_items.append(item)
                    current_weight += item_weight
            
            waste_items = selected_items
        
        # Generate steps for moving items to undocking container
        return_plan = []
        retrieval_steps = []
        
        for step, item in enumerate(waste_items):
            item_obj = self.items[item["itemId"]]
            from_container_id = item["containerId"]
            from_container = self.containers[from_container_id]
            
            # Get retrieval steps
            steps = from_container.get_retrieval_steps(item["itemId"])
            
            # Add to overall retrieval steps
            retrieval_steps.extend(steps)
            
            # Add movement step
            return_plan.append({
                "step": step + 1,
                "itemId": item["itemId"],
                "itemName": item["name"],
                "fromContainer": from_container_id,
                "toContainer": undocking_container_id
            })
        
        # Calculate total volume
        total_volume = sum(
            (item["position"]["endCoordinates"]["width"] - item["position"]["startCoordinates"]["width"]) *
            (item["position"]["endCoordinates"]["depth"] - item["position"]["startCoordinates"]["depth"]) *
            (item["position"]["endCoordinates"]["height"] - item["position"]["startCoordinates"]["height"])
            for item in waste_items
        )
        
        # Generate return manifest
        return_manifest = {
            "undockingContainerId": undocking_container_id,
            "undockingDate": undocking_date,
            "returnItems": [
                {
                    "itemId": item["itemId"],
                    "name": item["name"],
                    "reason": item["reason"]
                }
                for item in waste_items
            ],
            "totalVolume": total_volume,
            "totalWeight": total_weight
        }
        
        return {
            "success": True,
            "returnPlan": return_plan,
            "retrievalSteps": retrieval_steps,
            "returnManifest": return_manifest
        }
    
    def complete_undocking(self, undocking_container_id, timestamp):
        """
        Complete undocking process, removing items from the system
        Returns success status and number of items removed
        """
        if undocking_container_id not in self.containers:
            return {"success": False, "itemsRemoved": 0}
            
        undocking_container = self.containers[undocking_container_id]
        
        # Count items in the container
        items_count = len(undocking_container.items)
        
        # Remove all items
        for item_id in list(undocking_container.items.keys()):
            undocking_container.remove_item(item_id)
            
            # Also remove from main items dictionary
            if item_id in self.items:
                del self.items[item_id]
            
            # Log the disposal
            self.logs.append({
                "timestamp": timestamp,
                "userId": "SYSTEM",
                "actionType": "disposal",
                "itemId": item_id,
                "details": {
                    "fromContainer": undocking_container_id,
                    "toContainer": None,
                    "reason": "Undocking"
                }
            })
        
        return {
            "success": True,
            "itemsRemoved": items_count
        }
    
    def simulate_days(self, num_days=None, to_timestamp=None, items_to_be_used_per_day=None):
    """
    Simulate passage of time
    Returns status and changes made
    """
    if to_timestamp:
        # Convert to_timestamp to a datetime object
        target_date = datetime.fromisoformat(to_timestamp)
        delta = (target_date - self.current_date).days
        if delta < 0:
            return {"success": False, "message": "Invalid target date (earlier than current date)"}
        num_days = delta
    elif num_days is None:
        return {"success": False, "message": "Either num_days or to_timestamp must be provided"}

    # Initialize lists to track changes
    items_used = []
    items_expired = []
    items_depleted = []

    for day in range(num_days):
        # Update the current date
        self.current_date += timedelta(days=1)

        # Check for expired items
        for item_id, item in self.items.items():
            if item.expiry_date and self.current_date > item.expiry_date:
                item.is_waste = True
                items_expired.append({
                    "itemId": item_id,
                    "name": item.name
                })

        # Simulate item usage for the day
        if items_to_be_used_per_day:
            for item_usage in items_to_be_used_per_day:
                item_id = item_usage.get("itemId")
                item_name = item_usage.get("name")

                # Find the item by ID or name
                item = None
                if item_id and item_id in self.items:
                    item = self.items[item_id]
                elif item_name:
                    # Find by name
                    matching_items = [item for item in self.items.values() if item.name == item_name]
                    if matching_items:
                        # Use the first matching item
                        item = matching_items[0]

                if item:
                    # Mark the item as used
                    remaining_uses = item.mark_as_used()
                    items_used.append({
                        "itemId": item.item_id,
                        "name": item.name,
                        "remainingUses": remaining_uses
                    })

                    # Check if the item is now depleted
                    if item.is_waste:
                        items_depleted.append({
                            "itemId": item.item_id,
                            "name": item.name
                        })

    # Return the results
    return {
        "success": True,
        "newDate": self.current_date.isoformat(),
        "changes": {
            "itemsUsed": items_used,
            "itemsExpired": items_expired,
            "itemsDepletedToday": items_depleted
        }
    }
    
      
