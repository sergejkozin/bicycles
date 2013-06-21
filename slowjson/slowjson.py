# coding: utf-8

# implement own json serializator because could't found json for python 2.4

__version__ = '0.0.3'

class SlowJson( object ):
	""" JSON format implementation
	"""

	# terminal symbols
	TERMINALS = [ ',', ']', '}', ' ' ]


	class ParseError( Exception ):
		""" exception that incorrect data
		"""
		pass


	@staticmethod
	def _decode( text ):
		if type( text ) == unicode:
			return text

		return text.decode( 'utf8' )



	class Parser( object ):
		""" json parser
		"""
		def __init__( self, jstr ):
			self.i 		= 0						# current index in input data
			self.jstr 	= SlowJson._decode(jstr)	# data in json representation


		def next( self ):
			""" return next symbol and move current position to next
			"""
			if self.i >= len( self.jstr ): 
				return None

			value = self.jstr[ self.i ]
			self.i += 1

			return value


		def back( self ):
			""" return position back
			"""
			self.i -= 1
			if self.i < 0: self.i = 0


		def skip_whitespaces( self ):
			""" skip whitespace from current to first substantial symbol
			"""
			c = None
			
			while True:
				c = self.next()
				if c is None: break
				if c.isspace(): continue
				break
			
			# back to non space symbol
			if c: self.back()


		def next_token( self, terminals=None ):
			""" next token. define token by terminals. in default use all terminals from constants
			"""
			if not terminals: 
				terminals = SlowJson.TERMINALS
			if not isinstance(terminals, list):
				terminals = [ terminals ]

			def is_space( c ):
				if not c: return  False

				if ' ' in terminals:
					return c.isspace()
				
				return False


			def is_escaped( c, value ):
				if not value: return False
				if value[ -1 ] != '\\': return False

				if c == '"': return True

				return False


			value = ''
			
			while True:
				c = self.next()

				if not is_escaped( c, value ) and c in terminals: 

					break
				if is_space(c): break
				if c is None: break

				value += c
				
			self.back() # save last symbol
			return value
			

		# ---------------------------------
		#	parsers for json-elements
		# ---------------------------------

		def parse_string( self ):
			text = self.next_token( '"' )
			self.next() # skip last quote
			if text == '\\': text = '\\\\'
			s = eval( 'u"' + text + '"' )
			return SlowJson._decode( s )

		def parse_number( self ):
			self.back()
			number = self.next_token()
	
			if '.' in number:
				return float( number )

			return int( number )

		def parse_null( self ):
			self.back()
			if self.next_token() == 'null': 
				return None

			raise SlowJson.ParseError()

		def parse_bool( self ):
			self.back()
			value = self.next_token()
			
			if value == 'true'	: return True
			if value == 'false' : return False

			raise SlowJson.ParseError()

		def parse_array( self ):
			array = []

			while True:
				self.skip_whitespaces()
				
				value = self.parse()
				if value == ']': break
				if value == ',':  continue

				array.append( value )

			return array

		def parse_object( self ):
			result = {}

			while True:
				self.skip_whitespaces()
				
				value = self.parse()
				if value == '}': break
				if value == ',':  continue
				if value.isspace(): continue
				
				key = value

				self.skip_whitespaces()
				v = self.parse()
				if v != ':': 
					raise SlowJson.ParseError( v )
				self.skip_whitespaces()

				value = self.parse()
				result[ key ] = value

			return result




		def parse( self ):
			""" parse element of json and return decodet value
			"""
			c = self.next()

			if c is None:
				raise NyJson.ParseError()


			if c in [ 't', 'f' ]:
				return self.parse_bool()

			if c == 'n':
				return self.parse_null()

			if c == '"':
				return self.parse_string()

			if c == '[':
				return self.parse_array()

			if c == '{':
				return self.parse_object()

			if c.isdigit() or c == '-':
				return self.parse_number()

			return c







	@classmethod
	def dumps( self, obj, indent=None ):
		""" JSON encoder. Translate object to JSON representation.
		"""
		# None
		if obj is None: return 'null'

		# bool
		if type( obj ) == bool:
			if obj: 
				return 'true'
			return 'false'

		# numbers
		if type( obj ) in [ long, int, float ]:
			return str( obj )

		# string
		if type( obj ) in [ str, unicode ]:
			text = SlowJson._decode( obj )
			return '"%s"' % repr(text)[2:-1]

		# array
		if isinstance( obj, list ):
			if not obj: return '[]'

			jlist = '[ '

			for o in obj[:-1]:
				jlist += self.dumps( o ) + ', '

			jlist += self.dumps( obj[-1] ) + ' ]'
			return jlist


		# object
		if isinstance( obj, dict ):
			if not obj: return '{}'
			
			jdict = '{ '
			keys = obj.keys()
			
			for key in keys[:-1]:
				jdict += '"%s" : %s,' % (key, self.dumps( obj[key] ))

			key = keys[-1]
			jdict += '"%s" : %s }' % (key, self.dumps( obj[key] ))
			return jdict

		





	@classmethod
	def loads( self, jstr ):
		""" deserialize JSON representation to object.
		"""
		return SlowJson.Parser( jstr ).parse()


# synonym
json = SlowJson