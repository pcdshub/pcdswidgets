"""
Threshold a png and give it a transparent background, adding it to the beamline diagrams folder.

We want the images used here to have transparent backgrounds so that we can draw
different background colors etc. behind the diagrams without saving many
different image files.

If we ever switch to using e.g. SVGs this will no longer be needed.

Usage:
    pixi run process-diagram-png <input.png> [--threshold 128]

This was written with the assistance of claude sonnet 4.6
"""

import argparse
import sys
from pathlib import Path

from PIL import Image


def threshold_and_transparent(
    input_path: Path,
    threshold: int,
) -> Image.Image:
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

    Returns
    -------
    image : Image
        The PIL Image object.
    """
    img = Image.open(input_path).convert("RGBA")
    grayscale = img.convert("L")

    result = Image.new("RGBA", img.size)
    gray_pixels = grayscale.load()
    result_pixels = result.load()

    if gray_pixels is None or result_pixels is None:
        raise RuntimeError(f"Unable to load image data from {input_path}")

    width, height = img.size
    for y in range(height):
        for x in range(width):
            lum = gray_pixels[x, y]
            if not isinstance(lum, (float, int)):
                raise TypeError("Color data found in greyscale: aborting")
            if lum >= threshold:
                result_pixels[x, y] = (255, 255, 255, 0)  # transparent
            else:
                result_pixels[x, y] = (0, 0, 0, 255)  # opaque black

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="process-diagram-png",
        description="Threshold a png and give it a transparent background, adding it to the beamline diagrams folder.",
    )
    parser.add_argument("input", type=Path, help="Input PNG file")
    parser.add_argument(
        "--threshold",
        type=int,
        default=128,
        help="Luminance threshold 0-255 (default: 128). Pixels >= N become transparent.",
    )
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Error: '{args.input}' not found.", file=sys.stderr)
        return 1

    if not 0 <= args.threshold <= 255:
        print("Error: --threshold must be between 0 and 255.", file=sys.stderr)
        return 1

    output_path = Path(__file__).parent / "diagram" / args.input.name
    if output_path.is_file():
        response = input(f"Warning: {output_path} already exists. Would you like to overwrite it?\n(y/n)\n")
        if not response.lower().startswith("y"):
            print("Aborting", file=sys.stderr)
            return 1

    image = threshold_and_transparent(args.input, args.threshold)
    image.save(output_path, format="PNG")
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
