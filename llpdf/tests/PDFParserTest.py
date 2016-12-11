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

import unittest
from llpdf.repr import PDFParser
from llpdf.types.PDFName import PDFName
from llpdf.types.PDFXRef import PDFXRef

class PDFParserTest(unittest.TestCase):
	def test_name(self):
		self.assertEqual(PDFParser.parse("/Foo"), PDFName("/Foo"))
		self.assertEqual(PDFParser.parse("/Foo#20Bar"), PDFName("/Foo Bar"))

	def test_string_simple(self):
		self.assertEqual(PDFParser.parse("(Foo)"), b"Foo")
		self.assertEqual(PDFParser.parse("(Foo Bar)"), b"Foo Bar")
		self.assertEqual(PDFParser.parse("(Foo   Bar)"), b"Foo   Bar")
		self.assertEqual(PDFParser.parse("(Foo   Bar   )"), b"Foo   Bar   ")
		self.assertEqual(PDFParser.parse("( Foo)"), b" Foo")
		self.assertEqual(PDFParser.parse("(Foo )"), b"Foo ")
		self.assertEqual(PDFParser.parse("( Foo )"), b" Foo ")

	def test_string_escape_sequences(self):
		self.assertEqual(PDFParser.parse(r"(Foo\n)"), b"Foo\n")
		self.assertEqual(PDFParser.parse(r"(Foo\t\r\n)"), b"Foo\t\r\n")
		self.assertEqual(PDFParser.parse(r"(Foo\(\(\()"), b"Foo(((")
		self.assertEqual(PDFParser.parse(r"(Foo\)\)\)\(\(\()"), b"Foo)))(((")
		self.assertEqual(PDFParser.parse(r"(Foo\)\)\) \\\\\\ \(\(\()"), b"Foo))) \\\\\\ (((")
		self.assertEqual(PDFParser.parse(r"(Foo \\   Bar)"), b"Foo \\   Bar")
		self.assertEqual(PDFParser.parse(r"(Foo \\ \) Bar)"), b"Foo \\ ) Bar")

	def test_string_nested(self):
		self.assertEqual(PDFParser.parse("(Foo (Bar))"), b"Foo (Bar)")
		self.assertEqual(PDFParser.parse("(Foo( Bar))"), b"Foo( Bar)")
		self.assertEqual(PDFParser.parse("(Foo (Bar)   )"), b"Foo (Bar)   ")
		self.assertEqual(PDFParser.parse("(Foo ( Bar )   )"), b"Foo ( Bar )   ")
		self.assertEqual(PDFParser.parse("(Foo (Klammer) Bar)"), b"Foo (Klammer) Bar")
		self.assertEqual(PDFParser.parse("(Foo (Klammer (Klammer2) Yeah) Bar)"), b"Foo (Klammer (Klammer2) Yeah) Bar")
		self.assertEqual(PDFParser.parse("(Foo (Space)                   Yes)"), b"Foo (Space)                   Yes")

	def test_string_non_ascii(self):
		self.assertEqual(PDFParser.parse(r"(Foo \1 Bar)"), b"Foo \x01 Bar")
		self.assertEqual(PDFParser.parse(r"(Foo \12 Bar)"), b"Foo \x0a Bar")
		self.assertEqual(PDFParser.parse(r"(Foo \123 Bar)"), b"Foo S Bar")
		self.assertEqual(PDFParser.parse(r"(Foo \333 Bar)"), b"Foo \xdb Bar")
		self.assertEqual(PDFParser.parse("(Foo \xc4 Bar)"), b"Foo \xc4 Bar")

	def test_dict(self):
		self.assertEqual(PDFParser.parse("<< /Foo /Bar >>"), { PDFName("/Foo"): PDFName("/Bar") })
		self.assertEqual(PDFParser.parse("<< /Foo << /Bar /Koo>> >>"), { PDFName("/Foo"): { PDFName("/Bar"): PDFName("/Koo") } })
		self.assertEqual(PDFParser.parse("<< /Foobar13478 123 >>"), { PDFName("/Foobar13478"): 123 })

	def test_array(self):
		self.assertEqual(PDFParser.parse("[ 1 2 /Foo 3 4 ]"), [ 1, 2, PDFName("/Foo"), 3, 4])
		self.assertEqual(PDFParser.parse("[ /Foobar13478 /Barfoo999 ]"), [ PDFName("/Foobar13478"), PDFName("/Barfoo999") ])
		self.assertEqual(PDFParser.parse("[ 12345 9999 48 489 8473 << /foo 3939 >>]"), [ 12345, 9999, 48, 489, 8473, { PDFName("/foo"): 3939 } ])
		self.assertEqual(PDFParser.parse("[ 12345 9999 48 489 R 8473 3.43984 << /foo 3939 >>]"), [ 12345, 9999, PDFXRef(48, 489), 8473, 3.43984, { PDFName("/foo"): 3939 }])
		self.assertEqual(PDFParser.parse("[ 0.333679 0 0 0.333468 78.832642 172.074584 ]"), [ 0.333679, 0, 0, 0.333468, 78.832642, 172.074584 ])
		self.assertEqual(PDFParser.parse("[ 1.2345 1.2345 ]"), [ 1.2345, 1.2345 ] )

	def test_xref(self):
		self.assertEqual(PDFParser.parse("123 456 R"), PDFXRef(123, 456))
		self.assertEqual(PDFParser.parse("[ 123 456 R 999 888 R ]"), [ PDFXRef(123, 456), PDFXRef(999, 888) ])

	def test_int(self):
		self.assertEqual(PDFParser.parse("013478"), 13478)
		self.assertEqual(PDFParser.parse("13478"), 13478)
		self.assertEqual(PDFParser.parse("-913478"), -913478)

	def test_float(self):
		self.assertEqual(PDFParser.parse("-9.13478"), -9.13478)
		self.assertEqual(PDFParser.parse("13.478"), 13.478)
		self.assertEqual(PDFParser.parse(".13478"), 0.13478)
		self.assertEqual(PDFParser.parse("000.33478"), 0.33478)
		self.assertEqual(PDFParser.parse("10.000"), 10.0)

	def test_realworld_pdf(self):
		self.assertEqual(PDFParser.parse("""<<
			/Length 213 0 R
			/PatternType 1
			/BBox [0 0 2596 37]
			/XStep 8243
			/YStep 8243
			/TilingType 1
			/PaintType 1
			/Matrix [ 0.333679 0 0 0.333468 78.832642 172.074584 ]
			/Resources <<
				/XObject <<
					/x211 211 0 R
					>>
				>>
			>>"""), {
			PDFName("/Length"):			PDFXRef(213, 0),
			PDFName("/PatternType"):	1,
			PDFName("/BBox"):			[ 0, 0, 2596, 37 ],
			PDFName("/XStep"):			8243,
			PDFName("/YStep"):			8243,
			PDFName("/TilingType"):		1,
			PDFName("/PaintType"):		1,
			PDFName("/Matrix"):			[ 0.333679, 0, 0, 0.333468, 78.832642, 172.074584 ],
			PDFName("/Resources"): {
				PDFName("/XObject"): {
					PDFName("/x211"): PDFXRef(211, 0),
				},
			},
		})
		self.assertEqual(PDFParser.parse("<< /XHeight 0 /CharSet (/F) /FontFile 2992 0 R >>"), {
			PDFName("/XHeight"):	0,
			PDFName("/CharSet"):	b"/F",
			PDFName("/FontFile"):	PDFXRef(2992, 0),
		})
