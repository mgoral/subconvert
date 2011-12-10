from datetime import datetime

class FrameTime:
	def __init__(self, fps, value_type, **kwargs):
		'''Construct and convert value(s) given in kwargs.
		Kwargs should describe either 'frame' or 'h', 'm',
		's' and 'ms'. '''
		if fps >= 0:
			self.fps = float(fps)
		else:
			raise ValueError, _("Incorrect fps argument.")
		if value_type == 'frame':
			self.__set_time__( int(kwargs['frame']) / self.fps)
		elif value_type == 'time':
			if int(kwargs['h']) < 0 or int(kwargs['m']) > 59 or int(kwargs['m']) < 0 \
			or int(kwargs['s']) > 59 or int(kwargs['s']) < 0 or int(kwargs['ms']) > 999 \
			or int(kwargs['ms']) < 0:
				raise ValueError, "Arguments not in allowed ranges."
			self.miliseconds = int(kwargs['ms'])
			self.seconds = int(kwargs['s'])
			self.minutes = int(kwargs['m'])
			self.hours = int(kwargs['h'])
			self.frame = int(round(self.fps * (3600*self.hours + 60*self.minutes + self.seconds + float(self.miliseconds)/1000)))
			self.ss = self.frame / self.fps
		elif value_type == 'ss':
			self.__set_time__( kwargs['seconds'] )
		else:
			raise AttributeError, _("Not supported FrameTime type: '%s'") % value_type
	
	def __set_time__(self, seconds):
		if seconds >= 0:
			self.ss = float(seconds)
			self.frame = int(round(self.ss * self.fps))
		else:
			raise ValueError, _("Incorrect seconds value.")
		tmp = seconds
		seconds = int(seconds)
		self.miliseconds = int((tmp - seconds)*1000)
		self.hours = seconds / 3600
		seconds -= 3600 * self.hours
		self.minutes = seconds / 60
		self.seconds = seconds - 60 * self.minutes
	
	def __set_frame__(self, frame):
		if frame >= 0:
			self.__set_time__(frame / self.fps)
		else:
			raise ValueError, _("Incorrect frame value.")

	def __cmp__(self, other):
		assert(self.fps == other.fps)
		if self.ss < other.ss:
			return -1
		elif self.ss == other.ss:
			return 0
		elif self.ss > other.ss:
			return 1

	def __add__(self, other):
		assert(self.fps == other.fps)
		result = self.ss + other.ss
		return FrameTime(fps = self.fps, value_type = 'ss', seconds = result)
	
	def __sub__(self, other):
		assert(self.fps == other.fps)
		assert(self.ss >= other.ss)
		result = self.ss - other.ss
		return FrameTime(fps = self.fps, value_type = 'ss', seconds = result)
	
	def __mul__(self, n):
		result = self.ss * n
		return FrameTime(fps = self.fps, value_type = 'ss', seconds = result)
	
	def __div__(self, n):
		result = self.ss / n
		return FrameTime(fps = self.fps, value_type = 'ss', seconds = result)
	
	def __str__(self):
		return "t: %s:%s:%s.%s; f: %s" % \
			( self.hours, self.minutes, self.seconds, self.miliseconds, self.frame )

