from util import Pos


QUAD_TRANSFORMATIONS = [
    # X -> X, X -> Y, Y -> X, Y -> Y
    [1, 0, 0, 1],
    [0, 1, 1, 0],
    [0, -1, 1, 0],
    [-1, 0, 0, 1],
    [-1, 0, 0, -1],
    [0, -1, -1, 0],
    [0, 1, -1, 0],
    [1, 0, 0, -1],
]


def calculate_fov(pos, radius, level):
    """Calculates FOV radiating from given position with given radius.
    Yields positions that can be seen."""
    for quadrant in range(8):
        for seen_pos in cast_light(pos, 1, 0, 1, radius, quadrant, level):
            yield(seen_pos)


def cast_light(start_pos, start_y, start_slope, end_slope, radius, quad,
               level):
    if start_slope > end_slope:
        return
    prev_blocked = False
    for y in range(start_y, radius + 1):
        dy = y
        for dx in range(y + 1):
            trans = QUAD_TRANSFORMATIONS[quad]
            pos = start_pos + Pos(dx * trans[0] + dy * trans[1],
                                  dx * trans[2] + dy * trans[3])
            left_slope = (dx - .5) / (dy + .5)
            right_slope = (dx + .5) / (dy - .5)

            if start_slope > right_slope or end_slope < left_slope:
                continue

            yield pos

            if level[pos].opaque:
                if prev_blocked:
                    new_start = right_slope
                else:
                    # end of row of see-through tiles
                    prev_blocked = True
                    for pos in cast_light(start_pos, y + 1,
                                          start_slope, left_slope,
                                          radius, quad, level):
                        yield pos
                    new_start = right_slope
            elif prev_blocked:
                # end of series of walls
                prev_blocked = False
                start_slope = new_start
        if prev_blocked:
            break
