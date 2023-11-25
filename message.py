class Message:
    def __init__(self, symbol=None, command=None, parameters=None):
        self.symbol = symbol
        self.command = command
        self.parameters = parameters or {}
