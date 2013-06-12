def _cut( text, begin=None, end=None, case=False ):
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
	
	
	
def cut( text, begin=None, end=None, case=False ):
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
		text = _cut( text, a, b, case )
	
	return text
	
	
	
def remove_tags( text ):
	""" remove all tags from html part
	"""
	while True:
		a = text.find('<')
		if a < 0: break
		
		b = text.find('>', a)
		if b < 0: break

		tag = text[a:b].strip().lower()
		separator = ' ' if tag in [ 'br', 'br/' ] else ''

		text = text[:a] + separator + text[b+1:]
		

		
	while '>' in text:
		text = cut( text, '>' )
		
	while '<' in text:
		text = cut( text, None, '<' )
		
	return text.strip()

	

def split( text, separator, count=None, case=False ):
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
		
	

def normalize( text ):
	""" remote whitespaces from text
	"""
	text = text.replace( '\n', ' ' ).replace( '\r', ' ' ).replace( '\t', ' ' )
	text = text.replace( '&nbsp;', ' ' )
	
	text = text.strip()
	
	while '  ' in text:
		text = text.replace( '  ', ' ' )

	return text.strip()



def empty_filter( texts ):
	def _filter( a ):
		return bool(a)
		
	return filter( _filter, texts )
		
		

def contains_filter( texts, subtext ):
	"""
	"""
	subtext = subtext.lower()
	def _filter( a ):
		return subtext in a.lower()
		
	return filter( _filter, texts )





def parse_img_links( html ):
	""" parse <img src=> links
	"""
	images = split( html, '<img' )
	images = contains_filter( images, 'src=' )
	
	result = []
	for link in images:
		link = cut( link, 'src=' )
		
		lquote = link[0]
		if lquote not in [ '"', "'" ]: lquote = None
		rquote = lquote if lquote else ' '
		
		
		link = cut( link, lquote, rquote )
		result.append( link )
		
	return result

	



def parse_li_list( html ):
	""" parser ul-li list
	"""
	result = [ s for s in split( html, '<li') ]
	result = [ cut( s, '>' ) for s in result ]
	result = [ normalize( s ) for s in result ]
	
	return [ cut( s, None, '</li>' ) for s in result if s ]
	
	

def contains( a, b ):
	return b.lower() in a.lower()
	
	

def parse_ahref_links( html ):
	""" parse links
	"""
	links = split( html, '<a' )
	links = contains_filter( links, 'href' )
	
	result = []
	for link in links:
		if contains( link, 'href="' ):
			result.append( cut( link, 'href="', '"' ) )
			continue
			
		if contains( link, "href='" ):
			result.append( cut( link, "href='", "'" ) )
			continue
			
		result.append( cut( link, 'href=', ' ' ) )
		
	return empty_filter( result )

	
	

def parse_table( html ):
	""" parse html-table
	"""
	rows = split( html, '<tr' )
	rows = [ cut( row, '>', '</tr>' ) for row in rows ]
	empty_filter( rows )
	
	
	
	result = []
	for row in rows:
		columns = split( row, '<td' )
		columns = [ cut( col, '>', '</td>' ) for col in columns ]
		columns = empty_filter( columns )
		columns = [ normalize( remove_tags(col) ) for col in columns ]
		
		result.append( columns )
		
	return result
		
