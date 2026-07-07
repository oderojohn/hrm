class BaseSMSBackend:
    def send(self, to, message):
        raise NotImplementedError
