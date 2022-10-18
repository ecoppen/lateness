<h1 align="center">
Lateness
</h1>

<p align="center">
A python (3.10+) and Fastapi script to log lateness
</p>
<p align="center">
<img alt="GitHub Pipenv locked Python version" src="https://img.shields.io/github/pipenv/locked/python-version/ecoppen/lateness">
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

uvicorn lateness.main:app --reload

### Prerequisites
This program was written to connect to a school API to log student lateness using a touch screen, card reader and Raspberry Pi.
- Raspberry pi - `https://thepihut.com/products/raspberry-pi-4-model-b`
- Touchscreen - `https://thepihut.com/products/official-raspberry-pi-7-touchscreen-display`
- Smartcard reader - `https://www.amazon.co.uk/Non-Contact-Drive-Free-Compatible-Multiple-Systems-125Khz-ID/dp/B08ZYDBYCL/`

### Installation instructions 

- Clone the repo `git clone https://github.com/ecoppen/lateness.git`
- Go into the lateness folder `cd lateness`
- Install pipenv `pip install pipenv`
- Adjust the Pipfile if you want to use Python 3.8 or 3.9 (last line) `nano Pipfile`
- Install the requirements `pipenv install`
- Edit the boot shell script with the correct home directory `nano boot.sh`
- Make the boot file executable `chmod +x boot.sh`
- Go into the config folder `cd config`
- Create a config json file from the example `cp config.json.example config.json`
- Adjust the config file to your needs `nano config.json`
- Add the autostart routine to the Raspberry Pi to start boot.sh `nano ~/.config/autostart/lateness.desktop`
```
[Desktop Entry]
Type=Application
Name=Lateness
Exec=/bin/bash /path/to/boot.sh
```
- Edit the autostart routine to start a chromium browser in full screen `sudo nano /etc/xdg/lxsession/LXDE-pi/autostart`
```
@xset s off
@xset -dpms
@xset s noblank
@chromium-browser --kiosk http://127.0.0.1:8000
```
