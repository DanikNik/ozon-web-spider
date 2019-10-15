class SubstitutionQueue:
    def __init__(self, maxsize):
        self.max_size = maxsize
        self.size = 0
        self.data = []

    def push(self, elem):
        self.data.append(elem)
        self.data.sort()
        self.size += 1
        while self.size > self.max_size:
            self.data.pop(-1)
            self.size -= 1

    def pop(self, elem):
        self.size -= 1
        return self.data.pop(0)

    def is_empty(self):
        return self.size == 0

    def __len__(self):
        return self.size
