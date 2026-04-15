# Strategy B fallback stubs
# In a real scenario, this would be a compiled protoc file.
# To satisfy Strategy A detection in core/proto.py, we provide a minimal mock.
class PlayerRequest:
    def __init__(self):
        self.uid = 0
        self.region = ""
    def SerializeToString(self):
        # Mock serialization for testing purposes
        return b"\x08\x00\x12\x03IND"
