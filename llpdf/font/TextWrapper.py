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

import collections
from llpdf.font.PostScriptEnums import character_names

class TextWrapper(object):
	_Character = collections.namedtuple("Character", [ "index", "char", "prefer_break", "cumulative_width" ])

	def __init__(self, t1font, text_width, font_size, prefer_break_on = " "):
		self._font = t1font
		self._text_width = text_width
		self._font_size = font_size
		self._missing_width = self._font.get_missing_width()
		self._prefer_break_on = prefer_break_on
		self._subsequent_indent = 15
		self._widths = { }

	def _get_glyph_width(self, char):
		if char not in self._widths:
			charname = character_names.get(char)
			if charname is None:
				glyph_width = self._missing_width
			else:
				glyph = self._font.charset.get("/" + charname)
				glyph_width = glyph.width
			self._widths[char] = glyph_width / 1000 * self._font_size
		return self._widths[char]

	def _get_cumulative_width(self, text):
		cumulative_width = 0
		for (index, char) in enumerate(text):
			glyph_width = self._get_glyph_width(char)
			prefer_break = char in self._prefer_break_on
			cumulative_width += glyph_width
			yield self._Character(index = index, char = char, prefer_break = prefer_break, cumulative_width = cumulative_width)

	def _wrap_paragraph(self, text):
		cumulative_width = list(self._get_cumulative_width(text))
		current_width = 0
		break_at = None
		breaks = [ ]
		for char in cumulative_width:
			#print(char, self._text_width - (char.cumulative_width - current_width))
			if (char.cumulative_width - current_width) > self._text_width:
				# We need a break. Do we have a preferred break?
				if break_at is None:
					# No, just break hard.
					breaks.append(char.index)
					current_width = cumulative_width[char.index - 1].cumulative_width - self._subsequent_indent
				else:
					# Yes, we can.
					if break_at.char == " ":
						breaks.append(break_at.index + 1)
						current_width = cumulative_width[break_at.index].cumulative_width - self._subsequent_indent
					else:
						breaks.append(break_at.index)
						current_width = cumulative_width[break_at.index + 1].cumulative_width - self._subsequent_indent
					break_at = None
			else:
				if char.prefer_break:
					break_at = char

		breaks.insert(0, 0)
		breaks.append(len(cumulative_width))
		lines = [ ]
		for (start, end) in zip(breaks, breaks[1:]):
			chars = text[start : end]
			lines.append(chars)
		return lines

	def _join_lines(self, lines):
		text = [ "[ %s ] TJ" % (self._font.encode_text(line)) for line in lines ]
		if len(text) >= 2:
			text[1] = "    %d 0 Td %s" % (self._subsequent_indent, text[1])
			text[-1] += " %d 0 Td" % (-self._subsequent_indent)
		return text

	def wrap_paragraphs(self, paragraphs):
		lines = [ ]
		for paragraph in paragraphs:
			lines += self._join_lines(self._wrap_paragraph(paragraph))
		text = " T*\n".join(lines)
		text = text.encode("ascii")
		return text

	def __str__(self):
		return "TextWrap<%d pt to %.0f>" % (self._font_size, self._text_width)

if __name__ == "__main__":
	from .T1Font import T1Font
	font = T1Font.from_pfb_file("/usr/share/texlive/texmf-dist/fonts/type1/bitstrea/charter/bchr8a.pfb")
	wrapper = TextWrapper(font, font_size = 8, text_width = 100, prefer_break_on = "")
	print(wrapper)
	print(wrapper.wrap_paragraphs(["A"]))
