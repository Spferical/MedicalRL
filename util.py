class Pos(object):
    def __init__(self, x_or_tuple, y=None):
        if isinstance(x_or_tuple, tuple):
            self.x, self.y = x_or_tuple
        else:
            self.x = x_or_tuple
            self.y = y

    def __add__(self, pos):
        return Pos(self.x + pos.x, self.y + pos.y)

    def __sub__(self, pos):
        return Pos(self.x - pos.x, self.y - pos.y)

    def __mul__(self, num):
        return Pos(self.x * num, self.y * num)

    def __floordiv__(self, num):
        return Pos(self.x // num, self.y // num)

    def __str__(self):
        return "({}, {})".format(self.x, self.y)
