class Pos(object):
    def __init__(self, x_or_tuple, y=None):
        if isinstance(x_or_tuple, tuple):
            self.x, self.y = x_or_tuple
        else:
            self.x = x_or_tuple
            self.y = y

    def __eq__(self, pos):
        return self[:] == pos[:]

    def __add__(self, pos):
        return Pos(self.x + pos.x, self.y + pos.y)

    def __sub__(self, pos):
        return Pos(self.x - pos.x, self.y - pos.y)

    def __mul__(self, num):
        return Pos(self.x * num, self.y * num)

    def __floordiv__(self, num):
        return Pos(self.x // num, self.y // num)

    def __repr__(self):
        return "Pos({}, {})".format(self.x, self.y)

    def __len__(self):
        return 2

    def __getitem__(self, i):
        return (self.x, self.y)[i]

    def __hash__(self):
        return hash(repr(self))
