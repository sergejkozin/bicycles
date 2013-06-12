import json	
import threading
from collections import OrderedDict

# -------------------------------------------------------------------------
#		Save data formats
# -------------------------------------------------------------------------

class Format( object ):
	def __init__( self, filename ):
		self.file = self._openfile( filename )
		self._lock = threading.Lock()
		
		
	def _openfile( self, filename ):
		return open( filename, 'w' ) 
	
	
	def _writeitem( self, item ):
		pass
	
	
	def append( self, item ):
		if type(item)  == list:
			for i in range(len(item)):
				item[i] = item[i].decode( 'utf8', errors='ignore' )
				
		if type(item) in [ dict, OrderedDict ]:
			for key in item:
				value = item[ key ]
				
#				if type(key) == str:
#					key = key.decode( 'utf8', errors='ignore' )
#				
				if type(value) == str:
					value = value.decode( 'utf8', errors='ignore' )
				
				item[ key ] = value
						
		try:
			self._lock.acquire()
			self._writeitem( item )
		finally:
			self._lock.release()		
	
		
	def close( self ):
		if self.file: self.file.close()
	
	
	
# -----------------------
#	JSON
class JsonFormat( Format ):
	def _writeitem( self, item ):
		separator = ',\n' if self.file.tell() > 1 else '['
		self.file.write( separator + json.dumps(item, indent=4) )
		
		
	def close( self ):
		self.file.write( ']' )
		Format.close( self )
	
	
	
# -----------------------
#	CSV
class CsvFormat( Format ):
	def __init__( self, filename, columns=None ):
		Format.__init__( self, filename )
		
		self.csv_writer = None
		self.columns = columns or []
	
	
	def _openfile( self, filename ):
		return open( filename, 'wb' )
		
		
	def _writeitem( self, item ):
		if not self.csv_writer:
			# create csv writer			
			self.csv_writer = csv.writer( self.file, delimiter=';', quoting=csv.QUOTE_ALL )
			
			# define columns
			if not self.columns and type( item ) in [ dict, OrderedDict ]:
				self.columns = item.keys()
		
			# write header
			if self.columns:
				self.csv_writer.writerow( self.columns )
			
		# write data-row
		row = []
		
		if type( item ) == list:
			for s in item:
				if not s: s = u''
				try:
					if type(s) == str: s = s.decode( 'utf8', errors='ignore' )
					row.append( s.encode( 'utf8', errors='ignore' ) )
				except:
					print( s )
			
		if not row:
			for key in self.columns:
				value = item.get( key, '' )
				if type(value) == str: value = unicode(value).encode( 'utf8', errors='ignore' )
				row.append( value )

		self.csv_writer.writerow( row )
			
	
	





class TsvReader( object ):
	""" read tsv (tab separated values)
	"""
	@staticmethod
	def read( f ):
		try:
			data = f.read()
		except:
			return []

		if not data: return []
		return [ row.split( '\t' ) for row in data.split( '\n' ) ]


	@staticmethod
	def create_dict( rows ):
		header = rows[0]
		rows = rows[ 1: ]

		index_number = {}
		def get_index( key ):
			if key not in index_number:
				index_number[ key ] = header.index( key )
			return index_number.get( key, -1 )



		result = []
		for row in rows:
			item = OrderedDict()
			for key in header:
				index = get_index( key )
				item[ key ] = row[ index ] if index < len(row) else None

			result.append( item )

		return result



class TsvWriter( object ):
	def __init__( self ):
		self.data = []
		self.header = []


	def set_header( self, header ):
		self.header = header


	def append( self, row ):
		row = [ str(s) for s in row ]
		self.data.append( row )

		
	def save( self, filename ):
		header = '\t'.join( self.header )

		rows = [ '\t'.join( r ) for r in self.data ]
		if header: rows.insert( 0, header )

		text = '\n'.join( rows )

		f = None
		try:
			f = open( filename, 'w' )
			f.write( text )

		finally:
			if not f: f.close()







class JsonWriter( object ):
	def __init__( self ):
		self.data = []

	def append( self, data ):
		self.data.append( data )

	def save( self, filename ):
		f = None
		try:
			f = open( filename, 'w' )
			f.write( json.dumps( self.data, indent=4 ) )

		finally:
			if f: f.close()


class JsonReader( object ):
	def __init__( self, filename ):
		self.filename = filename

	def read( self ):
		f = None
		try:
			f = open( self.filename )
			return json.loads( f.read() )
		
		finally:
			if f: f.close()
