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

import enum
import zlib

class Filter(enum.IntEnum):
	Uncompressed = 0
	FlateDecode = 1
	RunLengthDecode = 2
	CCITTFaxDecode = 3
	ASCIIHexDecode = 4
	ASCII85Decode = 5

class Predictor(enum.IntEnum):
	NoPredictor = 1
	TIFFPredictor2 = 2
	PNGPredictionNone = 10
	PNGPredictionSub = 11
	PNGPredictionUp = 12
	PNGPredictionAverage = 13
	PNGPredictionPaeth = 14
	PNGPredictionOptimum = 15

class EncodedObject(object):
	def __init__(self, compressed_data, filtering, columns = 1, predictor = Predictor.NoPredictor):
		self._compressed_data = compressed_data
		self._filtering = filtering
		self._columns = columns
		self._predictor = predictor

	@property
	def filtering(self):
		return self._filtering

	@property
	def columns(self):
		return self._columns

	@property
	def predictor(self):
		return self._predictor

	def _decompress(self):
		"""Only decompress filter, but do not de-predict."""
		if self._filtering == Filter.Uncompressed:
			return self._compressed_data
		elif self._filtering == Filter.FlateDecode:
			return zlib.decompress(self._compressed_data)
		else:
			raise Exception(NotImplemented)

	def _depredict(self, decompressed_data):
		if self.predictor == Predictor.NoPredictor:
			return decompressed_data
		elif self.predictor == Predictor.PNGPredictionUp:
			result = bytearray()
			previous_scanline = bytes(self.columns)
			for i in range(0, len(decompressed_data), self.columns + 1):
				png_filter = decompressed_data[i]
				scanline = decompressed_data[i + 1 : i + self.columns + 1]
				if png_filter == 2:
					decompressed_scanline = bytes((prev + cur) & 0xff for (prev, cur) in zip(previous_scanline, scanline))
				else:
					raise Exception(NotImplemented)
				result += decompressed_scanline

				previous_scanline = decompressed_scanline
			return result
		else:
			raise Exception(NotImplemented)

	def decode(self):
		return self._depredict(self._decompress())

	def __len__(self):
		return len(self._compressed_data)

	def __str__(self):
		details = [ ]
		details.append("%d bytes" % (len(self)))
		details.append(self._filtering.name)
		if self.predictor != Predictor.NoPredictor:
			details.append(self.predictor.name)
			details.append("%d columns" % (self.columns))
		return "CompressedObject<%s>" % (", ".join(details))

if __name__ == "__main__":
	with open("xref.bin", "rb") as f:
		data = f.read()
	enc = EncodedObject(data, filtering = Filter.Uncompressed, columns = 5, predictor = Predictor.PNGPredictionUp)
	print(enc)
	print(enc.decode().hex())

