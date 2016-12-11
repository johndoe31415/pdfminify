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
from llpdf.repr import PDFParser
from llpdf.types.PDFName import PDFName
from llpdf.types.PDFXRef import PDFXRef
from llpdf.FileRepr import StreamRepr
from llpdf.EncodeDecode import EncodedObject
from .Comparable import Comparable

class PDFObject(Comparable):
	_OBJ_RE = re.compile(r"^(?P<obj_header>(?P<objid>\d+)\s+(?P<gennum>\d+)\s+obj?)")

	def __init__(self, objid, gennum, rawdata):
		assert(objid is not None)
		assert(gennum is not None)
		assert(isinstance(objid, int))
		assert(isinstance(gennum, int))
		self._objid = objid
		self._gennum = gennum
		if rawdata is not None:
			strm = StreamRepr(rawdata)
			stream_begin = strm.read_until_token(b"stream")
			if stream_begin is None:
				# No stream in this object found, just content
				content = rawdata
				self._stream = None
			else:
				(stream_data, end_marker) = strm.read_until_token(b"endstream")
				content = stream_begin[0]
				self._stream = stream_data

			content = content.decode("latin1")

			# Remove line continuations
			content = content.replace("\\\r\n", "")
			content = content.replace("\\\n", "")
			content = content.replace("\\\r", "")

			self._content = PDFParser.parse(content)
			if (self._stream is not None) and (PDFName("/Length") in self._content) and isinstance(self._content[PDFName("/Length")], int):
				# When direct length field is given, then truncate the stream
				# according to it. For indirect streams, we don't do this (yet)
				self._stream = self._stream[ : self._content[PDFName("/Length")]]
		else:
			self._stream = None
			self._content = None

	def set_content(self, content):
		self._content = content

	def set_stream(self, stream):
		assert(isinstance(stream, EncodedObject))
		self.set_raw_stream(stream.encoded_data)
		stream.update_meta_dict(self.content)

	def set_raw_stream(self, raw_stream):
		assert((raw_stream is None) or isinstance(raw_stream, (bytes, bytearray)))
		self._stream = raw_stream

	def replace_by(self, pdfobj):
		self.set_content(pdfobj.content)
		self.set_stream(pdfobj.raw_stream)

	def truncate(self, stream_length):
		self._stream = self._stream[ : stream_length]

	@classmethod
	def create(cls, objid, gennum, content, stream = None):
		assert((stream is None) or isinstance(stream, EncodedObject))
		result = cls(objid, gennum, rawdata = None)
		result.set_content(content)
		if stream is not None:
			result.set_stream(stream)
		return result

	@classmethod
	def create_image(cls, objid, gennum, img, alpha_xref = None):
		content = {
			PDFName("/Type"):				PDFName("/XObject"),
			PDFName("/Subtype"):			PDFName("/Image"),
			PDFName("/Width"):				img.width,
			PDFName("/Height"):				img.height,
			PDFName("/BitsPerComponent"):	img.bits_per_component,
			PDFName("/ColorSpace"):			PDFName("/" + img.colorspace.name),
			PDFName("/Interpolate"):		True,
		}
		if alpha_xref is not None:
			content[PDFName("/SMask")] = alpha_xref
		return cls.create(objid, gennum, content, stream = img.imgdata)

	@property
	def xref(self):
		return PDFXRef(self._objid, self._gennum)

	def cmpkey(self):
		return ("PDFObject", self.xref)

	@property
	def objid(self):
		return self._objid

	@property
	def gennum(self):
		return self._gennum

	@classmethod
	def parse(cls, f):
		pos = f.tell()
		objid = f.read_next_token()
		gennum = f.read_next_token()
		object_start = f.read_next_token()
		object_data = f.read_until_token(b"endobj")

		if (object_start is None) or (object_data is None) or (object_start[0] != b"obj"):
			f.seek(pos)
			return None

		objid = int(objid[0].decode("ascii"))
		gennum = int(gennum[0].decode("ascii"))
		return cls(objid = objid, gennum = gennum, rawdata = object_data[0])

	@property
	def content(self):
		return self._content

	@property
	def raw_stream(self):
		return self._stream

	@property
	def stream(self):
		if not self.has_stream:
			return None
		else:
			return EncodedObject.from_object(self)

	@property
	def has_stream(self):
		return self.raw_stream is not None

	@property
	def is_objstrm(self):
		return self.has_stream and isinstance(self.content, dict) and (self.content.get(PDFName("/Type")) == PDFName("/ObjStm"))

	@property
	def is_image(self):
		return self.has_stream and (self.content.get(PDFName("/Type")) == PDFName("/XObject")) and (self.content.get(PDFName("/Subtype")) == PDFName("/Image"))

	@property
	def is_pattern(self):
		return (self.getattr(PDFName("/PatternType")) == 1) and (self.getattr(PDFName("/PaintType")) == 1)

	def getattr(self, key):
		if not isinstance(self.content, dict):
			return None
		return self.content.get(key)

	def __len__(self):
		return 0 if (not self.has_stream) else len(self.raw_stream)

	def __str__(self):
		return "PDFObject<ID=%d, gen=%d, %d bytes>" % (self.objid, self.gennum, len(self))
