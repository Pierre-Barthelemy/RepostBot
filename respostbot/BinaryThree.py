class Node:
    def __init__(self, value):
        self.Value = value
        self.L = None
        self.R = None

    def value(self):
        return self.Value

    def left(self):
        return self.L

    def right(self):
        return self.R

    def set_left(self, value):
        self.L = value

    def set_right(self, value):
        self.R = value


class Tree:
    def __init__(self):
        self.Root = None

    def get_root(self):
        return self.Root

    def set_root(self, value):
        self.Root = value

    def add(self, value):
        if self.get_root() is None:
            self.set_root(Node(value))
            return None
        else:
            return self._add(value, self.get_root())

    def _add(self, value, node):
        if value == node.value():
            return node.value()
        elif value < node.value():
            if node.left() is not None:
                return self._add(value, node.left())
            else:
                node.set_left(Node(value))
                return None
        else:
            if node.right() is not None:
                return self._add(value, node.right())
            else:
                node.set_right(Node(value))
                return None

    def find(self, value):
        if self.get_root() is not None:
            return self._find(value, self.get_root())
        else:
            return None

    def _find(self, value, node):
        if value == node.value():
            print("found")
            return node
        elif value < node.value() and node.left() is not None:
            return self._find(value, node.left())
        elif value > node.value() and node.right() is not None:
            return self._find(value, node.right())

    def delete_tree(self):
        # garbage collector will do this for us.
        self.set_root(None)

    def count(self):
        return self._count(self.get_root())

    def _count(self, node):
        if node is None:
            return 0
        else:
            nb = self._count(node.left())
            nb += self._count(node.right())
            return nb + 1

    def height(self):
        return self._height(self.get_root())

    def _height(self, node):
        if node is None:
            return 0
        else:
            return max(self._height(node.left()), self._height(node.right())) + 1

    def life(self):
        print("Count : {}\nHeight : {}".format(self.count(), self.height()))

    def print_tree(self):
        if self.get_root() is not None:
            self._print_tree(self.get_root())

    def _print_tree(self, node):
        if node is not None:
            self._print_tree(node.left())
            print(str(node.value()) + ' ')
            self._print_tree(node.right())
