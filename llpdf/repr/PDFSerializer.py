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
from llpdf.types.MarkerObject import MarkerObject

class PDFSerializer(object):
	_PRINTABLE = set(b"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'*+,-./:;<=>?@[]^_`{|}~ ")

	def __init__(self, pretty = False):
		self._pretty = pretty
		self._offset = 0
		self._marks = { }

	@staticmethod
	def _serialize_hexbytes(obj):
		yield "<"
		yield obj.hex()
		yield ">"

	def _serialize_string(self, obj):
		yield "("
		for char in obj:
			if char in self._PRINTABLE:
				yield chr(char)
			else:
				yield "\\%03o" % (char)
		yield ")"

	def _serialize_bytes(self, obj):
		# Try to encode as string first
		str_string = "".join(self._serialize_string(obj))
		hex_string_len = 2 + (2 * len(obj))
		if len(str_string) > hex_string_len:
			return "".join(self._serialize_hexbytes(obj))
		else:
			return str_string

	def _spacing(self, nesting_level):
		if self._pretty:
			yield "    " * (nesting_level)

	def _serialize(self, obj, nesting_level = 0):
		if obj is None:
			yield "null"
		elif isinstance(obj, bool):
			yield "true" if obj else "false"
		elif isinstance(obj, int):
			yield str(obj)
		elif isinstance(obj, float):
			yield "%.3f" % (obj)
		elif isinstance(obj, PDFName):
			yield obj.value
		elif isinstance(obj, (bytes, bytearray)):
			yield self._serialize_bytes(obj)
		elif isinstance(obj, PDFXRef):
			yield "%d %d R" % (obj.objid, obj.gennum)
		elif isinstance(obj, dict):
			itemiter = obj.items()
			if self._pretty:
				itemiter = sorted(itemiter)
			yield "<<"
			yield "\n" if self._pretty else " "
			for (key, value) in itemiter:
				assert(isinstance(key, PDFName))
				yield from self._spacing(nesting_level + 1)
				yield "%s " % (key.value)
				yield from self._serialize(value, nesting_level + 1)
				yield "\n" if self._pretty else " "
			yield from self._spacing(nesting_level)
			yield ">>"
		elif isinstance(obj, list):
			yield "["
			for element in obj:
				yield " "
				yield from self._serialize(element, nesting_level + 1)
			yield " ]"
		elif isinstance(obj, MarkerObject):
			self._marks[obj.name] = self._offset
			if obj.is_raw:
				yield obj.raw
			else:
				yield from self._serialize(obj.child)
		else:
			raise Exception("Unknown serialization token: %s" % (type(obj)))

	def get_mark(self, name):
		return self._marks[name]

	@property
	def offset(self):
		return self._offset

	@offset.setter
	def offset(self, value):
		self._offset = value

	def serialize(self, obj, start_offset = None):
		if start_offset is not None:
			self.offset = start_offset

		result = bytearray()
		for next_part in self._serialize(obj):
			next_part = next_part.encode("latin1")
			self._offset += len(next_part)
			result += next_part
		result += b"\n"
		return result

if __name__ == "__main__":
	serializer = PDFSerializer(pretty = True)
	obj = {
		PDFName("/Foo"):	b"Bar Foo \x12 \x34 \x56 ()",
		PDFName("/Bar"):	[ 1.234, 4.567, 7.89, 1 / 3 ],
		PDFName("/Moo"):	{
			PDFName("/Inner1"):	b"Muh",
			PDFName("/Inner2"):	"Mäh".encode("latin1"),
		},
	}
	print(serializer.serialize(obj))
