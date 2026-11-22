#!/usr/bin/env python3
"""The picture that tastes of one ingredient.

Writes one image of food to /output/entry.png: a single halved jammy egg,
its molten golden yolk pouring in a glossy ribbon, chopsticks lifting the
top half, steam rising, against a dark background with warm golden light.
One ingredient, photographed photorealistically, made to look delicious.

The image is baked into the repository as image.jpg (the sandbox has no
network, so the program cannot fetch anything at run time). This program
simply copies it to /output/entry.png and validates it against the gate:
a whole PNG or JPEG, at most 1,048,576 bytes and 1024 by 1024 pixels.

Standard library only. No network. No arguments.
"""

import os
import shutil
import struct
import sys

MAX_BYTES = 1_048_576
MAX_DIMENSION = 1024
SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image.jpg")
DEST_DIR = "/output"
DEST = os.path.join(DEST_DIR, "entry.png")


def jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Return (width, height) of a JPEG by parsing its SOF marker."""
    if len(data) < 2 or data[:2] != b"\xff\xd8":
        raise ValueError("not a JPEG (missing SOI marker)")
    pos = 2
    while pos + 9 <= len(data):
        if data[pos] != 0xFF:
            raise ValueError("corrupt JPEG marker stream")
        marker = data[pos + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        if pos + 4 > len(data):
            raise ValueError("truncated JPEG segment")
        length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):  # SOF0/1/2: precision, height, width
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            return width, height
        pos += 2 + length
    raise ValueError("no SOF marker found in JPEG")


def main() -> int:
    with open(SOURCE, "rb") as f:
        data = f.read()

    if not data.startswith(b"\xff\xd8\xff"):
        print("error: image.jpg is not a JPEG", file=sys.stderr)
        return 1
    if len(data) > MAX_BYTES:
        print(f"error: image is {len(data)} bytes, over {MAX_BYTES}", file=sys.stderr)
        return 1
    width, height = jpeg_dimensions(data)
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        print(f"error: image is {width}x{height}, over {MAX_DIMENSION}px",
              file=sys.stderr)
        return 1

    os.makedirs(DEST_DIR, exist_ok=True)
    shutil.copyfile(SOURCE, DEST)

    # Verify what was actually written.
    with open(DEST, "rb") as f:
        written = f.read()
    assert written == data, "written bytes differ from source"
    print(f"wrote {DEST}: JPEG {width}x{height}, {len(written)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
