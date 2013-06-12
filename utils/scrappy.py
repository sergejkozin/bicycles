import os
import sys

import copy
import threading

import urllib
import urllib2
import httplib

import json
import csv

from collections import OrderedDict


__version__ = '0.0.1'


# -------------------------------------------------------------------------
#		Manipulating of URL
# -------------------------------------------------------------------------

class Url( object ):

	_url_base = None
	
	@classmethod
	def set_base( self, base ):
		Url._url_base = base

	@classmethod
	def get_base( self ):
		return Url._url_base
		
		
	@classmethod
	def abs( self, url, base=None ):
		if not base: base = Url._url_base
		if not url: return ''
		
		if self.isabsolute( url ): 
			if '://' in url: return url
			return 'http:' + url

		# get protocol
		protocol, base = base.split( '//', 1 ) if '//' in base else ('http:', base)
		protocol += '//'
		
		# get domain
		domain = base.split( '/' )[0] if '/' in base else base
		
		protocol = protocol.lower()
		domain = domain.lower()
		lower = url.lower()

		if protocol in lower: return url
		if domain in lower: return protocol + url

		if url[0] != '/': url = '/' + url
		return protocol + domain + url


	@classmethod
	def join( self, url1, url2 ):
		if not url1 and url2: return ''
		if not url1: return url2
		if not url2: return url1
		
		i = url1.rfind( '/' )
		if i < 0: i = len(url1) - 1
		
		if url2[0] == '/': url2 = url2[1:]
		
		return url1[:i+1] + url2

	@classmethod
	def isabsolute( self, url ):
		# best way
		if '://' in url.lower(): return True

		if url.lower()[:2] == '//': return True

		return False

	@classmethod
	def isrelative( self, url ):
		return not self.isabsolute( url )

	@classmethod
	def base( self, url ):
		if self.isrelative( url ): return ''
		protocol, host = url.split( '//', 1 )

		if '/' not in host: host += '/'
		host, page = host.split( '/', 1 )

		return protocol + '//' + host

	@classmethod
	def domain( self, url ):
		base = self.base( url )
		return '.'.join( base.split( '.' )[-2:] ).lower()





	""" url-wrapper for easy manipulating with requests
	"""
	def __init__( self, url=None ):
		self._protocol = ''
		self._server = ''
		self._page = ''
		self._arguments = {}
		
		if type( url ) in [ unicode, str ]:
			self.parse( url )


	def __str__( self ):
		return self.build()


	
	def __eq__( self, other ):
		if not other: return False
		
		if type( other ) in [ str, unicode ]:
			other = Url( other )
		
		if type( other ) != Url: return False
		if self.host.lower() != other.host.lower(): return False
		if self.arguments_str( True ).lower() != other.arguments_str( True ).lower(): return False
		
		return True
		
		
	def __ne__( self, other ):
		return not (self == other)
		
				
	@property
	def protocol( self ):
		return self._protocol if self._protocol else 'http'
		
	@protocol.setter
	def protocol( self, value ):
		self._protocol = value
		
	
	@property
	def server( self ):
		return self._server
		
	@server.setter
	def server( self, value ):
		self._server = value


	@property
	def host( self ):
		result = self.protocol + '://' if self.protocol else ''
		return result + self.server + self.page
		

	@host.setter
	def host( self, value ):
		if '://' in value:
			self.protocol, value = value.split( '://', 1 )
			
		if '/' not in value:
			value += '/'

		self.server, self.page = value.split( '/', 1 )


	@property
	def page( self ):
		return self._page

	@page.setter
	def page( self, value ):
		if value and value[0] != '/':
			value = '/' + value
			
		self._page = value


	@property
	def arguments( self ):
		return self._arguments

	@arguments.setter
	def arguments( self, value ):
		if isinstance( value, dict ): 
			self._arguments = copy.copy( value )
			return
			
		self.arguments.clear()
		if not value: return
		
		if value[0] == '?': value = value[1:]
		
		for item in value.split( '&' ):
			if not '=' in item: item += '='
			key, value = item.split( '=' )
			self.arguments[ key ] = value



	def arguments_str( self, sort=False ):
		# add arguments
		keys = self.arguments.keys()
		
		if sort: keys.sort()
			
		return '&'.join( ['%s=%s' % (key, self.arguments[key]) for key in keys] )



	def build( self ):
		result = ''

		# add host
		result += self.host

		# add arguments
		args = self.arguments_str()
		if args:
			result += '?' + args

		return result.replace( ' ', '%20' )
		

	def parse( self, url ):
		""" parse url and fill this object
		"""
		self.host = url
		
		if '?' not in url:
			self.arguments = {}
			return self
			
		# get arguments
		self.host, args = tuple(url.split( '?' ))
		
		# remove fragment
		if '#' in args: args = args.split( '#' )[0]
		
		for item in args.split( '&' ):
			if '=' not in item:
				item += '='
				
			key, value = item.split( '=' )
			self.arguments[ key ] = value
		
		return self



