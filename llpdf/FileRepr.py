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

import os
import types

class _TempSeekObject(object):
	def __init__(self, f):
		self._f = f
		self._offset = self._f.tell()
		self._entered = 0

	@property
	def prev_offset(self):
		return self._offset

	def __enter__(self):
		self._entered += 1
		assert(self._entered == 1)
		return self

	def __exit__(self, *args):
		self._f.seek(self._offset)

class FileWriterDecorator(object):
	def writeline(self, text):
		return self.write((text + "\n").encode("utf-8"))

	def filesize(self):
		pos = self.tell()
		self.seek(0, os.SEEK_END)
		filesize = self.tell()
		self.seek(pos)
		return filesize

	@classmethod
	def wrap(cls, f):
		f.writeline = types.MethodType(cls.writeline, f)
		f.filesize = types.MethodType(cls.filesize, f)
		return f

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

	def advance(self, offset):
		self.seek(self.tell() + offset)

	def tempseek(self, offset):
		tempseek_obj = _TempSeekObject(self)
		self.seek(offset)
		return tempseek_obj

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
			found_terminals = [ (result.find(terminal, max(len(result) - chunksize - len(terminal), 0)), terminal) for terminal in terminals ]
			found_terminals = [ (idx, terminal) for (idx, terminal) in found_terminals if (idx != -1) ]
			if len(found_terminals) > 0:
				found_terminals.sort(key = lambda occurence: occurence[0] - len(occurence[1]))
				(idx, terminal) = found_terminals[0]
				result = result[:idx]
				self.seek(pos + len(result) + len(terminal))
				return (result, terminal)

	def read_until_token(self, token):
		# TODO: This is a performance disaster. Fix me later.
		possibilities = [ token + b"\r\n", token + b"\r", token + b"\n", token + b"\t", token + b" " ]
		return self.read_until(possibilities)

	def read_next_token(self):
		possibilities = [ b"\r\n", b"\r", b"\n", b"\t", b" " ]
		while True:
			next_token = self.read_until(possibilities)
			if next_token is None:
				return None
			if len(next_token[0].strip(b"\r\n\t ")) > 0:
				return next_token

	def read_n_tokens(self, count):
		return [ self.read_next_token()[0] for i in range(count) ]

	def readline(self):
		(data, terminal) = self.read_until([ b"\r\n", b"\n", b"\r" ])
		return data

	def readline_nonempty(self):
		while True:
			line = self.readline()
			if line.strip(b"\r\n \t") != b"":
				return line

	@classmethod
	def from_file(cls, f):
		data = f.read()
		return cls(data)

if __name__ == "__main__":
	f = StreamRepr(b"foobar barfoo mookoo\rline2\n")
	print(f.readline())
#	print(f.read_next_token())
#	print(f.read_next_token())
#	print(f.read_next_token())
