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

from llpdf.types.XRefTable import CompressedXRefEntry
from llpdf.types.PDFObject import PDFObject
from llpdf.types.PDFName import PDFName
from llpdf.EncodeDecode import EncodedObject

class CompressedObjectContainer(object):
	def __init__(self, objid):
		self._objid = objid
		self._contained_objects = [ ]

	@property
	def objid(self):
		return self._objid

	@property
	def objects_inside_count(self):
		return len(self._contained_objects)

	def add(self, obj):
		self._contained_objects.append(obj)
		return CompressedXRefEntry(obj.objid, self.objid, len(self._contained_objects) - 1)

	def serialize(self, serializer):
		header = [ ]
		data = bytearray()
		for obj in self._contained_objects:
			obj_data = serializer.serialize(obj.content)
			offset = len(data)
			header.append(obj.objid)
			header.append(offset)
			data += obj_data + b"\n"

		header = " ".join(str(value) for value in header)
		header = header.encode("utf-8") + b"\n"
		full_data = header + data
		content = {
			PDFName("/Type"):	PDFName("/ObjStm"),
			PDFName("/N"):		self.objects_inside_count,
			PDFName("/First"):	len(header),
		}
		return PDFObject.create(objid = self.objid, gennum = 0, content = content, stream = EncodedObject.create(full_data))

	def __str__(self):
		return "CompressedContainer<ObjId = %d, %d objects inside: {%s}>" % (self.objid, self.objects_inside_count, ", ".join(str(obj.objid) for obj in self._contained_objects))
