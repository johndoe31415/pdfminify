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
from llpdf.EncodeDecode import EncodedObject, Filter

class EncodeDecodeTest(unittest.TestCase):
	def test_no_decompress(self):
		uncompressed_data = b"Foobar"
		obj = EncodedObject(uncompressed_data, Filter.Uncompressed)
		self.assertEqual(obj.decode(), b"Foobar")

	def test_flate_decompress(self):
		compressed_data = bytes.fromhex("78 9c 73 cb cf 4f 4a 2c  02 00 07 eb 02 5a")
		obj = EncodedObject(compressed_data, Filter.FlateDecode)
		self.assertEqual(obj.decode(), b"Foobar")


