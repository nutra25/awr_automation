class AWRComponent:
    def __init__(self, awr):
        self.awr = awr

    @property
    def app(self):
        return self.awr.app

    @property
    def logger(self):
        return self.awr.logger