#!/usr/bin/env python3
"""
Threshold a PNG image to black and white, then make white pixels transparent.

Usage:
    python prepare_png.py <input.png> [output.png] [--threshold 128]

If output is omitted, the input file is overwritten in place.

Written entirely by claude sonnet 4.6
"""

import argparse
import sys
from pathlib import Path

from PIL import Image


def threshold_and_transparent(
    input_path: Path,
    output_path: Path,
    threshold: int = 128,
) -> None:
    """
    Convert a PNG to black-and-white and make white pixels transparent.

    Pixels whose luminance is >= threshold become transparent; all others
    become opaque black.

    Parameters
    ----------
    input_path : Path
        Source PNG file.
    output_path : Path
        Destination PNG file (RGBA).
    threshold : int
        Luminance cutoff in [0, 255].  Pixels at or above this value are
        treated as white and made transparent.
    """
    img = Image.open(input_path).convert("RGBA")
    grayscale = img.convert("L")

    result = Image.new("RGBA", img.size)
    pixels = grayscale.load()
    result_pixels = result.load()

    width, height = img.size
    for y in range(height):
        for x in range(width):
            lum = pixels[x, y]
            if lum >= threshold:
                result_pixels[x, y] = (255, 255, 255, 0)  # transparent
            else:
                result_pixels[x, y] = (0, 0, 0, 255)  # opaque black

    result.save(output_path, format="PNG")
    print(f"Saved: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Threshold a PNG to black/white and make white parts transparent.")
    parser.add_argument("input", type=Path, help="Input PNG file")
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        default=None,
        help="Output PNG file (default: overwrite input)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=128,
        metavar="N",
        help="Luminance threshold 0-255 (default: 128). Pixels >= N become transparent.",
    )
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Error: '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    if not 0 <= args.threshold <= 255:
        print("Error: --threshold must be between 0 and 255.", file=sys.stderr)
        sys.exit(1)

    output = args.output if args.output is not None else args.input
    threshold_and_transparent(args.input, output, args.threshold)


if __name__ == "__main__":
    main()