# -------------------------------------------------------------------------
#		Offline database
# -------------------------------------------------------------------------

class HtmlCache( object ):
	def __init__( self, filename=None ):
		self._lock = threading.Lock()
		
		self.http_base = {}
		
		self.filename = filename
		self.load()
		
			
	
	
	def __getitem__( self, url ):
		if type(url) in [ unicode, str ]:
			url = Url( url )
			
		key1 = url.host
		key2 = url.arguments_str( True )
		
		try:
			self._lock.acquire()
		
			host = self.http_base.get( key1, {} )
			if not host: return ''
		
			html = host.get( key2, '' )
			return html
		
		finally: 
			self._lock.release()
		
		
	def __setitem__( self, url, html ):
		if type(url) in [ unicode, str ]:
			url = Url( url )
			
		if type( html ) == str:
			html = html.decode( 'utf8', errors='ignore' )
			
		key1 = url.host
		key2 = url.arguments_str( True )
		
		try:
			self._lock.acquire()
		
			if not self.http_base.get( key1 ):
				self.http_base[ key1 ] = {}
			
			self.http_base[ key1 ][ key2 ] = html
			
		finally:
			self._lock.release()
		
		
	def __delitem__( self, url ):
		if type(url) in [ unicode, str ]:
			url = Url( url )
			
		key1 = url.host
		key2 = url.arguments_str( True )
		
		try:
			self._lock.acquire()
			
			if not self.http_base.get( key1 ): return
		
			if not self.http_base.get( key1 ).get( key2 ):
				del self.http_base[ key1 ]
			else:
				del self.http_base[ key1 ][ key2 ]	
				
		finally:
			self._lock.release()
		
		
		
	def get( self, url ):
		return self[ url ]
		
	def add( self, url, data ):
		self[ url ] = data
		
	def remove( self, url ):
		del self[ url ]
		
		
				
	def save( self, filename=None ):
		filename = (filename or self.filename)
		if not filename: return
		
		try:
			self._lock.acquire()
			
			with open( filename, 'w' ) as f:
				f.write( json.dumps(self.http_base) )
				
		finally:
			self._lock.release()
		
	
	def load( self, filename=None ):
		filename = filename or self.filename
		if not filename: return
		
		try:
			self._lock.acquire()
			
			with open( filename, 'r' ) as f:
				self.http_base = json.loads( f.read() )
		except:
			pass
			
		finally:
			self._lock.release()
			
	
	def pages( self ):
		result = []
		
		for i in self.http_base:
			for j in self.http_base.get( i, {} ):
				if j: j = '?' + j
				result.append( i + j )
				
		return result
				
	



