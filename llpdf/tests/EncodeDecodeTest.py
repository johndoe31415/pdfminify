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

import zlib
import base64
import unittest
from llpdf.EncodeDecode import EncodedObject, Filter, Predictor

class EncodeDecodeTest(unittest.TestCase):
	def setUp(self):
		self._data = {
			"linear": bytes(range(13 * 11)),
		}

		self._data["prng"] = bytearray()
		state = 0xaabbccdd
		for i in range(13 * 11):
			state = ((state * 1664525) + 1013904223) & 0xffffffff
			self._data["prng"].append(state & 0xff)

	def test_no_decompress(self):
		uncompressed_data = b"Foobar"
		obj = EncodedObject(uncompressed_data, Filter.Uncompressed)
		self.assertEqual(obj.decode(), b"Foobar")

	def test_flate_decompress(self):
		compressed_data = bytes.fromhex("78 9c 73 cb cf 4f 4a 2c  02 00 07 eb 02 5a")
		obj = EncodedObject(compressed_data, Filter.FlateDecode)
		self.assertEqual(obj.decode(), b"Foobar")

	def _test_png_predictors(self, columns, encoded_data, pixel_data):
		obj = EncodedObject(encoded_data, Filter.Uncompressed, columns = columns, predictor = Predictor.PNGPredictionOptimum)
		obj_decode = obj.decode()
		self.assertEqual(len(obj_decode), len(pixel_data))
		for line_offset in range(0, len(pixel_data), columns):
			self.assertEqual(obj_decode[line_offset : line_offset + columns], pixel_data[line_offset : line_offset + columns], "Row %d" % (line_offset // columns))
		self.assertEqual(obj_decode, pixel_data)

	def test_png_predictors_linear_0(self):
		# n_linear.png: 13 x 11, 8 bpp, color = ColorType.Grayscale, 1 bytes/pixel, compression = 0, filter = 0, interlace = 0
		# predictor methods: 0
		columns = 13
		encoded_data = zlib.decompress(base64.b64decode("""
			eJxjYGBkYmZhZWPn4OTi5mHg5eMXEBQSFhEVE5eQZJCSlpGVk1dQVFJWUVVjUNfQ1NLW0d
			XTNzA0MmYwMTUzt7C0sraxtbN3YHB0cnZxdXP38PTy9vFl8PMPCAwKDgkNC4+IjGKIjomN
			i09ITEpOSU1LZ8jIzMrOyc3LLygsKi5hKC0rr6isqq6pratvaGRoam5pbWvv6Ozq7untAw
			DuYieq"""))
		pixel_data = self._data["linear"]
		self._test_png_predictors(columns, encoded_data, pixel_data)

	def test_png_predictors_prng_0(self):
		# n_prng.png: 13 x 11, 8 bpp, color = ColorType.Grayscale, 1 bytes/pixel, compression = 0, filter = 0, interlace = 0
		# predictor methods: 0
		columns = 13
		encoded_data = zlib.decompress(base64.b64decode("""
			eJwBmgBl/wCYF4phTDteJUCfcil0AEPGbegnWvGcSy61kK8AQrnEU5b9ODcqgexb/gBF4L
			8SSRRjZo2IR/oRADxrztUwz+LZZHM2HdgAV8qhjHueZYDfsmm0gwAGrShnmjHci2710O+C
			APkEk9Y9eHdqwSybPoUAIP9SiVSjps3IhzpRfACrDhVwDyIZpLN2XRiXAArhzLvepcAf8q
			n0w0bfL0dc"""))
		pixel_data = self._data["prng"]
		self._test_png_predictors(columns, encoded_data, pixel_data)

	def test_png_predictors_linear_1(self):
		# s_linear.png: 13 x 11, 8 bpp, color = ColorType.Grayscale, 1 bytes/pixel, compression = 0, filter = 0, interlace = 0
		# predictor methods: 1
		columns = 13
		encoded_data = zlib.decompress(base64.b64decode("""
			eJxjZGBEBrwoPCkUnjoKzwSF54jC80PhRaPwMlB4pSi8JmQOAMVFA1s="""))
		pixel_data = self._data["linear"]
		self._test_png_predictors(columns, encoded_data, pixel_data)

	def test_png_predictors_prng_1(self):
		# s_prng.png: 13 x 11, 8 bpp, color = ColorType.Grayscale, 1 bytes/pixel, compression = 0, filter = 0, interlace = 0
		# predictor methods: 1
		columns = 13
		encoded_data = zlib.decompress(base64.b64decode("""
			eJxjnFFffP31e+Xj0vGXt3szOjcvr7Y3nr56/eP22/KMTuXc/c7p1v8/h2fnL2Z0nX0/2P
			y0P7P67/2bxRlt9JPZo+cLf+/mP/x8N2M4kiHnGdmQDJnM+BPJEHdGBSRDtBlXIxlSz8iF
			ZEgzAKHGR/k="""))
		pixel_data = self._data["prng"]
		self._test_png_predictors(columns, encoded_data, pixel_data)

	def test_png_predictors_linear_2(self):
		# u_linear.png: 13 x 11, 8 bpp, color = ColorType.Grayscale, 1 bytes/pixel, compression = 0, filter = 0, interlace = 0
		# predictor methods: 2
		columns = 13
		encoded_data = zlib.decompress(base64.b64decode("""
			eJxjYmBkYmZhZWPn4OTi5mHiRQYDywMAAiAG/w=="""))
		pixel_data = self._data["linear"]
		self._test_png_predictors(columns, encoded_data, pixel_data)

	def test_png_predictors_prng_2(self):
		# u_prng.png: 13 x 11, 8 bpp, color = ColorType.Grayscale, 1 bytes/pixel, compression = 0, filter = 0, interlace = 0
		# predictor methods: 2
		columns = 13
		encoded_data = zlib.decompress(base64.b64decode("""
			eJxjmiHelehjHafqML9Is4Rp9frH7bflJ5dz9zunWzP9/xyenb/Yffb9YPPT/kzM6r/3bx
			bX1k9mj54vzPS9m//w8931xddfv1c+ziQdf3m79/nm5dX2xtNXMyEb8p8J2RBmJmRDvjMh
			GyLNhGzIegCKJkaD"""))
		pixel_data = self._data["prng"]
		self._test_png_predictors(columns, encoded_data, pixel_data)

	def test_png_predictors_linear_3(self):
		# a_linear.png: 13 x 11, 8 bpp, color = ColorType.Grayscale, 1 bytes/pixel, compression = 0, filter = 0, interlace = 0
		# predictor methods: 3
		columns = 13
		encoded_data = zlib.decompress(base64.b64decode("""
			eJxjZmBkYmJmZmFhZWVjY2fmZUcCzCIoPCkUniIKTx2Fp4fCM0HhWaPwHFF4Hsg8AGt/BU
			M="""))
		pixel_data = self._data["linear"]
		self._test_png_predictors(columns, encoded_data, pixel_data)

	def test_png_predictors_prng_3(self):
		# a_prng.png: 13 x 11, 8 bpp, color = ColorType.Grayscale, 1 bytes/pixel, compression = 0, filter = 0, interlace = 0
		# predictor methods: 3
		columns = 13
		encoded_data = zlib.decompress(base64.b64decode("""
			eJxjnnG6XkZG1PGbXr3yhwTm7zOPNvZqThW8uzNVUZdZ0dSwNrLV8ezL0MC5lcwqiW87vx
			baSroy9q4UZZa6a5m6cK2n6ca/N1sPMltmXr0o+3Ppw1zOr4V7mW+7NvJqTp0INuQk8ze4
			IbKVqsxLgIZ8BBnCu1JUkHm25VPFtSe3Gv69yXrQl3nrVZCSxFyQNTMBUjtEVA=="""))
		pixel_data = self._data["prng"]
		self._test_png_predictors(columns, encoded_data, pixel_data)

	def test_png_predictors_linear_4(self):
		# p_linear.png: 13 x 11, 8 bpp, color = ColorType.Grayscale, 1 bytes/pixel, compression = 0, filter = 0, interlace = 0
		# predictor methods: 4
		columns = 13
		encoded_data = zlib.decompress(base64.b64decode("""
			eJxjYWBEAiy8g4cHAF0UATM="""))
		pixel_data = self._data["linear"]
		self._test_png_predictors(columns, encoded_data, pixel_data)

	def test_png_predictors_prng_4(self):
		# p_prng.png: 13 x 11, 8 bpp, color = ColorType.Grayscale, 1 bytes/pixel, compression = 0, filter = 0, interlace = 0
		# predictor methods: 4
		columns = 13
		encoded_data = zlib.decompress(base64.b64decode("""
			eJxjmVFffP31e+Xj0vGXt3uzrF6/vN3eePLq9f3tcvIs/z+HZ+enWwMp82V5LMzq9/d/q/
			NnVv8dvVmY5Xt38uHo3cLfu/mBmlmAul97nz8uXX35m/dqlvVhCEPOsXzm7ndOd58NNCQ/
			z51F/XfwN3FtkCHzxb+zdPOzy+0+BzZktxtLPNAleSCXfPM+3wwAUnlJYw=="""))
		pixel_data = self._data["prng"]
		self._test_png_predictors(columns, encoded_data, pixel_data)

	def test_png_predictors_linear_14(self):
		# suap_linear.png: 13 x 11, 8 bpp, color = ColorType.Grayscale, 1 bytes/pixel, compression = 0, filter = 0, interlace = 0
		# predictor methods: 1, 4
		columns = 13
		encoded_data = zlib.decompress(base64.b64decode("""
			eJxjZGBEBrzIHJYB5QEAWaIBLQ=="""))
		pixel_data = self._data["linear"]
		self._test_png_predictors(columns, encoded_data, pixel_data)

	def test_png_predictors_prng_1234(self):
		# suap_prng.png: 13 x 11, 8 bpp, color = ColorType.Grayscale, 1 bytes/pixel, compression = 0, filter = 0, interlace = 0
		# predictor methods: 1, 2, 3, 4
		columns = 13
		encoded_data = zlib.decompress(base64.b64decode("""
			eJxjnnG6XkZG1PGbXr3yhwTm7zOPNvZqThW8uzNVUZfl/+fw7Px0ayBlviyPhVn9/v5vdf
			7M6r+jNwszfe/mP/x8d33x9dfvlY8zW2ZevSj7c+nDXM6vhXuZb7s28mpOnQg25CTjT+5+
			Z7Ah2fmL3VnUfwd/E9cGGTJf/DtLNz+73O5zQLPeK+92Y+QCGyYdf3m79/lmAOkKSOw="""))
		pixel_data = self._data["prng"]
		self._test_png_predictors(columns, encoded_data, pixel_data)
