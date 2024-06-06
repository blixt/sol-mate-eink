# Sol Mate e-Paper Display ☀️

I initially made [the ☀️ Sol Mate GPT](https://chatgpt.com/g/g-QIydQSFRm-sol-mate), but it didn't take too long until I wondered what it would look like on [an e-Paper display](https://www.amazon.com/dp/B0BMQ83W7W).

![GO7dhuhWMAANHTS](https://github.com/blixt/sol-mate-eink/assets/158591/d32dc678-6b6f-4424-b3b0-84c9e74b53f1)

This repository contains all the code that was needed to generate and display a weather report for any specified location on a Raspberry Pi with an attached Waveshare e-Paper display.

You will need to specify an `OPENAI_API_KEY` environment variable. The code will load environment variables from a `.env` file in the same directory.

## Hardware

- Raspberry Pi 5
- Waveshare e-Paper 7.3" display (code needs to be updated for other sizes)

## Usage

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

Now you can use the `control.py` script to generate an image and show it on the screen:

```sh
python control.py show Barcelona
```

Don't leave the same image on the display for too long. Use the `clear` command to clear it:

```sh
python control.py clear
```

I set up a cron job (`crontab -e`) to update the image two times per day, but keep in mind this can end up costing a non-trivial amount:

```crontab
0 8 * * * cd ~/src/sol-mate-eink && ./venv/bin/python control.py show Barcelona
0 18 * * * cd ~/src/sol-mate-eink && ./venv/bin/python control.py show Barcelona
0 2 * * * cd ~/src/sol-mate-eink && ./venv/bin/python control.py clear
```
