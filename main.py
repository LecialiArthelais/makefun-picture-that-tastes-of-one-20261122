"""The picture that tastes of one ingredient.

A single halved jammy egg: the top half lifted by chopsticks, a glossy
ribbon of molten golden yolk pouring down into the bottom half, steam
rising, against a dark near-black background in warm golden light.
One ingredient, photoreal, nothing else on the plate.

This program is the entrypoint for the make.fun bounty
"The picture that tastes of one ingredient". It copies the baked-in
image (``image.jpg``, next to this file) to ``/output/entry.png`` after
validating it against the bounty gate:

* the image must be a real JPEG (SOI magic bytes ``FF D8 FF``),
* it must be at most 1,048,576 bytes,
* its width and height must each be at most 1024 pixels.

Standard library only. No network access, no arguments, no side
effects beyond writing the single output file.
"""

import os
import struct
import sys

MAX_BYTES = 1_048_576
MAX_DIMENSION = 1024
OUTPUT_PATH = "/output/entry.png"
JPEG_SOI = b"\xff\xd8\xff"


def fail(message):
    """Print an error to stderr and exit with status 1."""
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def jpeg_dimensions(data):
    """Parse JPEG SOF markers (SOF0/SOF1/SOF2) and return (width, height).

    Walks the marker segments after the SOI; the first Start-Of-Frame
    marker carries the image height and width as big-endian uint16s.
    Returns None if no SOF marker can be found.
    """
    pos = 2  # skip the SOI marker
    while pos + 9 <= len(data):
        if data[pos] != 0xFF:
            return None
        marker = data[pos + 1]
        if marker == 0xD8:  # SOI (should not repeat, but tolerate it)
            pos += 2
            continue
        if marker == 0xD9 or marker == 0xDA:  # EOI / SOS: no SOF after this
            return None
        if pos + 4 > len(data):
            return None
        segment_length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        if segment_length < 2 or pos + 2 + segment_length > len(data):
            return None
        if marker in (0xC0, 0xC1, 0xC2):  # SOF0, SOF1, SOF2
            height, width = struct.unpack(
                ">HH", data[pos + 5:pos + 9]
            )
            return width, height
        pos += 2 + segment_length
    return None


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(here, "image.jpg")

    if not os.path.isfile(source_path):
        fail(f"image not found: {source_path}")

    with open(source_path, "rb") as handle:
        data = handle.read()

    if not data:
        fail("image is empty")
    if len(data) > MAX_BYTES:
        fail(
            f"image is {len(data)} bytes, over the {MAX_BYTES} byte limit"
        )
    if not data.startswith(JPEG_SOI):
        fail("image is not a JPEG (missing SOI magic bytes)")

    dimensions = jpeg_dimensions(data)
    if dimensions is None:
        fail("could not parse JPEG dimensions (no SOF marker found)")
    width, height = dimensions
    if width <= 0 or height <= 0:
        fail(f"image has invalid dimensions {width}x{height}")
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        fail(
            f"image is {width}x{height}, over the "
            f"{MAX_DIMENSION}x{MAX_DIMENSION} limit"
        )

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "wb") as handle:
        handle.write(data)

    with open(OUTPUT_PATH, "rb") as handle:
        written = handle.read()
    if written != data:
        fail("output verification failed: bytes do not match the source")

    print(
        f"Wrote {OUTPUT_PATH}: JPEG {width}x{height}, "
        f"{len(data)} bytes"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
