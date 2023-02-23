class MockDevice:
    def __init__(self):
        self.name = None
        self.presence = True
        self.model = 'Module Model'
        self.serial = 'Module Serial'

    def get_name(self):
        return self.name

    def get_presence(self):
        return self.presence

    def get_model(self):
        return self.model

    def get_serial(self):
        return self.serial