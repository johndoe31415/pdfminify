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

from llpdf.font.T1Interpreter import T1Interpreter
from llpdf.font.T1Command import T1Command, T1CommandCode

class T1Glyph(object):
	def __init__(self, glyph_data):
		self._data = glyph_data
		self._parsed_glyph = None

	def _parse(self):
		stack = [ ]
		commands = [ ]
		index = 0
		#print(self._data.hex())
		while index < len(self._data):
			v = self._data[index]
			#print("Next %02x at %d" % (v, index))
			if 0 <= v < 32:
				# Command!
				if v == T1CommandCode.escape:
					w = self._data[index + 1]
					index += 1
					v = (v << 8) | w
				cmdcode = T1CommandCode(v)
				if cmdcode == T1CommandCode.div:
					# Directly execute the div
					div_result = stack[-2] / stack[-1]
					stack = stack[ : -2]
					stack.append(div_result)
				else:
					commands.append(T1Command(cmdcode, *stack))
					stack = [ ]
			elif 32 <= v <= 246:
				stack.append(v - 139)
			elif 247 <= v <= 250:
				w = self._data[index + 1]
				index += 1
				stack.append(((v - 247) * 256) + w + 108)
			elif 251 <= v <= 254:
				w = self._data[index + 1]
				index += 1
				stack.append(-(((v - 251) * 256) + w + 108))
			elif v == 255:
				value = self._data[index + 1 : index + 5]
				value = int.from_bytes(value, byteorder = "big", signed = True)
				stack.append(value)
				index += 4
			index += 1
		return commands

	def parse(self):
		if self._parsed_glyph is None:
			self._parsed_glyph = self._parse()
		return self._parsed_glyph

	def interpret(self, canvas = None, parent_font = None):
		interpreter = T1Interpreter(canvas = canvas, parent_font = parent_font)
		interpreter.run(self.parse())
		return interpreter

	@property
	def width(self):
		cmds = self.parse()
		cmd = cmds[0]
		if cmd.cmdcode == T1CommandCode.hsbw:
			return cmd[1]
		else:
			raise Exception("Do not know how to get width vector from commands:", cmds)

	@property
	def left_sidebearing(self):
		cmds = self.parse()
		cmd = cmds[0]
		if cmd.cmdcode == T1CommandCode.hsbw:
			return cmd[0]
		else:
			raise Exception("Do not know how to get width vector from commands:", cmds)

	@property
	def data(self):
		return self._data

	def __repr__(self):
		return str(self)

	def __str__(self):
		return "Glyph<%d bytes, w = %d, lsb = %d>" % (len(self._data), self.width, self.left_sidebearing)
