import os
import cgi
import smtplib
import Cookie
import uuid
import time
import json
import requests
import random

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from email import Encoders
from base64 import b64encode
from PIL import Image, ImageFont, ImageDraw
from threading import Thread

# local modules
import main
import machine
import log

PORT = 8000
FROM = 'bbhlightprinter@gmail.com'
FONT = 'FiraSansOT-Bold.otf'
USER_EXPIRE_TIME = 180

users = []
finished_users = []
server_is_running = False

class User:
	def __init__(self, uid, name='Anonymous Coward'):
		self.uid = uid
		self.name = name
		self.timestamp = None
		self.imagepath = main.IMG_DIR + main.DUMMY
		self.imageurl = ''
		self.previewpath = main.PREVIEW_DIR + main.DUMMY
		self.turn = False # is this user's turn now?
		self.emails = ''
		self.num_images = 0

def start():
	global server_is_running

	try:
		server = ThreadedHTTPServer(('', PORT), myHandler)
		log.ok('Serving at port %d' % PORT)
		server_is_running = True

		user_monitor_thread = Thread(target=check_users_expiration)
		user_monitor_thread.start()
		server.serve_forever()
	
	except KeyboardInterrupt:
		print
		log.msg('Received KeyboardInterrupt signal, shutting down the server')
		server.socket.close()
		if machine.use_arduino == True:
			machine.arduino.close()
		server_is_running = False

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	pass

class myHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		if self.path == '/':
			self.path = '/index.html'
		elif self.path.startswith('/get_user_time'):
			self.handle_get_user_time()
		elif self.path.startswith('/get_queue'):
			self.handle_get_queue()
		elif self.path.startswith('/turn'):
			self.handle_turn()
		elif self.path.startswith('/timeout'):
			self.handle_timeout()
		elif self.path.startswith('/get_samples'):
			self.handle_get_samples()
		elif self.path.startswith('/display'):
			self.handle_display()
		elif self.path.startswith('/preview'):
			self.handle_preview()
		elif self.path.startswith('/share'):
			self.handle_share()
		try:
			sendReply = False
			if self.path.endswith('.html'):
				mimetype = 'text/html'
				sendReply = True
			elif self.path.endswith('.css'):
				mimetype = 'text/css'
				sendReply = True
			elif self.path.endswith('.js'):
				mimetype = 'application/javascript'
				sendReply = True
			elif self.path.endswith('.jpg'):
				mimetype = 'image/jpg'
				sendReply = True
			elif self.path.endswith('.png'):
				mimetype = 'image/png'
				sendReply = True
			elif self.path.endswith('.gif'):
				mimetype = 'image/gif'
				sendReply = True
			elif self.path.endswith('.ttf'):
				mimetype = 'font/ttf'
				sendReply = True
			elif self.path.endswith('.otf'):
				mimetype = 'font/otf'
				sendReply = True

			if sendReply:
				self.serve(self.path, mimetype)

		except IOError:
			self.send_error(404, 'File not found: %s' % self.path)
	
	def do_POST(self):
		log.msg('Received form action: ' + self.path)
		if self.path.startswith('/signin'):
			self.handle_sign_in()
		elif self.path == '/submit':
			self.handle_submit()
		elif self.path.startswith('/submit_image'):
			self.handle_submit_image()
		elif self.path.startswith('/submit_sample'):
			self.handle_submit_sample()
		elif self.path.startswith('/submit_text'):
			self.handle_submit_text()
		elif self.path.startswith('/submit_surprise'):
			self.handle_submit_surprise()
		elif self.path.startswith('/validate'):
			self.handle_validate()
		elif self.path.startswith('/post_email'):
			self.handle_post_email()

	def handle_sign_in(self):
		global users
		form = cgi.FieldStorage(
			fp = self.rfile,
			headers = self.headers,
			environ={'REQUEST_METHOD':'POST',
				'CONTENT_TYPE':self.headers['Content-Type'],
		})

		# if form is empty, reset the page
		name = form.getvalue('name')
		if name == None:
			self.send_response(301)
			self.send_header('Location', '/')
			self.end_headers()
			return

		# if the user is in the list, resign him/her in
		user = self.get_user()
		if user != None:
			log.msg('\'%s\' already signed in. Resigning in as \'%s\'..' % (user.name, name))
			users.remove(user)
		uid = uuid.uuid4()
		user = User(uid, name)
		users.append(user)

		# assign cookie to user and go to the queue page
		self.send_response(301)
		self.send_header('Location', '/queue.html')
		self.set_cookie(uid)
		self.end_headers()
		log.ok('User \'%s\' signed in' % user.name)
		log.msg('There are ' + str(len(users)) + ' users now')
	
	def handle_get_queue(self):
		user = self.get_user()
		if not self.validate_user(user):
			return

		names = [] 
		for u in users:
			names.append(u.name)
		
		pos = names.index(user.name)
		self.send_response(200)
		self.end_headers()
		data = { 'names': names, 'pos': pos }
		self.wfile.write(json.dumps(data))
		if pos == 0:
			user.turn = True
			user.timestamp = time.time()
			log.msg(user.name + '\'s turn now!')
	
	def handle_get_user_time(self): # unused right now
		user = self.get_user()
		if user and not self.validate_user(user):
			return
		else:
			user = self.get_finished_user()
			if not self.validate_finished_user(user):
				return
		self.validate_user_turn(user)

		self.send_response(200)
		self.end_headers()
		now = time.time()
		deltatime = now - user.timestamp 
		data = { 'user_time': USER_EXPIRE_TIME - deltatime }
		self.wfile.write(json.dumps(data))

	def handle_turn(self):
		user = self.get_user()
		if not self.validate_user(user):
			return

		self.redir('/your_turn.html')
	
	def handle_timeout(self):
		user = self.get_user()
		if not self.validate_user(user):
			return

		log.msg('\'' + user.name + '\' timed out')
		users.remove(user)
		self.redir('/')
	
	def handle_get_samples(self):
		self.send_response(200)
		self.end_headers()
		files = [] 
		for (dirpath, dirnames, filepaths) in os.walk(main.RESIZED_SAMPLES_DIR):
			for f in filepaths:
				if f.endswith('.jpg'):
					files.append(dirpath + '/' + f)
		data = { 'files': files }
		self.wfile.write(json.dumps(data))

	def handle_submit(self):
		user = self.get_user()
		if not self.validate_user(user):
			return
		self.validate_user_turn(user);

		self.redir('/enter_details.html')
	
	def handle_submit_image(self):
		user = self.get_user()
		if not self.validate_user(user):
			return
		self.validate_user_turn(user);

		ctype, pdict = cgi.parse_header(self.headers.getheader('content-type')) 
		if ctype == 'multipart/form-data':
			query = cgi.parse_multipart(self.rfile, pdict)
			data = query.get('image')
		if data:
			user.imagepath = main.INPUT_DIR + str(user.uid) + '.jpg'
			fout = open(user.imagepath, 'wb')
			fout.write(data[0])
			fout.close()
		self.redir('/photo_taking.html')
	
	def handle_submit_sample(self):
		user = self.get_user()
		if not self.validate_user(user):
			return
		self.validate_user_turn(user);

		self.send_response(200)
		self.end_headers()
		filepath = self.rfile.readline().strip()
		user.imagepath = main.INPUT_DIR + str(user.uid) + '.jpg'
		fin = open(filepath, 'rb')
		fout = open(user.imagepath, 'wb')
		log.msg('Copying file \'%s\' to \'%s\' for processing' % (filepath, user.imagepath))
		fout.write(fin.read())
		fout.close()
		fin.close()
	
	def handle_submit_text(self):
		user = self.get_user()
		if not self.validate_user(user):
			return
		self.validate_user_turn(user);

		form = cgi.FieldStorage(
			fp = self.rfile,
			headers = self.headers,
			environ={'REQUEST_METHOD':'POST',
				'CONTENT_TYPE':self.headers['Content-Type'],
		})
		text = form.getvalue('text')
		user.imagepath = main.INPUT_DIR + str(user.uid) + '.jpg'
		create_text_image(text, user.imagepath)

		self.redir('/photo_taking.html')
	
	def handle_submit_surprise(self):
		user = self.get_user()
		if not self.validate_user(user):
			return
		self.validate_user_turn(user);
		
		form = cgi.FieldStorage(
			fp = self.rfile,
			headers = self.headers,
			environ={'REQUEST_METHOD':'POST',
				'CONTENT_TYPE':self.headers['Content-Type'],
		})
		filepath = random_file(main.RESIZED_SAMPLES_DIR)
		user.imagepath = main.INPUT_DIR + str(user.uid) + '.jpg'
		fin = open(filepath, 'rb')
		fout = open(user.imagepath, 'wb')
		fout.write(fin.read())
		fout.close()

		self.redir('/photo_taking.html')
	
	def handle_display(self):
		user = self.get_user()
		if not self.validate_user(user):
			return
		self.validate_user_turn(user);

		self.send_response(200)
		self.end_headers()
		if machine.use_arduino == True:
			user = self.get_user()
			machine.send_image_to_arduino(user)

	def handle_preview(self):
		log.msg('Previewing the captured image..')
		self.send_response(200)
		user = self.get_user()
		if not self.validate_user(user):
			return
		self.validate_user_turn(user);

		self.end_headers()
		data = { 'previewpath': user.previewpath }
		self.wfile.write(json.dumps(data))

	def handle_validate(self):
		user = self.get_user()
		if not self.validate_user(user):
			return
		self.validate_user_turn(user);

		form = cgi.FieldStorage(
			fp = self.rfile,
			headers = self.headers,
			environ={'REQUEST_METHOD':'POST',
				'CONTENT_TYPE':self.headers['Content-Type'],
		})
		self.send_response(301)
		if 'keep' in form:
			finish_user(user)
			if machine.use_arduino:
				upload_to_imgur(user)
			self.send_header('Location', '/share.html')
		else:
			self.send_header('Location', '/enter_details.html')
		self.end_headers()
	
	def handle_share(self):
		user = self.get_finished_user()
		if not self.validate_finished_user(user):
			return

		self.send_response(200);
		self.end_headers();
		if machine.use_arduino:
			data = { 'previewUrl': user.previewpath, 'imageUrl': user.imageurl }
			self.wfile.write(json.dumps(data))

	def handle_post_email(self):
		user = self.get_finished_user()
		if not self.validate_finished_user(user):
			return
		
		form = cgi.FieldStorage(
			fp = self.rfile,
			headers = self.headers,
			environ={'REQUEST_METHOD':'POST',
				'CONTENT_TYPE':self.headers['Content-Type'],
		})
		user.emails = form.getvalue('email_addr')
		email_image(user)
		self.redir('/email_sent.html')

	def set_cookie(self, uid):
		cookie = Cookie.SimpleCookie()
		cookie['uid'] = uid
		self.wfile.write(cookie['uid'].output())
	
	def get_cookie(self):
		if 'Cookie' in self.headers:
			return Cookie.SimpleCookie(self.headers['Cookie'])
		return None
	
	def get_uid(self):
		cookie = self.get_cookie()
		if cookie == None:
			return None
		if 'uid' in cookie:
			return cookie['uid'].value
		return None

	def get_user(self):
		uid = self.get_uid()
		if uid == None:
			return None
		for user in users:
			if uid == str(user.uid):
				return user
		return None

	def get_finished_user(self):
		uid = self.get_uid()
		if uid == None:
			return None
		for user in finished_users:
			if uid == str(user.uid):
				return user
		return None

	def user_signed_in(self):
		user = self.get_user()
		if user:
			return True
		return False
	
	def serve(self, path, mimetype):
		f = open(os.curdir + os.sep + path)
		self.send_response(200)
		self.send_header('Content-type', mimetype)
		self.end_headers()
		self.wfile.write(f.read())
		f.close()
	def validate_user(self, user):
		if user == None or not user in users:
			self.redir('/')
			log.msg('User is not in the list. Redirecting back to homepage..')
			return False
		return True
	
	def validate_finished_user(self, user):
		if user == None or not user in finished_users:
			self.redir('/')
			log.msg('User is not in the finished list. Redirecting back to homepage..')
			return False
		return True
	
	def validate_user_turn(self, user):
		if not user.turn:
			self.redir('/queue.html')
			log.msg('Not the user\'s turn. Redirecting to queue..')

	def redir(self, url):
		self.send_response(301)
		self.send_header('Location', url)
		self.end_headers()
			
