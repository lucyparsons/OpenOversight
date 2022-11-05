# Monkeypatch bug in imagehdr
from imghdr import tests


def test_jpeg1(h, f):
    """JPEG data in JFIF format"""
    if b"JFIF" in h[:23]:
        return "jpeg"


JPEG_MARK = (
    b"\xff\xd8\xff\xdb\x00C\x00\x08\x06\x06"
    b"\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f"
)


def test_jpeg2(h, f):
    """JPEG with small header"""
    if len(h) >= 32 and 67 == h[5] and h[:32] == JPEG_MARK:
        return "jpeg"


def test_jpeg3(h, f):
    """JPEG data in JFIF or Exif format"""
    if h[6:10] in (b"JFIF", b"Exif") or h[:2] == b"\xff\xd8":
        return "jpeg"


def add_jpeg_patch():
    """Custom JPEG identification patch.

    It turns out that imghdr sucks at identifying jpegs and needs a custom patch to
    behave correctly. This function adds that.

    Sources:
    - https://stackoverflow.com/a/57693121/3277713
    - https://bugs.python.org/issue28591
    """
    tests.append(test_jpeg1)
    tests.append(test_jpeg2)
    tests.append(test_jpeg3)
