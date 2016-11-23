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

class PDFParserTest(unittest.TestCase):
	def test_name(self):
		self.assertEqual(PDFParser.parse("/Foo"), PDFName("/Foo"))
		self.assertEqual(PDFParser.parse("/Foo#20Bar"), PDFName("/Foo Bar"))

	def test_dict(self):
		self.assertEqual(PDFParser.parse("<< /Foo /Bar >>"), { PDFName("/Foo"): PDFName("/Bar") })

	def test_array(self):
		self.assertEqual(PDFParser.parse("[ 1 2 /Foo 3 4 ]"), [ 1, 2, PDFName("/Foo"), 3, 4])

