# retrieve.py

from collections import deque
import numpy as np

class RetrievalPathFinder:
    """Optimal retrieval path calculator with 3D collision detection"""
    
    def __init__(self, container_space):
        self.space = container_space
        
    def find_retrieval_path(self, item_id):
        """BFS-based path finding with 3D collision checks"""
        if item_id not in self.space.items:
            return []
            
        target_pos = self.space.items[item_id]
        access_path = []
        visited = set()
        queue = deque([(target_pos, [])])
        
        while queue:
            current_pos, path = queue.popleft()
            
            # Check if reached open face (y=0)
            if current_pos[1] == 0:
                return path[::-1]  # Reverse to get front-to-back order
            
            # Find blocking items
            blockers = self._find_blockers(current_pos)
            for blocker_id in blockers:
                if blocker_id not in visited:
                    new_path = path + [{
                        'action': 'remove',
                        'item_id': blocker_id,
                        'position': self.space.items[blocker_id]
                    }]
                    queue.append((self.space.items[blocker_id], new_path))
                    visited.add(blocker_id)
                    
        return []

    def _find_blockers(self, position):
        """Find items blocking the path to container opening"""
        x, y, z, w, d, h = position
        blockers = []
        
        # Check only items between target and opening (y < current_y)
        for item_id, (ix, iy, iz, iw, id, ih) in self.space.items.items():
            if iy >= y:
                continue  # Skip items behind or same depth
                
            # Check X and Z overlap (must block entire path)
            x_overlap = (ix < x + w) and (ix + iw > x)
            z_overlap = (iz < z + h) and (iz + ih > z)
            
            if x_overlap and z_overlap:
                blockers.append(item_id)
                
        # Sort blockers by proximity to opening
        return sorted(blockers, 
                     key=lambda x: self.space.items[x][1], 
                     reverse=True)

class WasteOptimizer:
    """Waste management with 3D bin packing"""
    
    def __init__(self, containers):
        self.containers = containers
        
    def generate_return_plan(self, waste_items, max_weight):
        """3D bin packing with weight and volume constraints"""
        sorted_items = sorted(waste_items, 
                            key=lambda x: (-x['mass'], x['volume']))
        
        bins = []
        for item in sorted_items:
            placed = False
            for bin in bins:
                # Check weight and volume constraints
                if (bin['mass'] + item['mass'] <= max_weight and
                    bin['volume'] + item['volume'] <= bin['max_volume']):
                    
                    bin['items'].append(item)
                    bin['mass'] += item['mass']
                    bin['volume'] += item['volume']
                    placed = True
                    break
                    
            if not placed:
                bins.append({
                    'items': [item],
                    'mass': item['mass'],
                    'volume': item['volume'],
                    'max_volume': self._get_container_volume(item['target_container'])
                })
                
        return bins

    def _get_container_volume(self, container_id):
        container = next(c for c in self.containers if c['containerId'] == container_id)
        return container['width'] * container['depth'] * container['height']