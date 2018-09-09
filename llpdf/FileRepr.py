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
import enum

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

class TokenDelimiter(enum.IntEnum):
	CRLF = 0
	CR = 1
	LF = 2
	TAB = 3
	SPACE = 4
	EOF = 5

	def to_bytes(self):
		return {
			TokenDelimiter.CRLF:	b"\r\n",
			TokenDelimiter.CR:		b"\r",
			TokenDelimiter.LF:		b"\n",
			TokenDelimiter.TAB:		b"\t",
			TokenDelimiter.SPACE:	b" ",
		}[self]

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

	@property
	def at_eof(self):
		return self._offset == len(self._buf)

	def read_until(self, delimiters, chunksize = 128):
		assert(all(isinstance(delimiter, TokenDelimiter) for delimiter in delimiters))
		delimiters = set(delimiters)
		delimiter_patterns = [ (delimiter, delimiter.to_bytes()) for delimiter in sorted(delimiters) if (delimiter != TokenDelimiter.EOF) ]
		match_eof = TokenDelimiter.EOF in delimiters

		initial_pos = self.tell()
		result = bytearray()
		start_offset = 0
		while True:
			new_data = self.read(chunksize)
			if len(new_data) == 0:
				return None

			result += new_data

			matches = [ (result.find(pattern, start_offset), delimiter, pattern) for (delimiter, pattern) in delimiter_patterns ]
			matches = [ (index, delimiter, pattern) for (index, delimiter, pattern) in matches if (index != -1) ]
			if len(matches) > 0:
				# Take the one that comes earliest, i.e., with lowest offset
				matches.sort()
				(index, delimiter, pattern) = matches[0]
				found_data = result[ : index]
				self.seek(initial_pos + len(found_data) + len(pattern))
				return (found_data, delimiter)

			if self.at_eof and match_eof:
				return (result, TokenDelimiter.EOF)

			start_offset = len(result) - 2

	def _read_until_pattern(self, pattern, chunksize = 128):
		result = bytearray()
		start_offset = 0
		initial_pos = self.tell()
		while True:
			new_data = self.read(chunksize)
			if len(new_data) == 0:
				return None

			result += new_data
			index = result.find(pattern)
			if index != -1:
				found_data = result[ : index]
				self.seek(initial_pos + index)
				return found_data

			start_offset = len(result) - len(pattern)

	def read_until_token(self, token, rewind = False):
		match = self._read_until_pattern(token)
		if not match:
			return None
		pos = self.tell()
		token = self.read_next_token(accept_eof = True)
		if rewind:
			self.seek(pos)
		return match

	def read_next_token(self, accept_empty_data = False, accept_eof = False):
		delimiters = [ TokenDelimiter.CRLF, TokenDelimiter.CR, TokenDelimiter.LF, TokenDelimiter.TAB, TokenDelimiter.SPACE ]
		if accept_eof:
			delimiters.append(TokenDelimiter.EOF)
		while True:
			next_token = self.read_until(delimiters)
			if next_token is None:
				return None
			(data, delimiter) = next_token

			if (len(data.strip(b"\r\n\t ")) == 0) and (not accept_empty_data):
				continue
			return data

	def read_n_tokens(self, count):
		return [ self.read_next_token() for i in range(count) ]

	def readline(self):
		(data, delimiter) = self.read_until([ TokenDelimiter.CRLF, TokenDelimiter.LF, TokenDelimiter.CR, TokenDelimiter.EOF ])
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
