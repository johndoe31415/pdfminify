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

from . import tpg
from . import ParseTools
from llpdf.types.PDFName import PDFName
from llpdf.types.PDFXRef import PDFXRef

class PDFParser(tpg.VerboseParser):
	r"""
		separator space '[\s\n]+';

		token start_dict '<<';
		token end_dict '>>';
		token start_array '\[';
		token end_array '\]';
		token float '-?\d*\.\d+'							$ float
		token integer '-?\d+'								$ int
		token bool 'true|false'								$ ParseTools.to_bool
		token null 'null'									$ None
		token pdfname_token '/[a-zA-Z0-9][-#+a-zA-Z0-9]*'	$ PDFName
		token hexstring '<[\na-fA-F0-9]*>'					$ ParseTools.to_hexstring
		token start_string '\(';
		token end_string '\)\s*';
		token string_content '[^\\()]+';
		token string_escape_numeric '\\[0-7]{3}\s*';
		token string_escape_char '\\.\s*';


		START/e -> PDFExpression/e
		;

		PDFExpression/e -> PDFXRef/e
							| PDFDict/e
							| PDFValue/e
							| PDFName/e
							| PDFArray/e
							| PDFString/e
		;

		PDFDict/d -> start_dict								$ d = dict()
						(
							PDFName/k PDFExpression/v		$ d[k] = v
						)*
						end_dict
		;

		PDFArray/a -> start_array							$ a = list()
						( PDFExpression/e					$ a.append(e)
						)* end_array
		;

		PDFName/e -> pdfname_token/e
		;

		PDFXRef/e -> integer/a integer/b 'R'				$ e = PDFXRef(a, b)
		;

		PDFValue/e -> float/e
					| integer/e
					| bool/e
					| null/e
					| hexstring/e
		;

		PDFString/s -> start_string							$ s = bytearray()
							PDFInnerString/e				$ s += e
						end_string
		;

		PDFInnerString/s ->													$ s = bytearray()
						(
							string_escape_numeric/e							$ s += ParseTools.interpret_escape_numeric(e)
							| string_escape_char/e							$ s += ParseTools.interpret_escape_char(e)
							| start_string/a PDFInnerString/e end_string/b	$ s += a.encode() + e + b.encode()
							| string_content/e								$ s += e.encode("utf-8")
						)+
		;

	"""

	verbose = 0


def parse(text):
	return ParseTools.parse_using(text, PDFParser)

if __name__ == "__main__":
	examples = [
		r"(Foo Bar)",
		r"(Foo \\   Bar)",
		r"(Foo \\ \) Bar)",
		"(Foo (Klammer) Bar)",
		"(Foo (Klammer (Klammer2) Yeah) Bar)",
		"(Foo (Space)                   Yes)",
		"13478",
		"<< /Foobar13478 123 >>",
		"[ /Foobar13478 /Barfoo999 ]",
		"[ 12345 9999 48 489 8473 << /foo 3939 >>]",
		"[ 12345 9999 48 489 R 8473 3.43984 << /foo 3939 >>]",
		"<< /Length 213 0 R    /PatternType 1    /BBox [0 0 2596 37]    /XStep 8243    /YStep 8243    /TilingType 1    /PaintType 1    /Matrix [ 0.333679 0 0 0.333468 78.832642 172.074584 ]    /Resources << /XObject << /x211 211 0 R >> >> >>",
		"[ 0.333679 0 0 0.333468 78.832642 172.074584 ]",
		"[ 1.2345 1.2345 ]"
	]

	for example in examples:
		print(parse(example))

