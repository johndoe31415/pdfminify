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
import zlib
import collections
import logging

from .types.PDFObject import PDFObject
from .types.PDFName import PDFName
from llpdf.repr import PDFParser, GraphicsParser
from .FileRepr import StreamRepr

class PDFFile(object):
	_log = logging.getLogger("llpdf.PDFFile")

	def __init__(self, f):
		self._raw_f = f
		self._f = StreamRepr.from_file(f)
		self._hdr_version = self._identify()
		self._log.debug("Header detected: %s", str(self._hdr_version))
		if self._hdr_version not in [ b"%PDF-1.4", b"%PDF-1.5", b"%PDF-1.6", b"%PDF-1.7" ]:
			self._log.warning("Warning: Header indicates %s, unknown if we can handle this.", self._hdr_version.decode())

		self._objs = { }
		self._trailer = None
		self._read_objects()
		self._read_xref_table()
		self._trailer = self._read_trailer()
		self._log.debug("Finished reading PDF file. %d objects found.", len(self._objs))

	def _identify(self):
		self._f.seek(0)
		version = self._f.readline()

		pos = self._f.tell()

		after_hdr = self._f.read(6)
		if (after_hdr[0] != ord("%")) or any(value & 0x80 != 0x80 for value in after_hdr[ 1 : 5 ]):
			self._log.warn("PDF seems to violate standard, bytes read after initial line are %s.", after_hdr)
			self._f.seek(pos)

		return version.rstrip(b"\r\n ")

	@property
	def trailer(self):
		return self._trailer

	@property
	def image_objects(self):
		return [ obj for obj in self._objs.values() if obj.is_image ]

	@property
	def pattern_objects(self):
		return [ obj for obj in self._objs.values() if obj.is_pattern ]

	@property
	def stream_objects(self):
		return [ obj for obj in self._objs.values() if (obj.stream is not None) ]

	def get_objects_that_reference(self, xref):
		for obj in self.pattern_objects:
			resources = obj.content.get(PDFName("/Resources"))
			xobjects = resources.get(PDFName("/XObject"))
			xrefs = set(xobjects.values())
			if xref in xrefs:
				yield obj

	def get_extent_of_image(self, img_object):
		print("Determining extent of %s" % (img_object))
		for obj in self.get_objects_that_reference(img_object.xref):
			if obj.is_pattern:
				print("Referenced by pattern %s" % (obj), obj.content)
				matrix = obj.content.get(PDFName("/Matrix"))
				bbox = obj.content.get(PDFName("/BBox"))
				(scalex, scaley) = (matrix[0], matrix[3])
				(width, height) = (bbox[2] - bbox[0], bbox[3] - bbox[1])
				#return (width * scalex, height * scaley)
				return (width, height)
			else:
				print("Cannot determine phyiscal extents of image, scaling probably done in page code :-(")

	def delete_object(self, objid, gennum):
		key = (objid, gennum)
		if key in self._objs:
			del self._objs[key]

	@property
	def pages(self):
		root_obj = self.lookup(self._trailer[PDFName("/Root")])
		pages_obj = self.lookup(root_obj.content[PDFName("/Pages")])
		pagecontent_xrefs = pages_obj.content[PDFName("/Kids")]

		for page_xref in pagecontent_xrefs:
			page = self.lookup(page_xref)
			yield page

	@property
	def parsed_pages(self):
		for page in self.pages:
			content_xref = page.content[PDFName("/Contents")]
			content = self.lookup(content_xref)
			if PDFName("/Filter") not in content.content:
				# Uncompressed page
				pagedata = content.stream
			elif content.content[PDFName("/Filter")] == PDFName("/FlateDecode"):
				pagedata = zlib.decompress(content.stream)
			else:
				raise Exception("Do not know how to decompress page contents.")
			pagedata = pagedata.decode("utf-8")
			yield (page, GraphicsParser.parse(pagedata))

	def __getitem__(self, key):
		(objid, gennum) = key
		return self._objs.get((objid, gennum))

	def lookup(self, xref):
		return self[(xref.objid, xref.gennum)]

	def __iter__(self):
		return iter(self._objs.values())

	def _read_objects(self):
		self._log.debug("Started reading objects.")
		while True:
			obj = PDFObject.parse(self._f)
			if obj is None:
				break
			self._log.debug("Read object: %s", obj)
			self._objs[(obj.objid, obj.gennum)] = obj

	def _read_next_xref_batch(self):
		pos = self._f.tell()
		entries_hdr = self._f.readline()
		entries_hdr = entries_hdr.decode("ascii").rstrip("\r\n").split()
		if len(entries_hdr) != 2:
			# XRef Table is at end or we cannot parse this.
			self._f.seek(pos)
			return False

		(start_id, entry_cnt) = (int(entries_hdr[0]), int(entries_hdr[1]))
		for i in range(entry_cnt):
			self._f.readline()
		return True

	def _read_xref_table(self):
		self._log.debug("Started reading XRef table.")
		line = self._f.readline()
		if line not in [ b"xref", b"xref\r" ]:
			raise Exception("Expected XRef table to appear, but encountered %s." % (str(line)))

		while True:
			if not self._read_next_xref_batch():
				return False

	def _read_trailer(self):
		self._log.debug("Started reading trailer.")
		line = self._f.readline()
		if line not in [ b"trailer", b"trailer\r" ]:
			raise Exception("Expected trailer to appear, but encountered %s." % (str(line)))
		(trailer_data, delimiter) = self._f.read_until([ b"startxref\r\n", b"startxref\n" ])
		trailer_data = trailer_data.decode("latin1")
		trailer = PDFParser.parse(trailer_data)
		self._f.readline()
		line = self._f.readline()
		if line not in [ b"%%EOF", b"%%EOF\r" ]:
			raise Exception("Expected end of file, but encountered %s." % (str(line)))
		return trailer

	def read_stream(self):
		self._f.read_until([ b"stream\r\n", b"stream\n" ])
		(data, terminal) = self._f.read_until([ b"endstream\r\n", b"endstream\n" ])
		return data