class Browser( object ):
	""" receive data from site by url
	"""
	
	_cache = None
	
	@classmethod
	def cache( self ):
		return Browser._cache
		
	@classmethod
	def set_cache( self, cache ):
		Browser._cache = cache


	@classmethod
	def _url( self, url ):
		if type( url ) in [ str, unicode ]:
			url = Url( url )
		return url
		
			
	@classmethod
	def get_from_cache( self, url ):
		if not self.cache(): return None
		return self.cache().get( self._url(url).build() )
		
	@classmethod
	def add_to_cache( self, url, html ):
		if not self.cache(): return
		self.cache().add( self._url(url).build(), html )
	

	@classmethod
	def create_opener( self ):
		opener = urllib2.build_opener()
		opener.addheaders = [('User-agent', 'Mozilla/5.0')]

		return opener


	@classmethod
	def open( self, url ):
		url = self._url(url).build()
				
		# get data from server
		opener = self.create_opener()
		return opener.open( url )
			
		

	@classmethod
	def POST( self, url, data=None ):
		url = self._url(url) 
		
		data = data if data else {}
		data = urllib.urlencode( data )
		
		page = url.page
		args = url.arguments_str()
		if args and args[0] != '?': args = '?' + args
		
		page += args
		
		conn = httplib.HTTPConnection( url.server )
		conn.request( 'POST', page, data )
		
		resp = conn.getresponse()
		data = resp.read()
		
		conn.close()
		return data


	@classmethod
	def __get( self, url, page=None, args=None ):
		url = self._url( url )
		
		headers = {'User-agent': 'Mozilla/5.0'}
		
		page = page or url.page
		args = args or url.arguments_str()
		if args and args[0] != '?': args = '?' + args
		
		page += args
		
		conn = httplib.HTTPConnection( url.server )
		conn.request( 'GET', page, [], headers )
		
		resp = conn.getresponse()
		data = resp.read()
		
		conn.close()
		return data
		
	
	
	@classmethod
	def GET( self, url, page=None, args=None ):
		url = self._url(url)
		url.page = page or url.page
		url.arguments = args or url.arguments
				
		# try to get data from cache
		html = self.get_from_cache( url )
		if html: return html		

		f = None
		try:
			f = self.open( url )
			
			html = f.read()
			self.add_to_cache( url, html )

			return html.decode( 'utf8', errors='ignore' )

		except Exception as ex:
			Log.error( "### can't open: %s" % url )
			return u''
		
		finally:
			if f: f.close()

			

	@classmethod
	def file_size( self, url ):
		f = None
		try:
			f = self.open( url )
			size = f.headers.get( 'content-length', 0 )
			return int( size )

		except:
			Log.error( "### can't open: %s" % url )
			return 0

		finally:
			if f: f.close()

		return 0


	@classmethod
	def download( self, url, dir='' ):
		dir = os.path.abspath( dir )
		try:
			if not os.path.exists( dir ):
				os.makedirs( dir )
		except:
			pass

		url = self._url( url )
						
		f = None
		try:
			f = self.open( url )
			
			# get filename from headers
			filename = f.headers.get( 'content-disposition', '' )
			if filename:
				filename = filename.split( 'filename=' )[1].strip()
			else:
				filename = str(url).split( '/' )[-1]
			
			filepath = os.path.join( dir, filename )

			# count = 1
			# while os.path.exists( filepath ):
			# 	tempname = filename + '(%s)' % count
			# 	count += 1

			# 	filepath = os.path.join( dir, tempname )
			
			# save to local file
			local_file = None
			try:
				local_file = open( filepath, 'wb' )
				local_file.write( f.read() )
			finally:
				if local_file: local_file.close()

			return filename

			
		except:
			Log.error( "### can't download: %s" % self.url )
			return ''

		finally:
			if f: f.close()



# -------------------------------------------------------------------------
#		Data scraping
# -------------------------------------------------------------------------

