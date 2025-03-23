import numpy as np
from heapq import heappush, heappop
from collections import deque
from functools import lru_cache

class ContainerSpace:
    """Optimized 3D container space management with collision detection"""
    
    def __init__(self, width, depth, height):
        self.dims = (int(width), int(depth), int(height))
        self.occupancy = np.zeros(self.dims, dtype=bool)
        self.items = {}
        
    def add_item(self, item_id, position):
        x, y, z, w, d, h = position
        if self._check_collision(x, y, z, w, d, h):
            return False
        self.occupancy[x:x+w, y:y+d, z:z+h] = True
        self.items[item_id] = position
        return True
    
    def remove_item(self, item_id):
        position = self.items.pop(item_id)
        x, y, z, w, d, h = position
        self.occupancy[x:x+w, y:y+d, z:z+h] = False
        return position
    
    def _check_collision(self, x, y, z, w, d, h):
        """Efficient collision check using numpy slicing"""
        return np.any(self.occupancy[
            max(0, x):min(self.dims[0], x+w),
            max(0, y):min(self.dims[1], y+d),
            max(0, z):min(self.dims[2], z+h)
        ])

class PriorityBinPacker:
    """Priority-based 3D bin packing with accessibility optimization"""
    
    def __init__(self, containers):
        self.containers = {
            c['containerId']: {
                'space': ContainerSpace(c['width'], c['depth'], c['height']),
                'metadata': c,
                'free_space': deque()
            } for c in containers
        }
        self._init_free_spaces()
        
    def _init_free_spaces(self):
        """Precompute initial free spaces for faster packing"""
        for cid, container in self.containers.items():
            space = container['space']
            container['free_space'].extend(
                (y, x, z) 
                for y in range(space.dims[1])  # Depth-first
                for x in range(space.dims[0])
                for z in range(space.dims[2])
            )

    def pack_items(self, items):
        """Pack items with priority and accessibility optimization"""
        sorted_items = sorted(items, key=lambda x: (
            -x['priority'], 
            x['width'] * x['depth'] * x['height']
        ))
        
        for item in sorted_items:
            best = {'score': -np.inf, 'placement': None}
            
            for cid, container in self.containers.items():
                zone_bonus = 2 if container['metadata']['zone'] == item['preferredZone'] else -2
                
                for orientation in self.get_orientations(item):
                    position = self.find_optimal_position(container, orientation)
                    if position:
                        score = self._calculate_score(position, item['priority'], zone_bonus)
                        if score > best['score']:
                            best = {'cid': cid, 'pos': position, 'score': score}
            
            if best['score'] != -np.inf:
                container = self.containers[best['cid']]
                if container['space'].add_item(item['itemId'], best['pos']):
                    self._update_free_space(container, best['pos'])
                    yield {'item': item, 'container': best['cid'], 'position': best['pos']}
            else:
                yield {'rearrangements': self.suggest_rearrangements(item)}

    def find_optimal_position(self, container, dimensions):
        """Find optimal position using spatial hashing and depth-first search"""
        w, d, h = dimensions
        space = container['space']
        
        # Check cached free spaces first
        for y, x, z in container['free_space']:
            if (x + w <= space.dims[0] and 
                y + d <= space.dims[1] and 
                z + h <= space.dims[2]):
                if not np.any(space.occupancy[x:x+w, y:y+d, z:z+h]):
                    return (x, y, z, w, d, h)
        return None

    def _calculate_score(self, position, priority, zone_bonus):
        """Calculate placement score considering priority and accessibility"""
        depth_penalty = position[1] * 0.5  # Linear depth penalty
        return (priority * 10) + zone_bonus - depth_penalty

    def suggest_rearrangements(self, item):
        """Suggest items to rearrange to make space"""
        candidates = []
        for cid, container in self.containers.items():
            container_items = sorted(
                container['space'].items.items(),
                key=lambda x: (x[1][1], -x[1][3]*x[1][4]*x[1][5])  # Depth and volume
            )
            # Propose removing last 2 items in deepest positions
            candidates.extend(container_items[-2:])
        
        return [{
            'itemId': item_id,
            'fromContainer': cid,
            'newPosition': None
        } for item_id, _ in candidates]

    @staticmethod
    def get_orientations(item):
        """Generate all valid item orientations"""
        dims = [item['width'], item['depth'], item['height']]
        return list({(a, b, c) for a, b, c in permutations(dims) if a <= b <= c})

    def _update_free_space(self, container, position):
        """Update free space cache after placement"""
        x, y, z, w, d, h = position
        # Remove occupied positions from free space
        container['free_space'] = deque(
            pos for pos in container['free_space']
            if not (x <= pos[0] < x + w and
                    y <= pos[1] < y + d and
                    z <= pos[2] < z + h)
        )