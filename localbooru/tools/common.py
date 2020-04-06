from localbooru import __version__

COMMON_MAGICS = [('\xff\xd8', 'image/jpeg'),
				('GIF87a', 'image/gif'),
				('GIF89a', 'image/gif'),
				('\x89PNG', 'image/png'),
				('BM', 'image/bmp'),
				('\x1aE\xdf\xa3', 'video/webm')]

def get_version():
	return __version__

def magic_mime(head):
	for m in COMMON_MAGICS:
		if head.startswith(m[0]):
			return m[1]
