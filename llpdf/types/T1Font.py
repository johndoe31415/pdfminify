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

import zlib
from llpdf.FileRepr import StreamRepr
from llpdf.types.PDFName import PDFName

class _T1PRNG(object):
	_C1 = 52845
	_C2 = 22719

	def __init__(self, r = 55665):
		self._r = r & 0xffff

	def decrypt_byte(self, cipher):
		plain = (cipher ^ (self._r >> 8)) & 0xff
		self._r = (((cipher + self._r) & 0xffff) * self._C1 + self._C2) & 0xffff
		return plain

	def decrypt_bytes(self, data):
		return bytes(self.decrypt_byte(cipher) for cipher in data)


class T1Font(object):
	def __init__(self, cleardata, cipherdata, TODOdata):
		self._cleardata = cleardata
		self._cipherdata = cipherdata

	def decrypt(self):
		decrypted_data = _T1PRNG().decrypt_bytes(self._cipherdata)[4:]
		return decrypted_data

	def get_charstrings(self):
		data = self.decrypt()
		idx = data.index(b"/CharStrings")
		strm = StreamRepr(data[idx:])

		header = strm.read_n_tokens(5)
		char_count = int(header[1].decode("ascii"))
		for i in range(char_count):
			definition = strm.read_n_tokens(3)
			name = definition[0].decode("ascii")
			length = int(definition[1].decode("ascii"))
			strm.advance(length)
			strm.read_next_token()
			if name != "/.notdef":
				yield name

	def get_charset(self):
		return "".join(self.get_charstrings()).encode("ascii")

	@classmethod
	def from_fontfile_obj(cls, fontfile_object):
		length1 = fontfile_object.content[PDFName("/Length1")]
		length2 = fontfile_object.content[PDFName("/Length2")]
		length3 = fontfile_object.content[PDFName("/Length3")]
		data = fontfile_object.stream
		if fontfile_object.getattr(PDFName("/Filter")) == PDFName("/FlateDecode"):
			data = zlib.decompress(data)

		cleardata = data[ : length1]
		cipherdata = data[length1 : length1 + length2]
		otherdata = data[length1 + length2 : ]
		return cls(cleardata, cipherdata, otherdata)

	def __str__(self):
		return "T1Font<%d, %d, %d>" % (len(self._cleardata), len(self._cipherdata), 0)

if __name__ == "__main__":
	with open("ff1", "rb") as f1,  open("ff2", "rb") as f2:
		f1 = f1.read()
		f2 = f2.read()
	t1 = T1Font(f1, f2, b"")
	print(t1)
	print("".join(t1.get_charstrings()))
	print(len(list(t1.get_charstrings())))

