import sys
import logging 

from localbooru.web import LocalBooru

def main():
	webLocalBooru = LocalBooru()
	webLocalBooru.start()

if __name__ == '__main__':
      sys.exit(main())
