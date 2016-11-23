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
			raise Exception(NotImplemented)

	def _depredict(self, deencoded_data):
		if self.predictor == Predictor.NoPredictor:
			return deencoded_data
		elif self.predictor == Predictor.PNGPredictionUp:
			result = bytearray()
			previous_scanline = bytes(self.columns)
			for i in range(0, len(deencoded_data), self.columns + 1):
				png_filter = deencoded_data[i]
				scanline = deencoded_data[i + 1 : i + self.columns + 1]
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

	@classmethod
	def create(cls, unencoded_data, compress = True):
		if compress:
			zlib_encoded_data = zlib.compress(unencoded_data)
			enc_object = cls(encoded_data = zlib_encoded_data, filtering = Filter.FlateDecode)
		else:
			enc_object = cls(encoded_data = unencoded_data, filtering = Filter.Uncompressed)
		return enc_object

	@classmethod
	def from_object(cls, obj):
		if PDFName("/Filter") in obj.content:
			filtering = cls._REV_FILTER_MAP[obj.content[PDFName("/Filter")]]
		else:
			filtering = Filter.Uncompressed

		if PDFName("/DecodeParms") in obj.content:
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
		return "CompressedObject<%s>" % (", ".join(details))

if __name__ == "__main__":
	with open("xref.bin", "rb") as f:
		data = f.read()
	enc = EncodedObject(data, filtering = Filter.Uncompressed, columns = 5, predictor = Predictor.PNGPredictionUp)
	print(enc)
	print(enc.decode().hex())

