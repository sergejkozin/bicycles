import threading


class WaitedThread( threading.Thread ):
	_lock = threading.Lock()
	
	# list of active threads
	_threads = []
	
	@classmethod
	def add_thread( self, t ):
		WaitedThread._lock.acquire()
		try:
			WaitedThread._threads.append( t )
		finally:
			WaitedThread._lock.release()
	
	
	@classmethod
	def remove_thread( self, t ):
		WaitedThread._lock.acquire()
		try:
			if t not in WaitedThread._threads: return
			WaitedThread._threads.remove( t )
		finally:
			WaitedThread._lock.release()
	
	
	@classmethod
	def wait( self ):
		[ t.join() for t in WaitedThread._threads ]
		for t in WaitedThread._threads:
			if not t.is_alive(): self.remove_thread(t)


	@classmethod
	def count( self ):
		count = 0
		for t in WaitedThread._threads:
			if t.is_alive(): count += 1
		return count
	
	
	def start( self ):
		self.add_thread( self )
		threading.Thread.start( self )


	


class LimitedThread( WaitedThread ):
	limit = 25
	
	@classmethod
	def set_limit( self, limit ):
		self.limit = limit
		
		
	def start( self ):
		if self.count() >= self.limit:
			self.wait()

		WaitedThread.start( self )



