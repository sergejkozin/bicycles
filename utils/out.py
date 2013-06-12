import sys
import threading

# ----------------------------------------------
#		Print methods
# ----------------------------------------------

__lock = threading.Lock()

def _writefile( file, *args ):
	def _str( a ):
		if type(a) == str:
			return a

		if type(a) == unicode:
			return a.encode( 'utf8' )

		return str(a)

	args = [ _str(a) for a in args ]
	text = ' '.join( args )


	__lock.acquire()
	try:
		file.write( text )
		file.flush()
	finally:
		__lock.release()






def write( *args ):
	_writefile( sys.stdout, *args )
	
def writeln( *args ):
	args += ('\n',)
	write( *args )

def error( *args ):
	args += ('\n',)
	_writefile( sys.stderr, *args )


