#!/usr/bin/python3
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
from . import tpg

def to_bool(value):
	return value == "true"

def to_hexstring(text):
	text = text[1 : -1]
	text = text.replace("\n", "")
	return bytes.fromhex(text)

def interpret_escape_char(text):
	result = {
		r"\r":		b"\r",
		r"\n":		b"\n",
		r"\t":		b"\t",
		r"\(":		b"(",
		r"\)":		b")",
		r"\\":		b"\\",
	}.get(text[0 : 2])
	if result is None:
		raise Exception("Unknown escape character sequence %s in string input." % (text.encode("utf-8")))
	return result + text[2:].encode("ascii")

_numeric_regex = re.compile(r"\\(?P<code>\d{1,3})(?P<space>\s*)")
def interpret_escape_numeric(text):
	result = _numeric_regex.fullmatch(text)
	result = result.groupdict()
	value = int(result["code"], 8)
	return bytes([ value ]) + result["space"].encode("ascii")

def parse_using(text, parser_class):
	try:
		parser = parser_class()
		result = parser(text)
	except (tpg.LexicalError, tpg.SyntacticError) as e:
		print("-" * 120)
		print(text)
		print("-" * 120)
		print(text.split("\n")[e.line - 1])
		print((" " * (e.column - 1)) + "^")
		raise
	return result
