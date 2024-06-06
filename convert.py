from PIL import Image
import sys
from epaper import convert_image_to_palette, fit_image_to_canvas


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert.py <input_image_path> [<output_image_path>]")
        sys.exit(1)

    input_image_path = sys.argv[1]
    output_image_path = sys.argv[2] if len(sys.argv) > 2 else "output.png"

    # Load the image
    image = Image.open(input_image_path)
    # Resize and fit the image to the canvas
    canvas_size = (800, 480)
    image = fit_image_to_canvas(image, canvas_size)
    # Convert the fitted image to the palette
    image = convert_image_to_palette(image)
    # Save the final image
    image.save(output_image_path)
