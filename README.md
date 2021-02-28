# A Work in progress...

## v0.7.0

## Credits

Logic and Core inspired by
Full program details at:   https://gregtinkers.wordpress.com/2016/03/25/car-speed-detector/

## Description

This program for the Raspberry Pi 4 running Raspbian determines the speed of cars moving through the Picamera's field of view. This is meant to be in side profile view so cars cross the field of view from left to right and right to left. Data is gathered in a few different ways, CSV File, SQLight3 database, and an image is saved.

![Sample Image](html/assets/sample_snap.jpg?raw=true "Sample Image")


## Features
### Configuration
* All configs are in one file `_configs.py`. Most config variables have comments.
### Data
* Data is stored in a SQLight3 database. No worries if you don't know SQLight, this is behind the scenes. The database is created and updates are handled by the app. The data is primarily used for reporting by the web server, but if you have SQL skills and know SQLight3 you can pull you own report. Unless you changed in the onfigs, the db is stored in `db/speed-tracker.sqlite3`. ![DB Sample](html/assets/sample_db.png?raw=true "DB Sample")
* CSV files are also generated if you want to export into Excel and don't know SQl. Each time the App start a new CSV file is created
```
data/
├── carspeed_20210208_0631.csv
├── ...
└── carspeed_20210213_0952.csv
```
### Image snapshots of each car
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


### View Graphs/Reports

![Sample Graphs Page](html/assets/sample_web.png?raw=true "Sample Graphs Page")


### Monitor Cam status 
- Query and cycle through each record
![Query and view records](html/assets/sample_web.png?raw=true "Query and view records")

### Monitor Cam status 
- Turn Cam on/off with the toggle switch
- See most recent entries

![Sample Status Page](html/assets/sample_web2.png?raw=true "Sample Status Page")

### Web monitoring and live log view

#### track what the app is logging in real time as cars go by
![Speed Tracking Logs](html/assets/sample_log_placeholder.png?raw=true "Speed Tracking Logs")


#### Check on Server resource and resource usage, with the `top` command in a web browser
![Server Status](html/assets/sample_log_placeholder.png?raw=true "Server Status")

## Requirements

* Raspberry Pi 4 2gb RAM (Recommended, 4gb would be better)
    * We do need the desktop environment to calibrate so don't go headless.
    * Raspbian Buster - should work with any, but what I tested with
    * I've installed and it working fine on a PI Zero. A little sluggish but does the job.
* Picamera
* Opencv >=4.1.0.25
* python3
* Not a whole lot but a little terminal skills is nice



[Installation Instruction](1.install.md)

[Setup Instruction](2.setup.md)





