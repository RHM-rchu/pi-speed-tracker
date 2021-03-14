# A Work in progress...

## v0.7.1

## Credits

Logic and Core inspired by
Full program details at:   https://gregtinkers.wordpress.com/2016/03/25/car-speed-detector/

## Description

![Sample Image](html/assets/sample_snap.jpg?raw=true "Sample Image")

Light weight Python based traffic speed tracker using the Raspberry Pi. Tracking traffic in front of your street in a side view with traffic going from the left and right. It has been tested with the Pi Zero and RP4. It should work with any Ubuntu based distro, maybe other operating systems (NO not Windows) as long as dependencies are met. The speed tracker is not designed for highways or busy roads, it's targeted for rural and residential streets. It's great tool to get a sense of how traffic goes by in a day and how fast they are going.



![Sample web page](html/assets/sample_web_nav.png?raw=true "Sample web page")

Heres some of the features of the Web Control panels:
- Graphs by Hours, Times, and day of week, all searchable with custom plots points.

![Sample web page](html/assets/sample_searchable_graphs.png?raw=true "Sample web page")

- Cam status give a quick view of the most recent 100 (Default but can be change) photos and let's you know if you speed cam is running. Note: all speed tracked are stored as photos, these can be viewed in the graph section section.

![Sample Cam Status](html/assets/sample_status.png?raw=true "Sample Cam Status")

- Calibrating your camera. You can take quick snapshot of what you camera sees in the control panel. This allows you to focus and point the camera at the part of the road you want. You also have the ability to draw a box on the region of the road you want to monitor here.

![Sample select area of road](html/assets/sample_target_area.png?raw=true "Sample select area of road")

- Editing configurations, is all in one file and should be pretty self explanatory, one you open the editor.

![Sample Cam Status](html/assets/sample_configuration.png?raw=true "Sample Cam Status")

- Scheduling when the camera turns off and on can be done here as well.

![Sample Cam Status](html/assets/sample_scheduler.png?raw=true "Sample Cam Status")

- There is a debugger to help, to tell you what the AI see, in the as images. This can help determine if you have the camera physical location, need to configure the threshold, or redraw the a better section of road to track.

![Sample Cam Status](html/assets/sample_debugger.png?raw=true "Sample Cam Status")

- There are real time logs to for the webserver, speed camera, and server (computer) load & resources.

![Sample Cam Status](html/assets/sample_logger.png?raw=true "Sample Cam Status")


## Features
### Configuration
* All configurations are managed in the web control panel.
### Data
* Data is stored in a SQLight3 database. No worries if you don't know SQLight, this is behind the scenes. The database is created and updates are handled by the app. The data is primarily used for reporting with graphs and such. If you have SQL skills and know SQLight3 you can pull you own report. The database is in `./db/speed-tracker.sqlite3`. 

![DB Sample](html/assets/sample_db.png?raw=true "DB Sample")

* CSV files are also generated if you want to import to Excel. Each time the App start a new CSV file is created in the `./data/` directory
```
data/
├── carspeed_20210208_0631.csv
├── ...
└── carspeed_20210213_0952.csv
```

### Image snapshots of each car
* Images are stored in folders by `./media/images/YYYY/MM/DD`. Each car that has a reported speed will have an image saved. Generally this image is used with the webserver, but is also documented in the SQLight database and CSV files.
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


### View Graphs/Reports

![Sample Graphs Page](html/assets/sample_web.png?raw=true "Sample Graphs Page")


### Viewing Individual Records
- Query and cycle through each record

![Query and view records](html/assets/sample_query-review.png?raw=true "Query and view records")

### Monitor Cam status 
- Turn Cam on/off with the toggle switch
- See most recent entries

![Sample Status Page](html/assets/sample_web2.png?raw=true "Sample Status Page")

### Web monitoring and live log view

#### track what the app is logging in real time as cars go by

![Speed Tracking Logs](html/assets/sample_log_speed.png?raw=true "Speed Tracking Logs")

#### track what the app is logging in real time as cars go by
![Web Server Logs](html/assets/sample_log_web.png?raw=true "Web Server Logs")


#### Check on Server resource and resource usage, with the `top` command in a web browser

![Server Status](html/assets/sample_log_top.png?raw=true "Server Status")

## Requirements

* Raspberry Pi 4 2gb RAM (Recommended, 4gb would be better)
    * We do need the desktop environment to calibrate so don't go headless.
    * Raspbian Buster - Should work with most Ubuntu cores.
    * I've installed and it working fine on a PI Zero. A little sluggish but does the job.
* Camera module
* Opencv >=4.1.0.25
* python3
* Not a whole lot but a little terminal skills is nice



[Installation Instruction](1.install.md)

[Setup Instruction](2.setup.md)





