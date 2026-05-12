class PlayerRequest:
    """Minimal functional stub for Strategy A fallback."""
    def __init__(self):
        self.uid = ""
        self.region = ""
        self.version = ""

    def SerializeToString(self) -> bytes:
        from core.proto import encode_request_raw
        return encode_request_raw(self.uid, self.region, self.version)
