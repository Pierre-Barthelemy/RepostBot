
class Link:
    """
    Class to stock various data about a link.
    """
    def __init__(self, nb, author, time):
        self.Nb_repost = nb
        self.Author = author
        self.FirstPost = time

    def __lt__(self, other):
        return self.Nb_repost < other.Nb_repost

    def author(self):
        return self.Author

    def nb_repost(self):
        return self.Nb_repost

    def first_post(self):
        return self.FirstPost

    def add_one(self):
        self.Nb_repost += 1
