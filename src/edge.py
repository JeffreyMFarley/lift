
class Edge(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        h = hash(str(self))
        return h

    def __str__(self):
        return '{} -> {}'.format(self.start, self.end)