class HtmlParser( object ):
	@classmethod
	def _cut( self, text, begin=None, end=None, case=False ):
		""" cut by begin/end markers in text fragment
		"""
		if not text: return ''
		
		begin = begin or ''
		end = end or ''
		
		# lower values for not case sesitive search
		lower = text if case else text.lower()
		begin = begin if case else begin.lower()
		end = end if case else end.lower()
		
		# indexes of need part
		a = lower.find(begin) + len(begin) if begin else 0
		if a < 0: a = 0
		
		b = lower.find(end, a) if end else len(lower)
		if b < 0: b = len(lower)
		
		return text[ a:b ]
		
		
		
	@classmethod
	def cut( self, text, begin=None, end=None, case=False ):
		""" recursive cutting
		"""
		if not text: return ''
		
		if not begin: begin = []
		if not end: end = []
		
		if type( begin ) != list: begin = [ begin ]
		if type( end ) != list: end = [ end ]
		
		begin.reverse()
		end.reverse()
		
		while begin or end:
			a = begin.pop() if begin else None
			b = end.pop() if end else None
			text = self._cut( text, a, b, case )
		
		return text
		
		
		
	@classmethod
	def remove_tags( self, text ):
		""" remove all tags from html part
		"""
		while True:
			a = text.find('<')
			if a < 0: break
			
			b = text.find('>', a)
			if b < 0: break
			
			text = text[:a] + text[b+1:]
			
		while '>' in text:
			text = self.cut( text, '>' )
			
		while '<' in text:
			text = self.cut( text, None, '<' )
			
		return text.strip()

		
	@classmethod
	def split( self, text, separator, count=None, case=False ):
		""" not case sensitive split
		"""
		# change case of text
		lower = text if case else text.lower()
		separator = separator if case else separator.lower()
		
		# get indexes
		indexes = []
		last_index = 0
		while True:
			if count and len( indexes ) >= count: break
			
			index = lower.find( separator, last_index)
			if index < 0: break
			
			indexes.append( (last_index, index,) )
			last_index = index + len(separator)
					
		if last_index < len(lower):
			indexes.append( (last_index, len(lower),) )
						
		result = [ text[ i:j ] for i,j in indexes ]
		return result
			
		
	@classmethod
	def normalize( self, text ):
		""" remote whitespaces from text
		"""
		text = text.replace( '\n', ' ' ).replace( '\r', ' ' ).replace( '\t', ' ' )
		text = text.replace( '&nbsp;', ' ' )
		
		text = text.strip()
		
		while '  ' in text:
			text = text.replace( '  ', ' ' )
	
		return text.strip()
	
	
	@classmethod
	def empty_filter( self, texts ):
		def _filter( a ):
			return bool(a)
			
		return filter( _filter, texts )
			
			
	@classmethod
	def contains_filter( self, texts, subtext ):
		"""
		"""
		subtext = subtext.lower()
		def _filter( a ):
			return subtext in a.lower()
			
		return filter( _filter, texts )
	
	
	
	
	@classmethod
	def parse_img_links( self, html ):
		""" parse <img src=> links
		"""
		images = self.split( html, '<img' )
		images = self.contains_filter( images, 'src=' )
		
		result = []
		for link in images:
			link = self.cut( link, 'src=' )
			
			lquote = link[0]
			if lquote not in [ '"', "'" ]: lquote = None
			rquote = lquote if lquote else ' '
			
			
			link = self.cut( link, lquote, rquote )
			result.append( link )
			
		return result
	
		
	
	
	@classmethod
	def parse_li_list( self, html ):
		""" parser ul-li list
		"""
		result = [ s for s in self.split( html, '<li') ]
		result = [ self.cut( s, '>' ) for s in result ]
		result = [ self.normalize( s ) for s in result ]
		
		return [ self.cut( s, None, '</li>' ) for s in result if s ]
		
		
	@classmethod
	def contains( self, a, b ):
		return b.lower() in a.lower()
		
		
	@classmethod
	def parse_ahref_links( self, html ):
		""" parse links
		"""
		links = self.split( html, '<a' )
		links = self.contains_filter( links, 'href' )
		
		result = []
		for link in links:
			if self.contains( link, 'href="' ):
				result.append( self.cut( link, 'href="', '"' ) )
				continue
				
			if self.contains( link, "href='" ):
				result.append( self.cut( link, "href='", "'" ) )
				continue
				
			result.append( self.cut( link, 'href=', ' ' ) )
			
		return self.empty_filter( result )
	
		
		
	@classmethod
	def parse_table( self, html ):
		""" parse html-table
		"""
		rows = self.split( html, '<tr' )
		rows = [ self.cut( row, '>', '</tr>' ) for row in rows ]
		self.empty_filter( rows )
		
		
		
		result = []
		for row in rows:
			columns = self.split( row, '<td' )
			columns = [ self.cut( col, '>', '</td>' ) for col in columns ]
			columns = self.empty_filter( columns )
			columns = [ self.normalize( self.remove_tags(col) ) for col in columns ]
			
			result.append( columns )
			
		return result
			
	
	
	
		
		
		


	
	
# -------------------------------------------------------------------------
#		Loging
# -------------------------------------------------------------------------

class Log( object ):
	_lock = threading.Lock()
	
	@classmethod
	def _acquire( self ):
		Log._lock.acquire()
		
	@classmethod
	def _release( self ):
		Log._lock.release()
	
	
	@classmethod
	def info( self, text ):
		self._acquire()
		print text
		self._release()
		
		
	@classmethod
	def debug( self, *args ):
		self._acquire()
		print( args )
		self._release()
		
		
		
	@classmethod
	def error( self, text ):
		self._acquire()
		sys.stderr.write( text + '\n' )
		self._release()






