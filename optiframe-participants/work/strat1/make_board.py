"""Generate an A4 calibration board at exact nominal scale; print at 100%."""
import argparse
from io import BytesIO
import sys
from pathlib import Path

import cv2
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared.geometry import LOCAL, board_image, board_size, load_spec, write_image


def create(output):
    output.mkdir(parents=True, exist_ok=True)
    spec = load_spec()
    pixels_per_mm = 600 / 25.4
    image = board_image(spec, pixels_per_mm)
    write_image(output / "charuco_board.png", image)
    _, encoded = cv2.imencode(".png", image)
    width, height = board_size(spec)
    document = Canvas(str(output / "charuco_board.pdf"), pagesize=A4)
    document.setTitle("OptiFrame - metric calibration board")
    document.setFont("Helvetica-Bold", 16)
    document.drawString(27 * mm, 274 * mm, "OptiFrame - calibration board")
    document.setFont("Helvetica", 10)
    document.drawString(27 * mm, 265 * mm, "A4. Print at 100%. Disable fit-to-page. Cut only the white window.")
    origin_x, origin_y = 27 * mm, 115 * mm
    document.drawImage(ImageReader(BytesIO(encoded.tobytes())), origin_x, origin_y,
                       width=width * mm, height=height * mm)
    document.setFont("Helvetica", 9)
    document.drawString(27 * mm, 106 * mm, "13 x 11 squares. Squares: 12 mm. Markers: 9 mm. Window: 84 x 60 mm.")
    document.drawString(27 * mm, 100 * mm, "Board: 156 x 132 mm. Keep flat. Place the lens inside the window.")
    document.drawString(27 * mm, 88 * mm, "NASAL side: RIGHT. Define the lens horizontal axis before capture.")
    document.setLineWidth(0.4)
    document.line(27 * mm, 76 * mm, 99 * mm, 76 * mm)
    for position in [27, 99]:
        document.line(position * mm, 74 * mm, position * mm, 78 * mm)
    document.drawString(27 * mm, 68 * mm, "Check this span with a calliper: 72.0 +/- 0.2 mm.")
    document.drawString(27 * mm, 61 * mm, "Digital dimensions are nominal; physical printer scale is NOT verified.")
    document.setFont("Helvetica", 8)
    document.drawString(27 * mm, 47 * mm, "OpenCV DICT_5X5_100. Generated locally. Synthetic tests do not validate real lenses.")
    document.showPage()
    document.save()
    return output / "charuco_board.pdf"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=LOCAL / "board")
    print(create(parser.parse_args().output))
