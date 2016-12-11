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
from llpdf.types.PDFName import PDFName

class Filter(enum.IntEnum):
	Uncompressed = 0
	FlateDecode = 1
	DCTDecode = 2
	RunLengthDecode = 3
	CCITTFaxDecode = 4
	ASCIIHexDecode = 5
	ASCII85Decode = 6

class PNGPredictor(enum.IntEnum):
	No = 0
	Sub = 1
	Up = 2
	Average = 3
	Paeth = 4

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
	_FILTER_MAP = {
		Filter.FlateDecode:		PDFName("/FlateDecode"),
		Filter.RunLengthDecode:	PDFName("/RunLengthDecode"),
		Filter.DCTDecode:		PDFName("/DCTDecode"),
		Filter.CCITTFaxDecode:	PDFName("/CCITTFaxDecode"),
		Filter.ASCIIHexDecode:	PDFName("/ASCIIHexDecode"),
		Filter.ASCII85Decode:	PDFName("/ASCII85Decode"),
	}
	_REV_FILTER_MAP = { value: key for (key, value) in _FILTER_MAP.items() }

	def __init__(self, encoded_data, filtering, columns = 1, predictor = Predictor.NoPredictor):
		self._encoded_data = encoded_data
		self._filtering = filtering
		self._columns = columns
		self._predictor = predictor

	@property
	def decompressible(self):
		return self._filtering != Filter.DCTDecode

	@property
	def compressed(self):
		return self._filtering != Filter.Uncompressed

	@property
	def encoded_data(self):
		return self._encoded_data

	@property
	def filtering(self):
		return self._filtering

	@property
	def columns(self):
		return self._columns

	@property
	def predictor(self):
		return self._predictor

	@property
	def lossless(self):
		return self._filtering != Filter.DCTDecode

	@property
	def meta_dict(self):
		meta = {
			PDFName("/Length"):		len(self),
		}
		if self._filtering != Filter.Uncompressed:
			meta[PDFName("/Filter")] = self._FILTER_MAP[self._filtering]
		if self._predictor != Predictor.NoPredictor:
			meta[PDFName("/DecodeParms")] = {
				PDFName("/Columns"): self.columns,
				PDFName("/Predictor"): int(self.predictor),
			}
		return meta

	def update_meta_dict(self, content_object):
		if PDFName("/Filter") in content_object:
			del content_object[PDFName("/Filter")]
		if PDFName("/DecodeParms") in content_object:
			del content_object[PDFName("/DecodeParms")]
		content_object.update(self.meta_dict)

	@staticmethod
	def _rle_decode(rle_data):
		result = bytearray()
		index = 0
		while index < len(rle_data):
			length = rle_data[index]
			index += 1
			if 0 <= length <= 127:
				bytecnt = 1 + length
				result += rle_data[index : index + bytecnt]
				index += bytecnt
			elif length == 128:
				# EOD
				break
			else:
				bytecnt = 257 - length
				value = rle_data[index]
				result += bytecnt * bytes([ value ])
				index += 1
		return result

	def _decompress(self):
		"""Only decompress filter, but do not de-predict."""
		if self._filtering == Filter.Uncompressed:
			return self._encoded_data
		elif self._filtering == Filter.FlateDecode:
			return zlib.decompress(self._encoded_data)
		elif self._filtering == Filter.RunLengthDecode:
			return self._rle_decode(self._encoded_data)
		else:
			raise Exception(NotImplemented, self._filtering)

	@staticmethod
	def _paeth_predictor(a, b, c):
		# a = left, b = above, c = upper left
		p = a + b - c
		pa = abs(p - a)
		pb = abs(p - b)
		pc = abs(p - c)
		if (pa <= pb) and (pa <= pc):
			return a
		elif pb <= pc:
			return b
		else:
			return c

	def _depredict(self, deencoded_data):
		if self.predictor == Predictor.NoPredictor:
			return deencoded_data
		else:
			result = bytearray()
			previous_scanline = bytes(self.columns)
			for i in range(0, len(deencoded_data), self.columns + 1):
				png_filter = PNGPredictor(deencoded_data[i])
				scanline = deencoded_data[i + 1 : i + self.columns + 1]
				if png_filter == PNGPredictor.No:
					decompressed_scanline = scanline
				elif png_filter == PNGPredictor.Sub:
					previous_value = 0
					decompressed_scanline = bytearray()
					for (index, value) in enumerate(scanline):
						new_value = (value + previous_value) & 0xff
						decompressed_scanline.append(new_value)
						previous_value = new_value
				elif png_filter == PNGPredictor.Up:
					decompressed_scanline = bytes((prev + cur) & 0xff for (prev, cur) in zip(previous_scanline, scanline))
				elif png_filter == PNGPredictor.Average:
					previous_value = 0
					decompressed_scanline = bytearray()
					for (index, value) in enumerate(scanline):
						new_value = (value + ((previous_value + previous_scanline[index]) // 2)) & 0xff
						decompressed_scanline.append(new_value)
						previous_value = new_value
				elif png_filter == PNGPredictor.Paeth:
					previous_value = 0
					decompressed_scanline = bytearray()
					for (index, value) in enumerate(scanline):
						new_value = (value + self._paeth_predictor(previous_value, previous_scanline[index], previous_scanline[index - 1] if (index > 0) else 0)) & 0xff
						decompressed_scanline.append(new_value)
						previous_value = new_value
				else:
					raise Exception(NotImplemented, png_filter)
				result += decompressed_scanline
#				print("%2d %2d: %s" % (int(png_filter), i // (self.columns + 1), scanline.hex()))
#				print("   %2d: %s" % (i // (self.columns + 1), decompressed_scanline.hex()))
				previous_scanline = decompressed_scanline
			return result

	def decode(self):
		return self._depredict(self._decompress())

	@classmethod
	def _predict(cls, unpredicted_data, columns):
		assert(len(unpredicted_data) % columns == 0)
		rows = len(unpredicted_data) // columns

		predicted_data = bytearray()
		if rows == 1:
			predictor = Predictor.PNGPredictionSub
			predicted_data.append(PNGPredictor.Sub)
			predicted_data += bytearray((x - y) & 0xff for (x, y) in zip(unpredicted_data[1:], unpredicted_data))
		else:
			predictor = Predictor.PNGPredictionUp
			previous_scanline = bytes(columns)
			for row in range(rows):
				scanline = unpredicted_data[row * columns : (row + 1) * columns]
				predicted_data.append(PNGPredictor.Up)
				predicted_data += bytearray((x - y) & 0xff for (x, y) in zip(previous_scanline, scanline))

		return (predicted_data, predictor, columns)

	@classmethod
	def create(cls, unencoded_data, compress = True, predict = False, columns = None):
		if predict:
			if columns is None:
				columns = len(unencoded_data)
			(predicted_data, used_predictor, predictor_columns) = cls._predict(unencoded_data, columns)
		else:
			(predicted_data, used_predictor, predictor_columns) = (unencoded_data, Predictor.NoPredictor, 1)

		if compress:
			encoded_data = zlib.compress(predicted_data)
			filtering = Filter.FlateDecode
		else:
			encoded_data = predicted_data
			filtering = Filter.Uncompressed
		encoded_object = cls(encoded_data = encoded_data, filtering = filtering, predictor = used_predictor, columns = predictor_columns)
		return encoded_object

	@classmethod
	def from_object(cls, obj):
		if PDFName("/Filter") in obj.content:
			pdf_filter = obj.content[PDFName("/Filter")]
			if isinstance(pdf_filter, list):
				if len(pdf_filter) == 1:
					pdf_filter = pdf_filter[0]
				else:
					raise Exception("Cannot create EncodedObject from object that has multiple filters applied: %s" % (str(pdf_filter)))
			filtering = cls._REV_FILTER_MAP[pdf_filter]
		else:
			filtering = Filter.Uncompressed

		if (PDFName("/DecodeParms") in obj.content) and (PDFName("/Predictor") in obj.content[PDFName("/DecodeParms")]):
			predictor = Predictor(obj.content[PDFName("/DecodeParms")][PDFName("/Predictor")])
			columns = obj.content[PDFName("/DecodeParms")][PDFName("/Columns")]
		else:
			predictor = Predictor.NoPredictor
			columns = 1

		return cls(encoded_data = obj.raw_stream, filtering = filtering, predictor = predictor, columns = columns)

	def __len__(self):
		return len(self._encoded_data)

	def __str__(self):
		details = [ ]
		details.append("%d bytes" % (len(self)))
		details.append(self._filtering.name)
		if self.predictor != Predictor.NoPredictor:
			details.append(self.predictor.name)
			details.append("%d columns" % (self.columns))
		return "EncodedObject<%s>" % (", ".join(details))

if __name__ == "__main__":
	with open("xref.bin", "rb") as f:
		data = f.read()
	enc = EncodedObject(data, filtering = Filter.Uncompressed, columns = 5, predictor = Predictor.PNGPredictionUp)
	print(enc)
	print(enc.decode().hex())

	data = b"Foobar Bar Foobar " * 25
	print(EncodedObject.create(data, predict = True, columns = len(data) // 25))
	print(EncodedObject.create(data, predict = False))
	print(data)
