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

import logging

from .types.PDFObject import PDFObject
from .FileRepr import StreamRepr

class PDFResources(object):
	_log = logging.getLogger("llpdf.PDFResources")

	def __init__(self, resource_data):
		self._objs = { }
		self._f = StreamRepr(resource_data)
		self._read_objects()

	def _read_objects(self):
		while True:
			obj = PDFObject.parse(self._f)
			if obj is None:
				break
			self._objs[(obj.objid, obj.gennum)] = obj

	def replace_object(self, obj):
		self._objs[(obj.objid, obj.gennum)] = obj

	def delete_object(self, objid, gennum):
		if (objid, gennum) in self._objs:
			del self._objs[(objid, gennum)]

	def __iter__(self):
		return iter(self._objs.values())

	def __len__(self):
		return len(self._objs)

	def __str__(self):
		return "PDFResources<%d>" % (len(self))

