import os
import time
import subprocess
import struct
import serial
import cv2
import numpy as np

from math import cos, sin, pi
from threading import Thread

# local modules
import main
import server
import log

# serial comm. constants
LINE = 1
FLUSH = 2
SETTINGS = 3
RETURN = 4
END = 5

DEV_INITIALS = ['/dev/ttyACM', '/dev/ttyUSB', '/dev/tty.usbfdmodem', 'COM']
PREVIEW_SIZE = (640, 427)	# size of the image preview
MOTOR_RETURN_TIME = 3 
CAMERA_FOCUS_TIME = 1

dev = ''			# device full name / path
arduino = None			# arduino serial.Serial() object
use_arduino = True		# can be disabled for web app development purposes

num_leds = 0
line_length = 0
motor_speed = 0
motor_begin = 0
motor_end = 0
out_width = 0
out_height = 0

def start():
	global dev
	global arduino

	if use_arduino:
		# if device is not specified, pick the first one in the list
		if dev == '':
			devlist = subprocess.check_output(['python', '-m', 'serial.tools.list_ports'])
			dev = devlist.split()[0]

		# check or guess if Arduino is connected
		has_arduino = False
		for initial in DEV_INITIALS:
			if dev.startswith(initial):
				has_arduino = True
		
		# didn't find Arduino, so exit the program
		if not has_arduino:
			log.fail('Didn\'t find an Arduino port.')
			os.exit(1)

		log.msg('Connecting to Arduino at %s' % dev)
		arduino = serial.Serial(dev, 115200, timeout=1)
		arduino.read()
		log.ok('Arduino is connected')

# Plot a value into a certain range, similar to map() in Arduino.
# Why not just call it map()? because it already exists in Python
# but it doesn't do the same thing.
def plot(num, min1, max1, min2, max2):
	num = max(num, min1)
	num = min(num, max1)
	return (num - min1) / (max1 - min1) * (max2 - min2) - min2

# Distort the image so it appears undistorted on the machine
# then format the image for serial data transfer to Arduino.
def distort_and_format_image(user):
	log.msg('Distorting image ' + user.imagepath + ' with size (%d, %d)..' % (out_width, out_height))
	img = cv2.imread(user.imagepath)
	img = cv2.resize(img, (out_width, out_height))
	h, w = len(img), len(img[0])
	hh, hw = h / 2, w /2
	img_array = np.zeros(img.shape)

	# distort
	for i in range(w):
		f = float(i) / w
		angle = float(i) / w * pi
		hy = sin(angle) * hh
		hx = cos(angle) * hw
		y1 = hh - hy
		x1 = hw - hx
		y2 = hh + hy
		x2 = hw + hx
		for j in range(h):
			f = float(j) / h
			y = hh + (y2 - y1) * (f - 0.5)
			x = hw + (x2 - x1) * (f - 0.5)
			if y >= h or x >= w:
				break
			img_array[j][i] = img[y][x]

	# format
	output = []
	for x in range(w):
		for y in range(h):
			r = img_array[y][w-x-1][2] / 64
			g = img_array[y][w-x-1][1] / 64
			b = img_array[y][w-x-1][0] / 64
			output.append(r)
			output.append(g)
			output.append(b)

	cv2.imwrite(main.DISTORT_DIR + os.path.basename(user.imagepath), img_array)
	log.ok('Created distorted image')

	return output

# pick a byte at certain position
def nthbyte(val, n):
	return (val >> (8 * n)) & 0xff

# high-level function to send an image file to arduino
def send_image_to_arduino(user):
	global arduino

	# write data to file
	pydata = distort_and_format_image(user)
	data = struct.pack('%sB' % len(pydata), *pydata)

	# tell arduino to return motor to initial position
	arduino.write(struct.pack('B', RETURN))
	arduino.flush()

	# send some metadata to arduino
	metadata = [nthbyte(out_width, 1), nthbyte(out_width, 0),
			nthbyte(motor_begin, 1), nthbyte(motor_begin, 0),
			nthbyte(motor_end, 1), nthbyte(motor_end, 0)]
	arduino.write(struct.pack('%sB' % len(metadata), *metadata))
	arduino.flush()
	
	# wait until motor is back
	time.sleep(MOTOR_RETURN_TIME)
	
	# start focusing and capturing photo
	cap_thread = Thread(target=subprocess.check_output, args=[['gphoto2', '--force-overwrite', '--capture-image-and-download']])
	cap_thread.start()
	log.msg('Capturing..')

	# wait until the camera finish focusing
	time.sleep(CAMERA_FOCUS_TIME)

	# send light data to arduino
	idx = 0
	size = line_length
	pos = motor_begin
	arduino.readlines()
	while pos < motor_end - 3:
		s = arduino.readline().strip()
		if s.isdigit() == True:
			pos = float(s)
		if pos >= motor_begin and pos <= motor_end:
			idx = int(plot(pos, motor_begin, motor_end, 0, out_width))
		buf = data[idx*size : idx*size+size]
		arduino.write(struct.pack('B', LINE))
		arduino.write(buf)
		arduino.flush()
		arduino.write(struct.pack('B', FLUSH))
		arduino.flush()

	# mark end of data
	arduino.write(struct.pack('B', END))
	arduino.flush()

	# stop capturing photo
	cap_thread.join()
	log.ok('Finished capturing image')

	save_image(user)
	create_image_preview(user)

def save_image(user):
	log.msg('Saving image..')

	filepath = main.OUTPUT_DIR + str(user.uid) + '.jpg'
	infile = open('capt0000.jpg', 'rb')
	outfile = open(filepath, 'wb')
	dupfile = open(main.DUP_DIR + str(user.uid) + '_' + str(user.num_images) + '.jpg', 'wb')

	outfile.write(infile.read())
	infile.seek(0)
	dupfile.write(infile.read())

	outfile.close()
	dupfile.close()
	infile.close()
	user.imagepath = filepath
	user.num_images = user.num_images + 1

	log.ok('Saved the image at ' + filepath)

def create_image_preview(user):
	log.msg('Creating preview..')

	im = cv2.imread(user.imagepath)
	preview = cv2.resize(im, PREVIEW_SIZE)

	filename = os.path.basename(user.imagepath)
	path = main.PREVIEW_DIR + filename
	cv2.imwrite(path, preview)
	user.previewpath = path

	log.ok('Created preview at ' + path)
