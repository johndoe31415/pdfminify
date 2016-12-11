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
from llpdf.repr import GraphicsParser
from llpdf.repr.GraphicsParser import GraphCommand
from llpdf.types.PDFName import PDFName

class GraphicsParserTest(unittest.TestCase):
	def test_command_equality(self):
		self.assertEqual(GraphCommand("q"), GraphCommand("q"))
		self.assertNotEqual(GraphCommand("q", 0), GraphCommand("q"))
		self.assertNotEqual(GraphCommand("q"), GraphCommand("Q"))
		self.assertEqual(GraphCommand("q", 9, 3, 2.44), GraphCommand("q", 9, 3, 2.44))

	def test_simple_commands(self):
		self.assertEqual(GraphicsParser.parse("q"), [ GraphCommand("q") ])
		self.assertNotEqual(GraphicsParser.parse("q"), [ GraphCommand("Q") ])
		self.assertEqual(GraphicsParser.parse("q Q"), [ GraphCommand("q"), GraphCommand("Q") ])
		self.assertEqual(GraphicsParser.parse("q\n\n\t \n\n\nq\n\n"), [ GraphCommand("q"), GraphCommand("q") ])
		self.assertEqual(GraphicsParser.parse("1\n2\t3 4 5 6\n\ncm"), [ GraphCommand("cm", 1, 2, 3, 4, 5, 6) ])

	def test_array_arg(self):
		self.assertEqual(GraphicsParser.parse("<</Foo /Bar>>TJ"), [ GraphCommand("TJ", { PDFName("/Foo"): PDFName("/Bar") }) ])
		self.assertEqual(GraphicsParser.parse(r"[(some in-depth )3(things\).)]TJ"), [ GraphCommand("TJ", [ "(some in-depth )", 3, "(things\).)" ])])

	def test_real_pdf_data(self):
		result = GraphicsParser.parse("""
		q
		Q q
		79 841.89 516 -763 re W n
		1 1 1 rg /a0 gs
		79 1055.499 579.5 -976.5 re f
		0.666656 0.666656 0.666656 RG 1 w
		0 J
		0 j
		[ 1 1] 0.5 d
		10 M q 0 1 -1 0 0 841.889764 cm
		102.609 -79.5 -865 -485 re S Q
		Q q
		79.5 841.89 484.727 -762.391 re W n
		q
		0 866.230684 -486.499608 0 565.332662 78.832642 cm
		/a0 gs /x5 Do
		Q
		1 1 1 rg /a0 gs
		BT
		0 66 -66 0 167.850006 107.849998 Tm
		/f-0-0 1 Tf
		[(FOO)3(BARY )3(BARFOO)3(BA)]TJ
		0 -1.121212 Td
		[(MOO KO)20(KOO)21(LOLS)3(KIX)]TJ
		ET
		Q
		""")
		self.assertEqual(result, [
			GraphCommand("q"),
			GraphCommand("Q"),
			GraphCommand("q"),
			GraphCommand("re", 79, 841.89, 516, -763),
			GraphCommand("W"),
			GraphCommand("n"),
			GraphCommand("rg", 1, 1, 1),
			GraphCommand("gs", PDFName("/a0")),
			GraphCommand("re", 79, 1055.499, 579.5, -976.5),
			GraphCommand("f"),
			GraphCommand("RG", 0.666656, 0.666656, 0.666656),
			GraphCommand("w", 1),
			GraphCommand("J", 0),
			GraphCommand("j", 0),
			GraphCommand("d", [ 1, 1 ], 0.5),
			GraphCommand("M", 10),
			GraphCommand("q"),
			GraphCommand("cm", 0, 1, -1, 0, 0, 841.889764),
			GraphCommand("re", 102.609, -79.5, -865, -485),
			GraphCommand("S"),
			GraphCommand("Q"),
			GraphCommand("Q"),
			GraphCommand("q"),
			GraphCommand("re", 79.5, 841.89, 484.727, -762.391),
			GraphCommand("W"),
			GraphCommand("n"),
			GraphCommand("q"),
			GraphCommand("cm", 0, 866.230684, -486.499608, 0, 565.332662, 78.832642),
			GraphCommand("gs", PDFName("/a0")),
			GraphCommand("Do", PDFName("/x5")),
			GraphCommand("Q"),
			GraphCommand("rg", 1, 1, 1),
			GraphCommand("gs", PDFName("/a0")),
			GraphCommand("BT"),
			GraphCommand("Tm", 0, 66, -66, 0, 167.850006, 107.849998),
			GraphCommand("Tf", PDFName("/f-0-0"), 1),
			GraphCommand("TJ", [ "(FOO)", 3, "(BARY )", 3, "(BARFOO)", 3, "(BA)" ]),
			GraphCommand("Td", 0, -1.121212),
			GraphCommand("TJ", [ "(MOO KO)", 20, "(KOO)", 21, "(LOLS)", 3, "(KIX)" ]),
			GraphCommand("ET"),
			GraphCommand("Q"),
		])
