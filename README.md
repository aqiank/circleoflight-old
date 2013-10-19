Circle of Light
===============

![Setup](http://i.imgur.com/kNpy1ck.jpg "Yes, that's a Pokeball")

Circle of Light is an automated photograph framework where the users can easily
create their own light-painted photo by uploading pictures / text they want to be
shown on the light painting machine and share them on their favorite social
networks. This project is inspired by a project called
[Rainbow Machine](https://github.com/boxysean/RainbowMachine).

Description
---------------------

![Diagram](http://i.imgur.com/nvaVnxD.jpg)

The framework consists of an LPD8806 64-LED strip that is hooked on a wooden stick
which will be rotated by a servo motor controlled by Arduino. A computer acts as a
web app server for users to send images / text from their own machines (mobile phones
or PCs). The server also converts the assets sent by the users, send the data to the
Arduino for display, and trigger the camera capture.

The following are the setup that we used for our framework:
* Softwares
	* Web server code (Python)
	* Web app (HTML/Javascript)
	* Arduino code (C/C++)

* Hardwares
	* DSLR Camera (Nikon D300)
	* Servo Motor (HerkuleX DRS-0201)
	* LPD8806 LED strip (64 leds)
	* Web server
	* Arduino

Requirements
-----------
* Linux or OSX (for gPhoto2)
* Arduino and its libraries
	* [HerkuleX](http://www.sgbotic.com/products/datasheets/robotics/HerkuleX.zip)
	* [LPD8806](https://github.com/adafruit/LPD8806)
* Python 2 and its libraries
	* Requests (for http requests)
	* PySerial (for serial communication)
	* OpenCV 2 (for image processing)
	* NumPy (complements OpenCV 2)
	* Pillow (for drawing text)
* gPhoto2 (for automated camera capture)

For Fedora/Linux, install the Arduino, Python packages and gPhoto2 by typing this command:
`yum install arduino pyserial python-requests python-pillow opencv-python numpy gphoto2`

Guides for other Linux distros and OSX will come soon.

Assets
--------
Download the assets [here](https://app.box.com/s/7k4tqvcerlbui6o0fknn) as we only put code on Github.

Usage
-----
Using terminal, type `python src/main.py -a True` in the folder. If you just want to look
at the web app, type `python src/main.py`.

User Interface
--------------
![Home](http://i.imgur.com/X4VsGcs.jpg)
![Queue](http://i.imgur.com/LRPwkqc.jpg)
![Get Ready](http://i.imgur.com/vsf1IZe.jpg)
![Submit](http://i.imgur.com/VOArTfr.jpg)
![Takign Photo](http://i.imgur.com/B5Y7yoA.jpg)
![Validate](http://i.imgur.com/0hGJbVG.jpg)
![Share](http://i.imgur.com/xd6yIUi.jpg)
