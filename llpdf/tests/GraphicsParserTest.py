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
		#self.assertEqual(GraphicsParser.parse("[(some in-depth )3(things\).)]TJ"), [ GraphCommand("TJ", [ "(some in-depth )", 3, "(things).)" ]), ])
