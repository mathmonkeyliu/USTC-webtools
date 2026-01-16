class InvalidSessionError(Exception):
    """session无效"""
    def __init__(self):
        pass

    def __str__(self):
        return "该session不可用"