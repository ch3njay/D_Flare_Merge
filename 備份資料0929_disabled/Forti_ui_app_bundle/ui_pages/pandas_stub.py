class DataFrame:
    def __init__(self, data, index=None):
        self.data = {k: list(v) for k, v in data.items()}
        n = len(next(iter(self.data.values()))) if data else 0
        self.index = list(range(n)) if index is None else list(index)
    def __getitem__(self, key):
        return self.data[key]
    def select(self, idxs):
        data = {k: [v[i] for i in idxs] for k, v in self.data.items()}
        return DataFrame(data, index=[self.index[i] for i in idxs])
