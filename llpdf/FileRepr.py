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

class StreamRepr(object):
	def __init__(self, buf):
		self._buf = buf
		self._offset = 0

	def tell(self):
		return self._offset

	def seek(self, offset):
		if offset < 0:
			self._offset = 0
		elif offset > len(self._buf):
			self._offset = len(self._buf)
		self._offset = offset

	def read(self, length):
		data = self._buf[self._offset : self._offset + length]
		self._offset += len(data)
		return data

	def read_until(self, terminals, chunksize = 128):
		pos = self.tell()
		result = bytearray()
		while True:
			new_data = self.read(chunksize)
			if len(new_data) == 0:
				break
			result += new_data
			for terminal in terminals:
				idx = result.find(terminal, max(len(result) - chunksize - len(terminal), 0))
				if idx != -1:
					result = result[:idx]
					self.seek(pos + len(result) + len(terminal))
					return (result, terminal)

	def readline(self):
		(data, terminal) = self.read_until([ b"\n", b"\r\n", b"\r" ])
		return data

	def readline_nonempty(self):
		while True:
			line = self.readline()
			if line != b"":
				return line

	@classmethod
	def from_file(cls, f):
		data = f.read()
		return cls(data)

