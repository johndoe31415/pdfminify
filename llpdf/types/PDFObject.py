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
from llpdf.img.PDFImage import PDFImage
from .Comparable import Comparable

class PDFObject(Comparable):
	_OBJ_RE = re.compile("^(?P<obj_header>(?P<objid>\d+)\s+(?P<gennum>\d+)\s+obj?)")

	def __init__(self, objid, gennum, rawdata):
		self._objid = objid
		self._gennum = gennum
		if rawdata is not None:
			if rawdata.lstrip(b" \r\n").startswith(b"<<") and ((b"stream\r\n" in rawdata) or (b"stream\n" in rawdata)):
				line_offset = 0
				offset = rawdata.find(b"stream\n")
				if offset == -1:
					line_offset = 1
					offset = rawdata.find(b"stream\r\n")
				content = rawdata[:offset]
				self._stream = rawdata[offset + 7 + line_offset : -(11 + line_offset)]
			else:
				content = rawdata
				self._stream = None
			content = content.decode("utf-8")
			self._content = PDFParser.parse(content)
		else:
			self._stream = None
			self._content = None

	def set_content(self, content):
		self._content = content

	def set_stream(self, stream):
		self._stream = stream

	def replace_by(self, pdfobj):
		self.set_content(pdfobj.content)
		self.set_stream(pdfobj.stream)

	@classmethod
	def create(cls, objid, gennum, content, stream):
		result = cls(objid, gennum, rawdata = None)
		result.set_content(content)
		result.set_stream(stream)
		return result

	@classmethod
	def create_image(cls, objid, gennum, img, alpha_xref = None):
		content = {
			PDFName("/Type"):				PDFName("/XObject"),
			PDFName("/Subtype"):			PDFName("/Image"),
			PDFName("/Filter"):				PDFName("/" + img.imgtype.name),
			PDFName("/Width"):				img.width,
			PDFName("/Height"):				img.height,
			PDFName("/BitsPerComponent"):	img.bits_per_component,
			PDFName("/ColorSpace"):			PDFName("/" + img.colorspace.name),
			PDFName("/Length"):				len(img),
			PDFName("/Interpolate"):		True,
		}
		if alpha_xref is not None:
			content[PDFName("/SMask")] = alpha_xref
#		if content[PDFName("/Filter")] == PDFName("/DCTDecode"):
#			content[PDFName("/Width")] = 1
#			content[PDFName("/Height")] = 1
		return cls.create(objid, gennum, content, img.imgdata)

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

	@property
	def rawdata(self):
		return self._rawdata

	@classmethod
	def parse(cls, f):
		pos = f.tell()
		while True:
			header = f.readline()			
			header = header.decode("ascii")
			if header.strip() == "":
				continue
			break
		result = cls._OBJ_RE.match(header)
		if not result:
			f.seek(pos)
			return None
		result = result.groupdict()
		f.seek(pos + len(result["obj_header"]) + 1)
		(objid, gennum) = (int(result["objid"]), int(result["gennum"]))
		(obj_data, obj_end) = f.read_until([ b"endobj\r\n", b"endobj\n", b"endobj \r\n", b"endobj \n", b"endobj " ])
		return cls(objid = objid, gennum = gennum, rawdata = obj_data)

	@property
	def content(self):
		return self._content

	@property
	def stream(self):
		return self._stream

	@property
	def is_image(self):
		return (self.stream is not None) and (self.content.get(PDFName("/Type")) == PDFName("/XObject")) and (self.content.get(PDFName("/Subtype")) == PDFName("/Image"))

	@property
	def is_pattern(self):
		return isinstance(self.content, dict) and (self.content.get(PDFName("/PatternType")) == 1) and (self.content.get(PDFName("/PaintType")) == 1)

	def __len__(self):
		return 0 if self.stream is None else len(self.stream)

	def __str__(self):
		return "PDFObject<ID=%d, gen=%d, %d bytes>" % (self.objid, self.gennum, len(self))

