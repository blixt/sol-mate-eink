# Sol Mate e-Paper Display ☀️

I initially made [the ☀️ Sol Mate GPT](https://chatgpt.com/g/g-QIydQSFRm-sol-mate), but it didn't take too long until I wondered what it would look like on [an e-Paper display](https://www.amazon.com/dp/B0BMQ83W7W).

![Picture of the screen installed with a wooden frame](https://github.com/user-attachments/assets/dbd29ded-63bb-4075-aca4-658bf9e4e0f5)

The script to update the screen takes a location (maybe your own, maybe your best friend's, or even a fictional place!) and get the weather for that location, then generate an illustration of the location including the current weather and lighting conditions. So if it's raining, there will be people with umbrellas in the picture, and so on. If you do generate for a fictional location, the weather service will be given the latitude/longitude of the most similar place on Earth (according to GPT). The illustrations are rendered using Dall-E 3. This is why an OpenAI API token is necessary to run it.

This repository contains all the code that was needed to generate and display a weather report for any specified location on a Raspberry Pi with an attached Waveshare e-Paper display.

## Hardware

- [Raspberry Pi 5](https://www.raspberrypi.com/products/raspberry-pi-5/)
- [Waveshare e-Paper 7.3" display](https://www.amazon.com/dp/B0BMQ83W7W) (code needs to be updated for other sizes)

## More pictures

- [3 more nice examples](https://x.com/blixt/status/1812941960451399909)
- [3D-printing the case](https://x.com/blixt/status/1811077705804169416)
- [4 examples, some with more color](https://x.com/blixt/status/1797317001372750301)
- [The setup, without the box](https://x.com/blixt/status/1796616909611278356)
- [Video of the thinness of the display](https://x.com/blixt/status/1797350136080699837)

## Software & Usage

This should all run on your Raspberry Pi.

I recommend setting up a virtual environment for Python, [such as uv](https://github.com/astral-sh/uv), first. Here are the instructions for if you're using `uv` (to be run inside the clone of this repo):

```sh
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Without `uv`:

```sh
python -m venv .
source .venv/bin/activate
pip install -r requirements.txt
```

You will need to specify an `OPENAI_API_KEY` environment variable. For your convenience, the code will load environment variables from a `.env` file in the current working directory.

Now you can use the `control.py` script to generate an image and show it on the screen:

```sh
python control.py show Barcelona
```

[Waveshare recommends](https://www.waveshare.com/wiki/7.3inch_e-Paper_HAT_(F)_Manual#Precautions) you don't leave the same image on the display for too long.

Use the `clear` command to clear it:

```sh
python control.py clear
```

I set up a cron job (`crontab -e`) to update the image two times per day, but keep in mind this can end up costing a non-trivial amount:

```crontab
0 8 * * * cd ~/src/sol-mate-eink && .venv/bin/python control.py show Barcelona
0 18 * * * cd ~/src/sol-mate-eink && .venv/bin/python control.py show Barcelona
0 2 * * * cd ~/src/sol-mate-eink && .venv/bin/python control.py clear
```

(You'll need to tweak the paths for your setup, of course.)

## Backend

Feel free to use the private API I hosted to get the weather if you're not going to hammer it. I also use this backend for my GPT. However, if you have high volume ideas in mind, please self-host it! The source code is here:

https://github.com/blixt/sol-mate

## Having issues?

I'd love to help if I can – [reach out on Twitter](https://twitter.com/blixt) or create an issue in this repo!
