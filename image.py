from image_match.goldberg import ImageSignature
gis = ImageSignature()


class Image:

    def __init__(self, link):
        self.Link = link
        self.Value = gis.generate_signature(link)

    def __lt__(self, other):  # <
        return gis.normalized_distance(self.value(), other.value()) < 0.65

    def ___le__(self, other):  # <=
        return gis.normalized_distance(self.value(), other.value()) <= 0.65

    def __eq__(self, other):  # ==
        if other is None:
            return False
        return gis.normalized_distance(self.value(), other.value()) < 0.1

    def __ne__(self, other):  # !=
        if other is None:
            return True
        return gis.normalized_distance(self.value(), other.value()) >= 1

    def __gt__(self, other):  # >
        return gis.normalized_distance(self.value(), other.value()) > 0.65

    def __ge__(self, other):  # >=
        return gis.normalized_distance(self.value(), other.value()) >= 0.65

    def __str__(self):
        return self.Link

    def value(self):
        return self.Value

    def link(self):
        return self.Link

    def setLink(self, link):
        self.Link = link
