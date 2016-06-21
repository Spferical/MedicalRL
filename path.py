import heapq
from constants import DIRECTIONS


def get_path(from_pos, to_pos, level):
    if level[to_pos].blocked or from_pos == to_pos:
        return []

    def get_walkable_adjacent_tiles(source_pos):
        adjacent = (source_pos + direction for direction in DIRECTIONS)
        return (pos for pos in adjacent if pos not in found and
                (pos == to_pos or not level.is_blocked(pos)))

    def heuristic(pos):
        return min(abs(pos.x - to_pos.x), abs(pos.y - to_pos.y))

    class Node(object):
        def __init__(self, pos, parent=None):
            self.pos = pos
            self.priority = heuristic(pos)
            self.parent = parent

        def get_path(self):
            path = []
            node = self
            while node:
                path.insert(0, node.pos)
                node = node.parent
            return path

        def __lt__(self, other):
            return self.priority < other.priority

    found = set([from_pos])
    starts = list(get_walkable_adjacent_tiles(from_pos))

    if to_pos in starts:
        return [to_pos]

    queue = []
    for pos in starts:
        heapq.heappush(queue, Node(pos))

    while queue:
        node = heapq.heappop(queue)
        for new_pos in get_walkable_adjacent_tiles(node.pos):
            if new_pos in found:
                continue
            if new_pos == to_pos:
                return Node(new_pos, node).get_path()
            heapq.heappush(queue, Node(new_pos, node))
            found.add(new_pos)
    return []
