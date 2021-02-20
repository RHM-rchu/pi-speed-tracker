# This version is not Officially ready. I still have much to do to make it usable on a new system without custom configs. Come back soon, or use if you want to figure things out on your own.

## Version (version .0.1)

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
* Opencv 4.1.0.25
* python3
## Usage

1. checkout this repo
```
git clone https://github.com/RHM-rchu/pi-speed-tracker
```
2. Install python virtual environment 
```
sudo pip install virtualenv virtualenvwrapper
```
create session source scripts
```
cat <<EOT >> ~/.bashrc

# virtualenv and virtualenvwrapper
export WORKON_HOME=$HOME/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh

EOT
```
Source the above environment variables 
```
source ~/.bashrc
```
create a new python environment
```
mkvirtualenv py3cv4 -p python3
```
load the environment
```
workon py3cv4
```
3. Update, Upgrade, then install requirements 
```
sudo apt-get update && sudo apt-get upgrade
```
requirements
```
sudo apt-get -y install libjpeg-dev libtiff5-dev libjasper-dev libpng-dev libavcodec-dev libavformat-dev \
libswscale-dev libv4l-dev libxvidcore-dev libx264-dev libfontconfig1-dev libcairo2-dev libgdk-pixbuf2.0-dev \
libpango1.0-dev libgtk2.0-dev libgtk-3-dev libatlas-base-dev gfortran libhdf5-dev libhdf5-serial-dev \
libhdf5-103 libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5 python3-dev
```
4. Install OpenCV 4 and Python 3 on the Pi. Ensure all dependencies have been installed.
```
pip3 install -r pip.requirments.txt
```
5. Ensure your hardware is setup and installed, and you have your cam pointing in the area you want to monitor. Enable the webcam in the `raspi-config`
```
sudo raspi-config
```
    1. Interface Options
    2. Camera
    3. <yes>
    4. <OK>
    5. <Finish> and exit
    6. Reboot
![DB Sample](html/assets/sample_enable_picam.png?raw=true "DB Sample")
6. run the calibrator.py app, This pops a video player where you can draw a triangle in the video player, select the region you want to monitor. This automatically set the coordinate in a file called `_configs_coords.py`. It's advised that you only use this program to set the Region Of Interest (ROI), which is the road area you want to monitor.
```
python3 calibrator.py
```
7. Measure the right and left corners that you mark when calibrating from the camera lens to the street. Set the these measurements into the `_configs.py`
8. Edit the configs to set speed limits and other values to customize to your taste.

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

7. Optional, install sqlite
```
sudo apt-get install sqlite3 libsqlite3-dev
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


