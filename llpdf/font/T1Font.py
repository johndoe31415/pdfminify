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
import enum
import struct
import logging
from llpdf.FileRepr import StreamRepr
from llpdf.types.PDFName import PDFName
from llpdf.types.PDFObject import PDFObject
from llpdf.EncodeDecode import EncodedObject
from llpdf.font.T1PRNG import T1PRNG
from llpdf.font.T1Glyph import T1Glyph
from llpdf.font.T1Canvas import NaiveDebuggingCanvas
from llpdf.font.T1Interpreter import T1Interpreter

class T1Font(object):
	_T1_FONT_KEY = 55665
	_T1_GLYPH_KEY = 4330
	_PFB_HEADER = struct.Struct("< H L")
	_FONT_BBOX_RE = re.compile(r"/FontBBox\s*{(?P<v1>-?\d+)\s+(?P<v2>-?\d+)\s+(?P<v3>-?\d+)\s+(?P<v4>-?\d+)\s*}")

	def __init__(self, cleardata, cipherdata, trailerdata):
		self._cleardata = cleardata
		self._cipherdata = cipherdata
		self._trailerdata = trailerdata
		self._charset = None
		self._subroutines = None
		self._numeric_glyph_map = { }

	def _decrypt_cipherdata(self):
		decrypted_data = T1PRNG(self._T1_FONT_KEY).decrypt_bytes(self._cipherdata)
		return decrypted_data

	@property
	def charset(self):
		if self._charset is None:
			self._parse_font()
		return self._charset

	@property
	def charset_string(self):
		return "".join(sorted(self.charset.keys())).encode("ascii")

	@classmethod
	def _parse_glyphs(cls, data):
		glyphs = { }
		numeric_glyph_map = { }
		strm = StreamRepr(data[data.index(b"/CharStrings") : ])
		header = strm.read_n_tokens(5)
		glyph_count = int(header[1].decode("ascii"))
		for i in range(glyph_count):
			definition = strm.read_n_tokens(3)
			name = definition[0].decode("ascii")
			length = int(definition[1].decode("ascii"))
			encoded_glyph_data = strm.read(length)
			decoded_glyph_data = T1PRNG(cls._T1_GLYPH_KEY).decrypt_bytes(encoded_glyph_data)
			glyph = T1Glyph(decoded_glyph_data)
			strm.read_next_token()
			if name != "/.notdef":
				glyphs[name] = glyph
				numeric_glyph_map[i] = name
		return (glyphs, numeric_glyph_map)

	@classmethod
	def _parse_subroutines(cls, data):
		subroutines = { }
		strm = StreamRepr(data[data.index(b"/Subrs") : ])
		header = strm.read_n_tokens(3)
		subroutine_count = int(header[1].decode("ascii"))
		for i in range(subroutine_count):
			(dup, subroutine_id, subroutine_length, start_subr_marker) = strm.read_n_tokens(4)
			subroutine_id = int(subroutine_id)
			subroutine_length = int(subroutine_length)
			encoded_subroutine_data = strm.read(subroutine_length)
			decoded_subroutine_data = T1PRNG(cls._T1_GLYPH_KEY).decrypt_bytes(encoded_subroutine_data)
			subroutines[subroutine_id] = T1Glyph(decoded_subroutine_data)
			end_subr_marker = strm.read_next_token()
		return subroutines

	def get_subroutine(self, subroutine_id):
		return self._subroutines.get(subroutine_id)

	def get_glyph(self, numeric_glyph):
		name = "/" + numeric_glyph.name
		return self.charset[name]

	def get_font_bbox(self):
		cleartext = self._cleardata.decode("ascii")
		result = self._FONT_BBOX_RE.search(cleartext)
		if result is None:
			raise Exception("/FontBBox not found in clear text data of T1 font.")
		result = result.groupdict()
		return [ int(result["v1"]), int(result["v2"]), int(result["v3"]), int(result["v4"]) ]

	def _parse_font(self):
		decrypted_data = self._decrypt_cipherdata()
		(self._charset, self._numeric_glyph_map) = self._parse_glyphs(decrypted_data)
		self._subroutines = self._parse_subroutines(decrypted_data)

	@classmethod
	def from_fontfile_obj(cls, fontfile_object):
		length1 = fontfile_object.content[PDFName("/Length1")]
		length2 = fontfile_object.content[PDFName("/Length2")]
		length3 = fontfile_object.content[PDFName("/Length3")]
		data = fontfile_object.stream.decode()

		cleardata = data[ : length1]
		cipherdata = data[length1 : length1 + length2]
		trailerdata = data[length1 + length2 : ]
		return cls(cleardata, cipherdata, trailerdata)

	@classmethod
	def from_pfb_file(cls, filename):
		with open(filename, "rb") as f:
			data = [ ]
			for expect_magic in [ 0x180, 0x280, 0x180]:
				(magic, length) = cls._PFB_HEADER.unpack(f.read(6))
				assert(magic == expect_magic)
				data.append(f.read(length))
			(cleardata, cipherdata, trailerdata) = data
		return cls(cleardata, cipherdata, trailerdata)

	def to_fontfile_obj(self, objid):
		content = {
			PDFName("/Length1"):	len(self._cleardata),
			PDFName("/Length2"):	len(self._cipherdata),
			PDFName("/Length3"):	len(self._trailerdata),
		}
		stream = EncodedObject.create(self._cleardata + self._cipherdata + self._trailerdata, compress = True)
		obj = PDFObject.create(objid, 0, content, stream)
		return obj

	def dump(self, filename_prefix):
		with open(filename_prefix + "1", "wb") as f:
			f.write(self._cleardata)
		with open(filename_prefix + "2", "wb") as f:
			f.write(self._decrypt_cipherdata())
		with open(filename_prefix + "3", "wb") as f:
			f.write(self._trailerdata)

	def __str__(self):
		return "T1Font<%d, %d, %d>" % (len(self._cleardata), len(self._cipherdata), 0)

if __name__ == "__main__":
	import sys
	if len(sys.argv) == 1:
		filename = "/usr/share/texlive/texmf-dist/fonts/type1/adobe/courier/pcrb8a.pfb"
	else:
		filename = sys.argv[1]

	print(filename)
	t1 = T1Font.from_pfb_file(filename)
	t1.dump("font_dump")

	for (charname, glyph) in sorted(t1.charset.items()):
		print(charname)
		canvas = NaiveDebuggingCanvas()
		commands = glyph.interpret(canvas = canvas, parent_font = t1)
		canvas.image.write_file("chars/" + charname[1:] + ".pnm")
