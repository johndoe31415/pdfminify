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
from llpdf.tools.OpenSSLVersion import OpenSSLVersion

class OpenSSLVersionTest(unittest.TestCase):
	def test_name(self):
		version = OpenSSLVersion("OpenSSL 1.0.2d  1 Mar 2016")
		self.assertEqual(int(version), 0x01000204f)
		self.assertEqual(version.date, "1 Mar 2016")

		version = OpenSSLVersion("OpenSSL 1.0.1e-fips 11 Feb 2013")
		self.assertEqual(int(version), 0x01000105f)
		self.assertEqual(version.date, "11 Feb 2013")

		version = OpenSSLVersion("OpenSSL 3.2.1 31 Dec 2099")
		self.assertEqual(int(version), 0x03020100f)
		self.assertEqual(version.date, "31 Dec 2099")
