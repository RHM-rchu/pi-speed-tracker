# Car Speed Detection - carspeed.py (version 2.0)

## Credits

Logic and Core inspired by
Full program details at:   https://gregtinkers.wordpress.com/2016/03/25/car-speed-detector/

## Description

This program for the Raspberry Pi 4 running Raspbian determines the speed of cars moving through the Picamera's field of view. This is meant to be in side profile view so cars cross the field of view from left to right and right to left. Data is gathered in a few different ways, CSV File, SQLight3 database, and an image is saved.

![Sample Image](html/assets/sample_snap.jpg?raw=true "Sample Image")


## Features
* All configs are in one file `_configs.py`, simply edit this file and start the Apps
* Data is stored in a SQLight3 database. No worries if you don't know SQLight, this is behind the scenes. The database is creation and updates are handled by the app. The data is primarily used for reporting by the web server, but if you have SQL skills and know a bit of SQLight3 you can pull you own report. ![DB Sample](html/assets/sample_db.png?raw=true "DB Sample")
* CSV files are generated if you want to export into Excel and don't know SQl, but want custom reports. Each time the App start a new CSV file is created
```
data/
├── carspeed_20210208_0631.csv
├── ...
└── carspeed_20210213_0952.csv
```
* Images are stored in folders by `YYYY/MM/DD`
```
media
└── images
    └── 2021
        └── 02
            ├── 08
            ├── 09
            ├── 10
            ├── 11
            └── 12
```
* Once setup and configure all you should ever need to use is the Web GUI, to view data in real-time. ![Web GUI Sample](html/assets/sample_web.png?raw=true "Web GUI Sample")

## Requirements

* Raspberry Pi 4 2gb RAM (Recommended)
    * Raspbian Buster - should work with any, but what I tested with
* Picamera
* Opencv 4.5.1
* python3/pip3
    * packages: mako sqlite3
## Usage

1. Install OpenCV 4 and Python 3 on the Pi. 
2. Ensure your hardware is setup and installed, and you have your cam pointing in the area you want to monitor. Enable the webcam in the `raspi-config`
3. checkout this repo
4. run the calibrator.py app, select the region you want, set the coordinate in the `_configs.py`. This also saves your image with the info at `media/images/calibrator.jpg`. Keyboard press `q` to exit when done.
```
python3 calibrator.py
```
5. Measure the right and left corners that you mark when calibrating from the camera lens to the street. Set the these measurements into the `_configs.py`
6. Edit the configs to set speed limits and other values to customize to your taste.

## running the webserver
This starts the webserver to view data as it comes in. if left to the default open the page in a brwoser at http://[server_ip_or_localhost]:8080 
```
python3 web-server.py
```
*Note* three are shell scripts in `*.sh`, used if you want to enable the webserver and speed-tracker app to be managed by `systemctl`. How to do this is outside the scope of these instructions. I'll create another read me for that some other time.
```
scripts/
├── load.py.virtualenv.sh
├── speed-tracker.sh
├── tmp.text.sh
└── web-server.sh
```

## running the app
This start the tracker to run the picam to start tracking speeds
```
python3 speed-tracker.py
```
if config `SHOW_IMAGE = True` and you launch in Raspberry Pi desktop environment you will get a preview video window. If you do not have the desktop environment running. If you are in the terminal always append `--show_image=False` to the startup to ensure you don't get error from the video player trying to open. 
```
python3 speed-tracker.py --show_image=False
```

*I know the readme is incomplete but I will add as I have time*


