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

import subprocess

class X509Certificate(object):
	def __init__(self, cert_filename, cert_format = "pem"):
		self._cert_format = cert_format.lower()
		assert(self._cert_format in [ "der", "pem" ])
		self._subject = None
		self._issuer = None
		self._serial = None
		self._parse_cert(cert_filename)

	def _parse_cert(self, filename):
		output = subprocess.check_output([ "openssl", "x509", "-in", filename, "-inform", self._cert_format, "-noout", "-subject", "-issuer", "-serial" ])
		output = output.decode().split("\n")
		results = { }
		prefixes = [ "subject= ", "issuer= ", "serial=" ]
		for line in output:
			for prefix in prefixes:
				if line.startswith(prefix):
					results[prefix] = line[len(prefix): ]
					break
		self._subject = results["subject= "]
		self._issuer = results["issuer= "]
		self._serial = int(results["serial="], 16)

	@property
	def issuer(self):
		return self._issuer

	@property
	def subject(self):
		return self._subject

	@property
	def serial(self):
		return self._serial

	def __str__(self):
		return "Cert<%s, %s, 0x%x>" % (self.subject, self.issuer, self.serial)

if __name__ == "__main__":
	crt = X509Certificate("crt")
	print(crt)