def random_file(path):
	files = []
	for (dirpath, dirnames, filenames) in os.walk(path):
		for f in filenames:
			files.append(dirpath + '/' + f)
	idx = random.randint(0, len(files) - 1)
	return files[idx]

def create_text_image(text, path):
	ft = ImageFont.truetype(main.FONT_DIR + FONT, 200)
	tw, th = ft.getsize(text)
	uw, uh = tw + 200, tw + 200
	im = Image.new("RGB", (uw, uh), "#000")
	draw = ImageDraw.Draw(im)
	draw.text((100, uw / 2 - 200), text, font=ft, fill="white")
	im.save(path)

def check_users_expiration():
	global users
	global finished_users

	while server_is_running:
		now = time.time()
		if users and len(users) > 0:
			user = users[0]
			if user.turn:
				deltatime = now - user.timestamp 
				log.msg('User \'%s\' has %f seconds left' % (user.name, USER_EXPIRE_TIME - deltatime))
				if deltatime > USER_EXPIRE_TIME:
					users.remove(user)
		if finished_users and len(finished_users) > 0:
			user = finished_users[0]
			if user.turn:
				deltatime = now - user.timestamp 
				log.msg('Finished user \'%s\' has %f seconds left' % (user.name, USER_EXPIRE_TIME - deltatime))
				if deltatime > USER_EXPIRE_TIME:
					finished_users.remove(user)

		time.sleep(5)

