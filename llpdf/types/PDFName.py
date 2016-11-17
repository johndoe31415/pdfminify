#	pdfminify - Tool to minify PDF files.
#	Copyright (C) 2016-2016 Johannes Bauer
#
#	This file is part of pdfminify.
#
#	pdfminify is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	pdfminify is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with pdfminify; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>
#

import re
import string
from .Comparable import Comparable

class PDFName(Comparable):
	_HEX_CHAR = re.compile("#([a-fA-F0-9]{2})")
	_PRINTABLE = set(string.ascii_letters + string.digits)

	def __init__(self, name):
		assert(name.startswith("/"))
		self._name = self._HEX_CHAR.sub(lambda match: chr(int(match.group(1), 16)), name)

	def cmpkey(self):
		return ("PDFName", self._name)

	@staticmethod
	def _escape(char):
		return "#%02x" % (ord(char))

	@property
	def value(self):
		return "/" + "".join(char if (char in self._PRINTABLE) else self._escape(char) for char in self._name[1:])

	def __repr__(self):
		return str(self)

	def __str__(self):
		return "Name<%s>" % (self.value)

if __name__ == "__main__":
	x = PDFName("/Adobe#20Green")
	print(x, x.value)

	x = PDFName("/Adobe#ff#20#41#41#20Green")
	print(x, x.value)
