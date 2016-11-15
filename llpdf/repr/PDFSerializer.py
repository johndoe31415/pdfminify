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

from llpdf.types.PDFName import PDFName
from llpdf.types.PDFXRef import PDFXRef

class PDFSerializer(object):
	def __init__(self, obj):
		self._obj = obj


	def _serialize(self, obj):
		if isinstance(obj, (int, float)):
			yield str(obj)
		elif isinstance(obj, bool):
			yield "true" if obj else "false"
		elif isinstance(obj, PDFName):
			yield obj.value
		elif isinstance(obj, bytearray):
			yield "(%s)" % (obj.decode("utf-8"))
		elif isinstance(obj, PDFXRef):
			yield "%d %d R" % (obj.objid, obj.gennum)
		elif isinstance(obj, dict):
			yield "<< "
			for (key, value) in obj.items():
				assert(isinstance(key, PDFName))
				yield "%s " % (key.value)
				yield from self._serialize(value)
				yield " "
			yield ">>"
		elif isinstance(obj, list):
			yield "[ "
			for element in obj:
				yield from self._serialize(element)
				yield " "
			yield " ]"
		else:
			raise Exception("Unknown serialization token: %s" % (type(obj)))

	def serialize(self):
		return "".join(self._serialize(self._obj))

