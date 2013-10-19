import time

start_time = time.time()

def fail(s):
	print "[ %.4f \033[91mFAIL\033[0m ] %s" % (time.time() - start_time, s)

def ok(s):
	print "[ %.4f \033[92mOK\033[0m ] %s" % (time.time() - start_time, s)

def msg(s):
	print "[ %.4f ] %s" % (time.time() - start_time, s)
