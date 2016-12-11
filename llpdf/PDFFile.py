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

from llpdf.repr import PDFParser, GraphicsParser
from .img.PDFImage import PDFImage
from .types.PDFObject import PDFObject
from .types.PDFName import PDFName
from .types.PDFXRef import PDFXRef
from .types.XRefTable import XRefTable
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
		self._xref_table = XRefTable()
		self._trailer = None
		self._read_pdf()
		self._log.debug("Finished reading PDF file. %d objects found.", len(self._objs))
		self._unpack_objstrms()
		self._log.debug("Finished unpacking all object streams in file. %d objects found total.", len(self._objs))
		self._fix_object_sizes()

	@property
	def xref_table(self):
		return self._xref_table

	def _identify(self):
		self._f.seek(0)
		version = self._f.readline()

		pos = self._f.tell()
		after_hdr = self._f.readline()
		if (after_hdr[0] != ord("%")) or any(value & 0x80 != 0x80 for value in after_hdr[ 1 : 5 ]):
			self._log.warning("PDF seems to violate standard, bytes read in second line are %s.", after_hdr)
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
		return [ obj for obj in self._objs.values() if obj.has_stream ]

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
				bbox = obj.content.get(PDFName("/BBox"))
				(width, height) = (bbox[2] - bbox[0], bbox[3] - bbox[1])
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
			self._log.error("Cannot access page data without trailer; returning empty page set.")
			return [ ]
		root_xref = self._trailer.get(PDFName("/Root"))
		if root_xref is None:
			self._log.error("Cannot access page data without /Root node in trailer; returning empty page set.")
			return [ ]
		root_obj = self.lookup(root_xref)
		if root_obj is None:
			self._log.error("Cannot access page data without /Root node (failed to lookup %s); returning empty page set.", root_xref)
			return [ ]
		pages_obj = self.lookup(root_obj.content[PDFName("/Pages")])

		yield from self._get_pages_from_pages_obj(pages_obj)

	@property
	def parsed_pages(self):
		for page in self.pages:
			content_xref = page.content[PDFName("/Contents")]
			content = self.lookup(content_xref)
			pagedata = content.stream.decode()
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
		self._log.debug("Started reading objects at 0x%x.", self._f.tell())
		objcnt = 0
		while True:
			obj = PDFObject.parse(self._f)
			if obj is None:
				break
			objcnt += 1
			self._log.debug("Read object: %s", obj)
			self._objs[(obj.objid, obj.gennum)] = obj
		self._log.debug("Finished reading %d objects at 0x%x.", objcnt, self._f.tell())
		return objcnt

	def _fix_object_sizes(self):
		self._log.debug("Fixing object sizes of indirect referenced /Length fields")
		for obj in self.stream_objects:
			length_xref = obj.content.get(PDFName("/Length"))
			if (length_xref is not None) and isinstance(length_xref, PDFXRef):
				length_obj = self.lookup(length_xref)
				length = length_obj.content
				if not isinstance(length, int):
					self._log.warning("Indirect length reference supposed to point to integer value, but points to %s (%s)", length_obj, length)
				else:
					if length != len(obj):
						obj.truncate(length)

	def _read_textline(self):
		line = self._f.readline_nonempty().decode("ascii").rstrip("\r\n")
		return line

	def _read_trailer(self):
		self._log.debug("Started reading trailer at 0x%x.", self._f.tell())
		(trailer_data, delimiter) = self._f.read_until_token(b"startxref")
		trailer_data = trailer_data.decode("latin1")
		self._trailer = PDFParser.parse(trailer_data)
		self._f.seek(self._f.tell() - len(delimiter))

	def _read_endfile(self):
		self._log.debug("Reading end-of-file data at 0x%x.", self._f.tell())
		while True:
			line = self._read_textline().strip("\r\n ")
			if line == "":
				continue
			elif line == "xref":
				self._xref_table.read_xref_table_from_file(self._f)
			elif line == "trailer":
				self._read_trailer()
			elif line == "startxref":
				xref_offset = int(self._f.readline())
				if self._trailer is None:
					# Compressed XRef directory
					with self._f.tempseek(xref_offset) as marker:
						self._log.trace("Will parse XRef stream at offset 0x%x referenced from 0x%x." % (xref_offset, marker.prev_offset))
						xref_object = PDFObject.parse(self._f)
						if xref_object is None:
							self._log.error("Could not parse a valid type /XRef object at 0x%x. Corrupt PDF?", xref_offset)
						else:
							self._trailer = xref_object.content
							assert(self._trailer[PDFName("/Type")] == PDFName("/XRef"))
							self._xref_table.parse_xref_object(xref_object.stream.decode(), self._trailer.get(PDFName("/Index")), self._trailer[PDFName("/W")])
			elif line == "%%EOF":
				self._log.debug("Hit EOF marker at 0x%x.", self._f.tell())
				break
			else:
				raise Exception("Unknown end file token '%s' at offset 0x%x." % (line, self._f.tell()))

	def _read_pdf(self):
		generation = 0
		while True:
			generation += 1
			self._log.debug("Trying to read generation %d data at offset 0x%x", generation, self._f.tell())
			objcnt = self._read_objects()
			if objcnt == 0:
				self._log.debug("No more data to read at 0x%x.", self._f.tell())
				break
			self._read_endfile()

	def _unpack_objstrm(self, objstrm_obj):
		data = objstrm_obj.stream.decode()
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

	def get_info(self, key):
		info_node_xref = self.trailer[PDFName("/Info")]
		info_node = self.lookup(info_node_xref)
		key = PDFName("/" + key)
		if (info_node is None) or (key not in info_node.content):
			return ""
		else:
			bin_value = info_node.content[key]
			self._log.debug("Info directionary %s = %s", key, bin_value)
			if bin_value.startswith(b"\xfe\xff") or bin_value.startswith(b"\xff\xfe"):
				return bin_value.decode("utf-16")
			else:
				return bin_value.decode("latin1")

	def set_info(self, key, value):
		info_node_xref = self.trailer[PDFName("/Info")]
		info_node = self.lookup(info_node_xref)
		if info_node is not None:
			info_node.content[PDFName("/" + key)] = value.encode("latin1")
		else:
			self._log.error("Cannot set /Info dictionary entry \"%s\" to \"%s\": info_node is None", key, value)

	def get_free_objids(self, count = 1):
		assert(count >= 1)
		for objid in range(1, len(self._objs) + count + 1):
			if (objid, 0) not in self._objs:
				yield objid

	def get_free_objid(self):
		return list(self.get_free_objids())[0]

	def delete_object(self, objid, gennum):
		key = (objid, gennum)
		if key in self._objs:
			del self._objs[key]

	def replace_object(self, obj):
		self._objs[(obj.objid, obj.gennum)] = obj
		return self
