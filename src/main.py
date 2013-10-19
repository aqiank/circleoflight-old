#/usr/bin/env python2

import optparse

# local modules
import server
import machine
import log

DISTORT_DIR = 'tmp/distort/'	# save the distorted image here
PREVIEW_DIR = 'tmp/preview/'	# save the image previews here
OUTPUT_DIR = 'tmp/output/'	# save the latest images here
DUP_DIR = 'tmp/dup/'		# save all the output images here, including the previous ones
FONT_DIR = 'font/'
IMG_DIR = 'img/'
INPUT_DIR = 'tmp/input/'
RESIZED_SAMPLES_DIR = IMG_DIR + 'resized_samples'
DUMMY = 'dummy.jpg'

def parse_args():
	global options

	parser = optparse.OptionParser();
	parser.add_option('-n', '--num', dest='num', default=64, help='number of leds')
	parser.add_option('-p', '--port', dest='port', default='', help='serial port device')
	parser.add_option('-s', '--speed', dest='speed', default=255, help='motor speed')
	parser.add_option('-b', '--begin', dest='begin', default=50, help='motor begin position')
	parser.add_option('-e', '--end', dest='end', default=612, help='motor end position')
	parser.add_option('-a', '--arduino', dest='arduino', default=True, help='use arduino')
	(options, args) = parser.parse_args()

	machine.dev = options.port
	machine.num_leds = options.num
	machine.motor_speed = options.speed
	machine.motor_begin = options.begin
	machine.motor_end = options.end
	machine.use_arduino = options.arduino == 'True'
	machine.line_length = machine.num_leds * 3
	machine.out_width = machine.motor_end - machine.motor_begin
	machine.out_height = machine.num_leds

if __name__ == '__main__':
	parse_args()
	machine.start()
	server.start()
