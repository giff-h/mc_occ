from math import log2

size = 38  # Interior dimension. Must be at least 11
x_start, z_start = (10, 10)  # Northwest corner of the walls relative to command execution
max_blocks = 2**15  # The maximum mc allows to process in one command
helix = 4  # Number of stair helices to create

stair_size = size - 6
x_corners = (x_start + 1, -(x_start + size))  # Interior corners
z_corners = (z_start + 1, -(z_start + size))  # Negative so that adding always moves in the correct direction
floor_fill = "/fill ~{} 1 ~{} ~{} 1 ~{}"


def walls():
    wall = "/fill ~{} {} ~{} ~{} 255 ~{} glass"
    x_corner = x_start + size + 1
    z_corner = z_start + size + 1
    yield wall.format(x_start, 1, z_start, x_start, z_corner)
    yield wall.format(x_corner, 1, z_start, x_corner, z_corner)
    yield wall.format(x_start, 1, z_start, x_corner, z_start)
    yield wall.format(x_start, 1, z_corner, x_corner, z_corner)
    yield wall.format(x_start, 255, z_start, x_corner, z_corner)


def clear():
    air = "/fill ~{} {} ~{} ~{} {} ~{} air".format(x_corners[0], '{}', z_corners[0],
                                                   abs(x_corners[1]), '{}', abs(z_corners[1]))
    top = 254
    chunk = max_blocks // (size * size)
    while top > chunk:
        yield air.format(top, top - chunk + 1)
        top -= chunk
    if top > 1:
        yield air.format(top, 2)
    yield floor_fill.format(x_corners[0], z_corners[0], abs(x_corners[1]), abs(z_corners[1])) + " torch"


def stairs():
    if helix == 0:
        return []

    stair = floor_fill + " spruce_stairs {}"
    corners = [(x_corners[0], z_corners[0]),
               (x_corners[1], z_corners[1]),
               (x_corners[1], z_corners[0]),
               (x_corners[0], z_corners[1])]

    for i in range(4):
        if helix > i:
            lt2 = i < 2
            x, z = corners[i]
            x += 3 if lt2 else 1
            z += 1 if lt2 else 3
            yield stair.format(abs(x), abs(z), abs(x + int(not lt2)), abs(z + int(lt2)), i)

            clone = "/clone ~{} 1 ~{}".format(abs(x), abs(z)) + " ~{} {} ~{} ~{} {} ~{} masked"
            for clone_set in clone_gen(x, z, lt2):
                yield clone.format(*clone_set)

            x_plank = -(x + (stair_size + 1) ** int(lt2))
            z_plank = -(z + (stair_size + 1) ** int(not lt2))
            yield "/fill ~{} {} ~{} ~{} {} ~{} planks 1".format(abs(x_plank), stair_size, abs(z_plank),
                                                                abs(x_plank + 1), stair_size, abs(z_plank + 1))

    clone_stairs = "/clone ~{} {} ~{} ~{} {} ~{} ~{} {} ~{}".format(x_start + 2, "{}", z_start + 2,
                                                                    x_start + size - 1, "{}", z_start + size - 1,
                                                                    x_start + 2, "{}", z_start + 2) + " masked"
    i = 0
    stair_area = (stair_size + 4) ** 2
    if stair_area * stair_size < max_blocks:
        while stair_area * stair_size * (i+1) < max_blocks:
            add_to = stair_size * (i+1) + 1
            if add_to + stair_size > 254:
                break
            yield clone_stairs.format(stair_size * i + 1, stair_size * (i+1), add_to)
            i += 1
    add_to = stair_size * (i+1) + 1
    chunk = max_blocks // stair_area
    start_from = 1
    while add_to + chunk - 1 < 255:
        yield clone_stairs.format(start_from, start_from + chunk - 1, add_to)
        start_from += chunk
        add_to += chunk
    yield clone_stairs.format(start_from, start_from + (254 - add_to), add_to)


def clone_gen(x, z, lt2):
    clones = int(log2(stair_size))
    remaining = stair_size - 2 ** clones
    x_mod = int(lt2)
    z_mod = int(not lt2)

    sets = [(diff - 1, diff, diff * 2 - 1, True) for diff in map(lambda i: 2 ** i, range(clones))]
    if remaining:
        sets.append((remaining - 1, stair_size - 1, stair_size - remaining, False))
    for clone_set in sets:
        x_end = abs(x + clone_set[0] ** x_mod)
        z_end = abs(z + clone_set[0] ** z_mod)
        x_to = min(abs(x + clone_set[1] * x_mod), abs(x + clone_set[2] ** x_mod))
        z_to = min(abs(z + clone_set[1] * z_mod), abs(z + clone_set[2] ** z_mod))
        yield(x_end, clone_set[1] if clone_set[3] else remaining, z_end,
              x_to, 1 + clone_set[1] if clone_set[3] else clone_set[2], z_to)


commands = list(walls()) + list(clear()) + list(stairs())
for line in commands:
    print("INIT:" + line)
print(len(commands))