def finish_user(user):
	global users
	global finished_users

	log.msg(user.name + ' is finished!')
	users.remove(user)
	user.timestamp = time.time()
	finished_users.append(user)

def email_image(user):
	msg = "To: %s\r\nFrom: %s\r\nSubject: %s\r\n\r\n" % (FROM, user.emails, "Your Light Printed Photo!")
	msg = msg + user.imageurl

	log.msg('Sending email to ' + user.emails)
	smtp = smtplib.SMTP('smtp.gmail.com', 587)
	smtp.ehlo()
	smtp.starttls()
	smtp.ehlo()
	smtp.login(FROM, 'passwordnotshownhere')
	smtp.sendmail(FROM, user.emails, msg)
	smtp.close()

	log.ok('Sent email to %s!' % user.emails)

def upload_to_imgur(user):
	log.msg('Uploading image to Imgur..')
	client_id = 'df7105d657080b3'
	headers = {"Authorization": "Client-ID df7105d657080b3"}
	url = "https://api.imgur.com/3/image"
	res = requests.post(
		url, 
		headers = headers,
		data = {
			'key': client_id, 
			'image': b64encode(open(user.imagepath, 'rb').read()),
			'type': 'base64',
			'name': 'circle_of_light.jpg',
			'title': 'Circle of Light'
		}
	)

	dic = res.json()
	if dic['status'] == 200:
		user.imageurl = dic['data']['link']
		log.ok('Uploaded image at ' + user.imageurl)
	else:
		log.fail('Couldn\'t upload image to Imgur')
