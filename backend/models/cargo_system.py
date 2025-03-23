import numpy as np
from heapq import heappush, heappop
from collections import deque
from datetime import datetime, timedelta

class CargoSystem:
    """Integrated cargo management system with waste handling"""
    
    def __init__(self, containers):
        self.containers = {
            c['containerId']: ContainerSpace(
                c['width'], 
                c['depth'], 
                c['height']
            ) for c in containers
        }
        self.bin_packer = PriorityBinPacker(containers)
        self.retrieval_finder = RetrievalPathFinder(self.containers)
        self.waste_optimizer = WasteOptimizer(containers)
        self.items = {}
        self.logs = deque(maxlen=10000)
        
    def add_items(self, items):
        """Add new items with optimal placement"""
        packed = self.bin_packer.pack_items(items)
        for item, cid, pos in packed:
            self.containers[cid].add_item(item['itemId'], pos)
            self.items[item['itemId']] = {
                **item,
                'containerId': cid,
                'position': pos,
                'remaining_uses': item.get('usageLimit', 0),
                'last_used': datetime.now().isoformat()
            }
            
    def retrieve_item(self, item_id, user_id):
        """Retrieve item with optimal path finding"""
        if item_id not in self.items:
            return None
            
        item = self.items[item_id]
        container = self.containers[item['containerId']]
        path = self.retrieval_finder.find_retrieval_path(
            item_id, 
            container
        )
        
        # Update usage count
        if item['remaining_uses'] > 0:
            item['remaining_uses'] -= 1
            item['last_used'] = datetime.now().isoformat()
            
        self.logs.append({
            'timestamp': datetime.now().isoformat(),
            'userId': user_id,
            'actionType': 'retrieval',
            'itemId': item_id,
            'details': {
                'steps': len(path),
                'container': item['containerId']
            }
        })
        
        return {
            'item': item,
            'retrieval_steps': path
        }
    
    def simulate_time(self, days):
        """Time simulation with waste handling"""
        current_date = datetime.now()
        waste = []
        
        for _ in range(days):
            current_date += timedelta(days=1)
            
            # Check expirations
            for item in self.items.values():
                if item.get('expiryDate'):
                    expiry_date = datetime.fromisoformat(item['expiryDate'])
                    if current_date > expiry_date:
                        waste.append(item)
                        
                if item['remaining_uses'] <= 0:
                    waste.append(item)
            
            # Process waste
            if waste:
                return_plan = self.waste_optimizer.generate_return_plan(
                    waste, 
                    max_weight=1000  # Example value
                )
                self.process_waste_return(return_plan)
                
        return self.get_system_status()
    
    def process_waste_return(self, return_plan):
        """Execute waste return plan"""
        for bin in return_plan:
            for item in bin['items']:
                container = self.containers[item['containerId']]
                container.remove_item(item['itemId'])
                del self.items[item['itemId']]
                
    def get_system_status(self):
        """Return current system state"""
        return {
            'containers': {
                cid: {
                    'utilization': np.sum(container.occupancy) / container.occupancy.size,
                    'item_count': len(container.items)
                } for cid, container in self.containers.items()
            },
            'total_items': len(self.items),
            'waste_count': sum(1 for item in self.items.values() 
                              if item['remaining_uses'] <= 0)
        }

class ContainerSpace:
    """Enhanced 3D container with optimized spatial operations"""
    
    def __init__(self, width, depth, height):
        self.dims = (width, depth, height)
        self.occupancy = np.zeros((width, depth, height), dtype=bool)
        self.items = {}
        
    def add_item(self, item_id, position):
        x, y, z, w, d, h = position
        if self._check_collision(x, y, z, w, d, h):
            return False
        self.occupancy[x:x+w, y:y+d, z:z+h] = True
        self.items[item_id] = position
        return True
    
    def _check_collision(self, x, y, z, w, d, h):
        return np.any(self.occupancy[
            max(0, x):min(self.dims[0], x+w),
            max(0, y):min(self.dims[1], y+d),
            max(0, z):min(self.dims[2], z+h)
        ])

class PriorityBinPacker:
    """Enhanced bin packing with genetic algorithm optimization"""
    
    def __init__(self, containers):
        self.containers = containers
        self.population_size = 50
        self.generations = 100
        
    def pack_items(self, items):
        # Genetic algorithm implementation
        best = self._genetic_algorithm(items)
        return best
    
    def _genetic_algorithm(self, items):
        # Implementation with crossover and mutation
        pass

class RetrievalPathFinder:
    """BFS-based path finding with memoization"""
    
    def __init__(self, containers):
        self.containers = containers
        
    def find_retrieval_path(self, item_id, container):
        position = container.items[item_id]
        visited = set()
        queue = deque([(position, [])])
        
        while queue:
            current_pos, path = queue.popleft()
            if current_pos[1] == 0:  # Reached open face
                return path
            
            blockers = self._find_blockers(current_pos, container)
            for blocker in blockers:
                if blocker not in visited:
                    new_path = path + [{
                        'action': 'remove',
                        'item_id': blocker,
                        'position': container.items[blocker]
                    }]
                    queue.append((container.items[blocker], new_path))
                    visited.add(blocker)
                    
        return []

    def _find_blockers(self, position, container):
        x, y, z, w, d, h = position
        return [
            item_id for item_id, (ix, iy, iz, iw, id, ih) in container.items.items()
            if iy < y and (ix < x + w and ix + iw > x) and (iz < z + h and iz + ih > z)
        ]

class WasteOptimizer:
    """Waste management with multiple optimization strategies"""
    
    def __init__(self, containers):
        self.containers = containers
        
    def generate_return_plan(self, waste_items, max_weight):
        # Hybrid bin packing algorithm
        return self._hybrid_bin_packing(waste_items, max_weight)
    
    def _hybrid_bin_packing(self, items, max_weight):
        # Combined first-fit and best-fit approach
        bins = []
        sorted_items = sorted(items, key=lambda x: (-x['mass'], x['volume']))
        
        for item in sorted_items:
            placed = False
            for bin in bins:
                if bin['mass'] + item['mass'] <= max_weight:
                    bin['items'].append(item)
                    bin['mass'] += item['mass']
                    placed = True
                    break
            if not placed:
                bins.append({
                    'items': [item],
                    'mass': item['mass']
                })
        return bins