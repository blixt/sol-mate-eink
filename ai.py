from dotenv import load_dotenv
import json
import logging
from openai import OpenAI
from PIL import Image
import requests

from epaper import convert_image_to_palette, fit_image_to_canvas, EPD_HEIGHT, EPD_WIDTH


# Load environment variables from a .env file
load_dotenv()
client = OpenAI()


def get_parameters_for_location(location: str) -> dict[str, str | float]:
    prompt = f"""
Get the weather data for {location}. If the location is not on Earth (fictional
or otherwise), pick the place on Earth that is most visually similar to the
location. Before you get the weather, reason about which temperature unit is
most likely to be used at the location in question. That is the temperature unit
you should use when getting the weather.
"""

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": prompt.strip(),
            }
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Retrieve the weather for the provided location.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "latitude": {
                                "type": "number",
                                "description": "The latitude of the location to get the weather for.",
                            },
                            "longitude": {
                                "type": "number",
                                "description": "The longitude of the location to get the weather for.",
                            },
                            "timezone": {
                                "type": "string",
                                "description": "The timezone that is in use at the specified latitude and longitude.",
                            },
                            "temperature_unit": {
                                "type": "string",
                                "description": "The most appropriate unit for temperature given the location.",
                                "enum": ["celsius", "fahrenheit"],
                            },
                        },
                        "required": [
                            "latitude",
                            "longitude",
                            "timezone",
                            "temperature_unit",
                        ],
                    },
                },
            }
        ],
        tool_choice={"type": "function", "function": {"name": "get_weather"}},
    )

    message = completion.choices[0].message
    assert message.tool_calls
    tool_call = message.tool_calls[0]
    arguments = json.loads(tool_call.function.arguments)
    return arguments


def get_image_prompt(location: str):
    weather_params = get_parameters_for_location(location)
    logging.info(f"Parameters for {location}: {weather_params}")
    weather = requests.get(
        "https://blixt--sol-mate-weather-api.modal.run/current", weather_params
    ).json()
    logging.info(f"Weather for {location}: {weather['status']}")

    prompt = f"""
Here is the weather for the location "{location}":

{weather["status"]}

Use Dall-E to generate a beautiful illustration of the location in a random
style that goes well for this situation, in the style of a wide post card
filling up the entire image. Try to describe a scene that is iconic and
aesthetically pleasing for the location specified above, but also one that can
showcase the weather. If it makes sense, use a scene that will have something
distinctly green/blue/red/yellow/orange.

Prefer to focus on one specific scene at the location in detail rather than
mixing up things that might appear at different places around the location. If
the location is something very local like a neighborhood, try to focus on that
in the image. Describe the weather conditions with visual keywords so that they
are clearly visible in the elements of the illustration. Also make sure to
describe the color of the sky based on the sun (or what it should look like if
only the moon is visible). Do not mention the exact time, instead use a more
general word like "morning", "afternoon" or "midnight" and focus on including
visual keywords that would clearly illustrate the place at that time. Also
include "at night" if it's nighttime.

The name of the location and MOST IMPORTANTLY, the temperature MUST feature as
prominently written text on top of the illustration. There should be no other
text except for the location name and temperature. For the text, use large
typography, in a style inspired by the location, weather and time of day. When
describing the typography, use strong visual keywords rather than vague
stylistic references. Make sure that the instructions for the text are clearly
included in the prompt.

There should be people in the image and at least some of them should be doing
something interesting. Describe what the people are wearing or doing based on
the weather conditions, but only mention umbrellas if it's raining, or jackets
if it's chilly, and so on, otherwise don't mention those things. Also include
any celebrations people at the location might normally celebrate based on the
current date, otherwise don't mention it.

Make sure to describe every part of the image in detail so that the location can
be accurately represented. If there should be buildings, describe how dense and
where they are. If there should be nature describe what kinds of natural
elements there are. If there are things happening or activities, describe them
in detail. Avoid abstract or indirect terms, preferring words that visually
describe what should be in the illustration in a very literal way.

The prompt sent to Dall-E should be very detailed and around 150 words long.
Avoid elaborate words and do not use negatives.
"""

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt.strip()}],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "generate_dalle_image",
                    "description": "Use Dall-E to generate an image with the given prompt.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The prompt to generate an image for. It should be very detailed and around 150 words long.",
                            },
                        },
                        "required": ["prompt"],
                    },
                },
            }
        ],
        tool_choice={"type": "function", "function": {"name": "generate_dalle_image"}},
    )

    message = completion.choices[0].message
    assert message.tool_calls
    tool_call = message.tool_calls[0]
    arguments = json.loads(tool_call.function.arguments)
    return arguments["prompt"]


def get_image(prompt: str) -> Image.Image:
    response = client.images.generate(
        model="dall-e-3", prompt=prompt, n=1, size="1792x1024", quality="hd"
    )

    image_url = response.data[0].url
    assert image_url is not None

    if response.data[0].revised_prompt:
        logging.info(f"Revised prompt: {response.data[0].revised_prompt}")

    # Download the image to a temporary location
    temp_image_path = "/tmp/temp_image.png"
    with requests.get(image_url, stream=True) as r:
        r.raise_for_status()
        with open(temp_image_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    image = Image.open(temp_image_path)
    image = fit_image_to_canvas(image, (EPD_WIDTH, EPD_HEIGHT))
    image = convert_image_to_palette(image)

    return image
