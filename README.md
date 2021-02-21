# A Work in progress...

## v0.4.5

## Credits

Logic and Core inspired by
Full program details at:   https://gregtinkers.wordpress.com/2016/03/25/car-speed-detector/

## Description

This program for the Raspberry Pi 4 running Raspbian determines the speed of cars moving through the Picamera's field of view. This is meant to be in side profile view so cars cross the field of view from left to right and right to left. Data is gathered in a few different ways, CSV File, SQLight3 database, and an image is saved.

![Sample Image](html/assets/sample_snap.jpg?raw=true "Sample Image")


## Features
* All configs are in one file `_configs.py`. Most config variables have comments.
* Data is stored in a SQLight3 database. No worries if you don't know SQLight, this is behind the scenes. The database is created and updates are handled by the app. The data is primarily used for reporting by the web server, but if you have SQL skills and know SQLight3 you can pull you own report. Unless you changed in the onfigs, the db is stored in `db/speed-tracker.sqlite3`. ![DB Sample](html/assets/sample_db.png?raw=true "DB Sample")
* CSV files are also generated if you want to export into Excel and don't know SQl. Each time the App start a new CSV file is created
```
data/
├── carspeed_20210208_0631.csv
├── ...
└── carspeed_20210213_0952.csv
```
* Images are stored in folders by `YYYY/MM/DD`. Each car that has a reported speed will have an image saved. Generally this image is used with the webserver, but is also documented in the SQLight database and CSV files.
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
* Once setup and configure all you should ever need to use is the Web GUI, to view data in real-time. 


View Graphs/Reports

![Sample Graphs Page](html/assets/sample_web.png?raw=true "Sample Graphs Page")


Monitor Cam status - can turn Cam on/off with the toggle switch in the header


![Sample Status Page](html/assets/sample_web2.png?raw=true "Sample Status Page")

## Requirements

* Raspberry Pi 4 2gb RAM (Recommended, 4gb would be better)
    * We do need the desktop environment to calibrate so don't go headless.
    * Raspbian Buster - should work with any, but what I tested with
* Picamera
* Opencv 4.1.0.25
* python3
* Not a whole lot but a little terminal skills is nice

## Usage
Anytime we need to run a command, assume it's in the terminal as your user account unless specified otherwise.

1. checkout this repo
```
git clone https://github.com/RHM-rchu/pi-speed-tracker
```
2. Install python virtualenv environment 
```
sudo pip install virtualenv virtualenvwrapper
```
Ensure the virtualenv loads on login.
run
```
cat <<EOT >> ~/.bashrc

# virtualenv and virtualenvwrapper
export WORKON_HOME=$HOME/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh

EOT
```
Source the above environment variables, or logout and back in
```
source ~/.bashrc
```
create a new python environment called `py3cv4` running python3
```
mkvirtualenv py3cv4 -p python3
```
load the environment
```
workon py3cv4
```
if it worked you should see something like this before you cursor in the terminal
`(py3cv4) pi@raspi-ai:~/repos/pi-speed-tracker $` note the `(py3cv4)` which is your current virtualenv

3. Update, Upgrade, then install requirements 
```
sudo apt-get update && sudo apt-get upgrade
```
Install requirements
```
sudo apt-get -y install libjpeg-dev libtiff5-dev libjasper-dev libpng-dev libavcodec-dev libavformat-dev \
libswscale-dev libv4l-dev libxvidcore-dev libx264-dev libfontconfig1-dev libcairo2-dev libgdk-pixbuf2.0-dev \
libpango1.0-dev libgtk2.0-dev libgtk-3-dev libatlas-base-dev gfortran libhdf5-dev libhdf5-serial-dev \
libhdf5-103 libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5 python3-dev
```
Optional, install sqlite
```
sudo apt-get install sqlite3 libsqlite3-dev
```
4. Install python dependencies. Ensure you are in the repo. If not already in the virtualenv run.
```
workon py3cv4
```
then run
```
pip install -r pip.requirments.txt
```
This could take about an hour if you have not run before.

5. Ensure your CAM is hooked up to you PI, and you have your cam pointing to the road. Then enable the webcam in the `raspi-config`. 
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

6. copy `_configs_sample.py` as `_configs.py`. From here anytime we manually make edits will be in `_configs.py`

7. Go to your Raspberry PI desktop environment and open a terminal. Run the calibrator.py app. This will pop a video player where you can draw a green triangle in the video player, select the region you want to monitor. This automatically set the coordinate in a file called `_configs_coords.py`. It's advised that you only use this program to set the Region Of Interest (ROI), which is the road area you want to monitor.
```
python calibrator.py
```
Draw the box around the road area to monitor. Once you are satisfied with the selection press, [ECS] key. This will save and/or create `_configs_coords.py` with the coordinates you selected for the app to monitor. No further edits are needed. This also saves an still image in `media/images/calibrator.jpg` with what you selected for reference (you will need to reference for the next step). If you move or even bump the camera you will need to repeat this step to recalibrate.
![Calibrator Sample](html/assets/sample_calibrator.png?raw=true "Calibrator Sample") to be referenced in the next step

8. Open `media/images/calibrator.jpg` and from the camera lens to the bottom left and right corner of the ROI box in calibrator.jpg measure the distance in feet. Yes! you do have to go outside to get measurements, can't do this step with your computer. 

Add the measurements into `_configs.py` as feed in `L2R_DISTANCE` (left corner) and `R2L_DISTANCE` (right corner)
```
# define some constants
L2R_DISTANCE = 120                      #<---- enter your distance-to-road value for cars going left to right here
R2L_DISTANCE = 120                      #<---- enter your distance-to-road value for cars going left to right here
...
```
While you're here edit and adjust the rest of the configs, they should be fairly obvious, if not read the description.

## Running the webserver
This starts the webserver for real time graphs and data. If left to the default open the page in a browser at http://[server_ip_or_localhost]:8080 
```
./scripts/service-manager.sh -a web -x start
```


9. Start webserver on boot, in `crontab` add the below line, change the path to the full repo path of `service-manager.sh`
    - run `crontab -e`, and in your editor of choice
```
@reboot ${HOME}/repos/pi-speed-tracker/scripts/service-manager.sh -a web -x start >/dev/null 2>&1
```
    - optional to auto start and top the speed `speed-tracker.py` script to monitor traffic (at night), start and stop. run `crontab -e`, and in your editor of choice
```
0 7 * * * ${HOME}/repos/pi-speed-tracker/scripts/service-manager.sh -a sped -x start >/dev/null 2>&1
0 17 * * * ${HOME}/repos/pi-speed-tracker/scripts/service-manager.sh -a sped -x stop >/dev/null 2>&1
```
in this case we start at 7am and stop at 5pm every day. Familiarize with crontab if you want to adjust. The change paths to your paths

The above uses the shell script manager, you can use this script to do many things run `service-manager.sh -h` to see options
```
scripts/
├── load.py.virtualenv.sh       <--- this file can be ignored
└── service-manager.sh          <--- start/stop/status script for apps to see options run: service-manager.sh -h 
```





