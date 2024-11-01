import logging
import sys
import time

from ai import get_image_dalle, get_image_recraft, get_image_prompt
from epaper import EPaperDisplay


logging.basicConfig(level=logging.INFO)


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("show", "clear"):
        print("Usage: python control.py <command> [location]")
        print("Available commands:")
        print("  show <location>  - Display the weather for the specified location.")
        print("  clear            - Clear the e-paper display.")
        sys.exit(1)

    command = sys.argv[1]

    if command == "show" and len(sys.argv) < 3:
        print("Usage: python control.py show <location>")
        sys.exit(1)

    if command == "clear" and len(sys.argv) > 2:
        print("Usage: python control.py clear")
        sys.exit(1)

    epd = EPaperDisplay()

    try:
        logging.info("Initializing the display")
        epd.initialize()

        if command == "show":
            location = sys.argv[2]
            logging.info(f"Getting the image prompt for {location}")
            prompt = get_image_prompt(location)
            logging.info(f"Prompt: {prompt}")

            logging.info("Generating the image")
            image = get_image_dalle(prompt)

            logging.info("Displaying the image")
            epd.display(image)
        elif command == "clear":
            logging.info("Clearing the display")
            epd.clear()

    except KeyboardInterrupt:
        logging.info("Interrupted by user")
    finally:
        logging.info("Putting the display to sleep")
        epd.sleep()


if __name__ == "__main__":
    main()
