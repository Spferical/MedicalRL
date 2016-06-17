from constants import DIRECTIONS


def get_path(from_pos, to_pos, level):
    if level[to_pos].blocked:
        return []

    def get_walkable_adjacent_tiles(source_pos):
        adjacent = (source_pos + direction for direction in DIRECTIONS)
        return (pos for pos in adjacent if not level[pos].blocked)

    def unwrap(wrapped_path):
        unwrapped_path = []
        while wrapped_path:
            unwrapped_path.insert(0, wrapped_path[0])
            wrapped_path = wrapped_path[1]
        return unwrapped_path

    found = set([from_pos])
    starts = list(get_walkable_adjacent_tiles(from_pos))

    if to_pos in starts:
        return [to_pos]

    queue = [(pos, None) for pos in starts]
    while queue:
        pos, hist = queue.pop(0)
        for new_pos in get_walkable_adjacent_tiles(pos):
            if new_pos in found:
                continue
            if new_pos == to_pos:
                return unwrap((new_pos, (pos, hist)))
            queue.append((new_pos, (pos, hist)))
            found.add(new_pos)
    return []
