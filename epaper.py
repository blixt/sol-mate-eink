from collections import namedtuple
from PIL import Image
import time
from typing import List, Tuple

# Display resolution
EPD_WIDTH = 800
EPD_HEIGHT = 480

# Commands
POWER_OFF = 0x02
POWER_ON = 0x04
DEEP_SLEEP = 0x07
DATA_START_TRANSMISSION = 0x10
DISPLAY_REFRESH = 0x12
IPC = 0x13
TSE = 0x41
AGID = 0x86
CMDH = 0xAA
CCSET = 0xE0
TSSET = 0xE6

# Data
DEEP_SLEEP_DATA = 0xA5

# Hardware interface pins
RST_PIN = 17
DC_PIN = 25
CS_PIN = 8
BUSY_PIN = 24
PWR_PIN = 18

Color = namedtuple("Color", ["r", "g", "b"])
_palette = namedtuple(
    "_palette", ["black", "white", "green", "blue", "red", "yellow", "orange"]
)

PALETTE = _palette(
    black=Color(0, 0, 0),
    white=Color(255, 255, 255),
    green=Color(0, 255, 0),
    blue=Color(0, 0, 255),
    red=Color(255, 0, 0),
    yellow=Color(255, 255, 0),
    orange=Color(255, 128, 0),
)


class EPaperDisplay:
    def __init__(self) -> None:
        import spidev
        import gpiozero

        self.spi = spidev.SpiDev()
        self.gpio_rst = gpiozero.LED(RST_PIN)
        self.gpio_dc = gpiozero.LED(DC_PIN)
        self.gpio_pwr = gpiozero.LED(PWR_PIN)
        self.gpio_busy = gpiozero.Button(BUSY_PIN, pull_up=False)

    def reset(self) -> None:
        self.gpio_rst.on()
        time.sleep(0.02)
        self.gpio_rst.off()
        time.sleep(0.002)
        self.gpio_rst.on()
        time.sleep(0.02)

    def send_command(self, command: int) -> None:
        self.gpio_dc.off()
        self.spi.writebytes([command])

    def send_data(self, data: int) -> None:
        self.gpio_dc.on()
        self.spi.writebytes([data])

    def send_bulk_data(self, data: List[int]) -> None:
        self.gpio_dc.on()
        self.spi.writebytes2(data)

    def wait_until_idle(self) -> None:
        while self.gpio_busy.value == 0:
            time.sleep(0.005)

    def refresh_display(self) -> None:
        self.send_command(POWER_ON)
        self.wait_until_idle()

        self.send_command(DISPLAY_REFRESH)
        self.send_data(0x00)
        self.wait_until_idle()

        self.send_command(POWER_OFF)
        self.send_data(0x00)
        self.wait_until_idle()

    def initialize(self) -> int:
        self.gpio_pwr.on()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 4000000
        self.spi.mode = 0b00
        self.reset()
        self.wait_until_idle()
        time.sleep(0.03)

        init_commands: List[tuple[int, List[int]]] = [
            (CMDH, [0x49, 0x55, 0x20, 0x08, 0x09, 0x18]),
            (0x01, [0x3F, 0x00, 0x32, 0x2A, 0x0E, 0x2A]),
            (0x00, [0x5F, 0x69]),
            (0x03, [0x00, 0x54, 0x00, 0x44]),
            (0x05, [0x40, 0x1F, 0x1F, 0x2C]),
            (0x06, [0x6F, 0x1F, 0x1F, 0x22]),
            (0x08, [0x6F, 0x1F, 0x1F, 0x22]),
            (IPC, [0x00, 0x04]),
            (0x30, [0x3C]),
            (TSE, [0x00]),
            (0x50, [0x3F]),
            (0x60, [0x02, 0x00]),
            # Resolution (0x0320 = 800, 0x01E0 = 480)
            (0x61, [0x03, 0x20, 0x01, 0xE0]),
            (0x82, [0x1E]),
            (0x84, [0x00]),
            (AGID, [0x00]),
            (0xE3, [0x2F]),
            (CCSET, [0x00]),
            (TSSET, [0x00]),
        ]

        for command, data in init_commands:
            self.send_command(command)
            for value in data:
                self.send_data(value)

        return 0

    def display(self, image: Image.Image) -> None:
        width, height = image.size
        if width != EPD_WIDTH or height != EPD_HEIGHT:
            raise Exception(
                "Invalid image dimensions: %d x %d, expected %d x %d"
                % (width, height, EPD_WIDTH, EPD_HEIGHT)
            )

        # Assert that the image is a palette-based image with the PALETTE colors.
        palette = image.getpalette()
        if not palette or image.mode != "P":
            raise Exception("Image is not in palette mode")
        flat_palette = [int(value) for color in PALETTE for value in color]
        if palette[: len(flat_palette)] != flat_palette:
            raise Exception("Image palette does not match the expected PALETTE colors")

        pixels = bytearray(image.tobytes("raw"))
        buf = [(pixels[i] << 4) | pixels[i + 1] for i in range(0, len(pixels), 2)]
        assert len(buf) == int(EPD_WIDTH * EPD_HEIGHT / 2)

        self.send_command(DATA_START_TRANSMISSION)
        self.send_bulk_data(buf)
        self.refresh_display()

    def clear(self, color: int = 1) -> None:
        color = color << 4 | color
        self.send_command(DATA_START_TRANSMISSION)
        self.send_bulk_data([color] * int(EPD_HEIGHT * EPD_WIDTH / 2))
        self.refresh_display()

    def sleep(self) -> None:
        self.send_command(DEEP_SLEEP)
        self.send_data(DEEP_SLEEP_DATA)
        time.sleep(2)
        self.spi.close()
        self.gpio_rst.off()
        self.gpio_dc.off()
        self.gpio_pwr.off()
        # If you intend to use this instance again, these shouldn't be closed.
        self.gpio_rst.close()
        self.gpio_dc.close()
        self.gpio_pwr.close()
        self.gpio_busy.close()


def fit_image_to_canvas(
    image: Image.Image, canvas_size: Tuple[int, int], contain=False
) -> Image.Image:
    """
    Returns a new image that is exactly the size of `canvas_size`. If `contain`
    is True, the input `image` will be fit inside of the canvas boundary
    (centered); otherwise, `image` will be made to cover the entire canvas while
    retaining as much of it as possible.
    """
    image_ratio = image.width / image.height
    canvas_ratio = canvas_size[0] / canvas_size[1]

    if contain:
        if image_ratio > canvas_ratio:
            new_width = canvas_size[0]
            new_height = round(new_width / image_ratio)
        else:
            new_height = canvas_size[1]
            new_width = round(new_height * image_ratio)
    else:
        if image_ratio > canvas_ratio:
            new_height = canvas_size[1]
            new_width = round(new_height * image_ratio)
        else:
            new_width = canvas_size[0]
            new_height = round(new_width / image_ratio)

    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    new_image = Image.new("RGB", canvas_size, (255, 255, 255))
    new_image.paste(
        image, ((canvas_size[0] - new_width) // 2, (canvas_size[1] - new_height) // 2)
    )

    return new_image


def convert_image_to_palette(image: Image.Image) -> Image.Image:
    """
    Returns a new version of `image` that only uses the 7 E-Paper colors.
    """
    image = image.convert("RGB")
    palette_image = Image.new("P", (1, 1), 0)
    flat_palette = [int(value) for color in PALETTE for value in color]
    palette_image.putpalette(flat_palette)
    image = image.quantize(palette=palette_image, dither=Image.Dither.FLOYDSTEINBERG)
    return image
