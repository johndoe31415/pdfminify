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

from .img.PDFImage import PDFImage
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
		self._xref_obj = None
		self._read_objects()
		self._read_endfile()
		self._log.debug("Finished reading PDF file. %d objects found.", len(self._objs))
		self._unpack_objstrms()
		self._log.debug("Finished unpacking all object streams in file. %d objects found total.", len(self._objs))

	def _identify(self):
		self._f.seek(0)
		version = self._f.readline()

		pos = self._f.tell()

		after_hdr = self._f.readline()
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
	def objstrm_objects(self):
		return [ obj for obj in self._objs.values() if obj.is_objstrm ]

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

	def _get_pages_from_pages_obj(self, pages_obj):
		pagecontent_xrefs = pages_obj.content[PDFName("/Kids")]
		for page_xref in pagecontent_xrefs:
			page = self.lookup(page_xref)
			if page.content[PDFName("/Type")] == PDFName("/Page"):
				yield page
			elif page.content[PDFName("/Type")] == PDFName("/Pages"):
				yield from self._get_pages_from_pages_obj(page)
			else:
				raise Exception("Page object %s contains neither page nor pages (/Type = %s)." % (pages_obj, page.content[PDFName("/Type")]))

	@property
	def pages(self):
		if self._trailer is None:
			raise Exception("Cannot get pages without trailer (root node).")
		root_obj = self.lookup(self._trailer[PDFName("/Root")])
		if root_obj is None:
			raise Exception("Root object is not in primary data stream (part of object stream?). Unsupported at the moment.")
		pages_obj = self.lookup(root_obj.content[PDFName("/Pages")])

		yield from self._get_pages_from_pages_obj(pages_obj)


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

	def _read_textline(self):
		line = self._f.readline_nonempty().decode("ascii").rstrip("\r\n")
		return line

	def _read_next_xref_batch(self):
		pos = self._f.tell()
		entries_hdr = self._f.readline()
		try:
			entries_hdr = entries_hdr.decode("ascii").rstrip("\r\n").split()
		except UnicodeDecodeError:
			# XRef Table is at end or we cannot parse this.
			self._f.seek(pos)
			return False

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
		while True:
			if not self._read_next_xref_batch():
				return False

	def _read_trailer(self):
		self._log.debug("Started reading trailer.")
		(trailer_data, delimiter) = self._f.read_until([ b"startxref\r\n", b"startxref\n" ])
		trailer_data = trailer_data.decode("latin1")
		self._trailer = PDFParser.parse(trailer_data)
		self._f.seek(self._f.tell() - len(delimiter))

	def _read_endfile(self):
		while True:
			line = self._read_textline()
			if line == "xref":
				self._read_xref_table()
			elif line == "trailer":
				self._read_trailer()
			elif line == "startxref":
				xref_offset = int(self._f.readline())
				if self._trailer is None:
					pos = self._f.tell()
					self._f.seek(xref_offset)
					xref_object = PDFObject.parse(self._f)
					self._trailer = xref_object.content
					self._xref_obj = self[(xref_object.objid, xref_object.gennum)]
					self._f.seek(pos)
			elif line == "%%EOF":
				break
			else:
				raise Exception("Unknown end file token '%s'." % (line))

	def _unpack_objstrm(self, objstrm_obj):
		if objstrm_obj.content[PDFName("/Filter")] != PDFName("/FlateDecode"):
			self._log.warn("Cannot unpack object stream %s with unknown filter %s.", objstrm_obj, objstrm_obj.content[PDFName("/Filter")])
			return
		data = zlib.decompress(objstrm_obj.stream)
		objcnt = objstrm_obj.content[PDFName("/N")]
		first = objstrm_obj.content[PDFName("/First")]
		self._log.debug("Object stream %s contains %d objects starting at offset %d.", objstrm_obj, objcnt, first)

		header = data[:first]
		data = data[first:]
		header = [ int(value) for value in header.decode("ascii").replace("\n", " ").split() ]
		for idx in range(0, len(header), 2):
			(objid, sub_offset) = (header[idx], header[idx + 1])
			if idx + 3 >= len(header):
				# Last object
				sub_obj_data = data[sub_offset : ]
			else:
				next_sub_offset = header[idx + 3]
				sub_obj_data = data[sub_offset : next_sub_offset]
			sub_obj = PDFObject(objid, 0, sub_obj_data)
			self.replace_object(sub_obj)
		self.delete_object(objstrm_obj.objid, objstrm_obj.gennum)

	def _unpack_objstrms(self):
		for obj in self.objstrm_objects:
			self._unpack_objstrm(obj)

	def read_stream(self):
		self._f.read_until([ b"stream\r\n", b"stream\n" ])
		(data, terminal) = self._f.read_until([ b"endstream\r\n", b"endstream\n" ])
		return data

	def get_image(self, img_xref):
		image = self.lookup(img_xref)
		if PDFName("/SMask") in image.content:
			# image has an alpha channel
			alpha_channel = self.lookup(image.content[PDFName("/SMask")])
		else:
			alpha_channel = None
		image = PDFImage.create_from_object(image, alpha_channel)
		self._log.debug("Created image from %s with alpha %s: %s",img_xref, alpha_channel, image)
		return image

	def delete_object(self, objid, gennum):
		key = (objid, gennum)
		if key in self._objs:
			del self._objs[key]

	def replace_object(self, obj):
		self._objs[(obj.objid, obj.gennum)] = obj
		return self

