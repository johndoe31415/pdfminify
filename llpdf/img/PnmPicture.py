#!/usr/bin/python3
#
#	PnmPicture - Simple PNM picture abstraction.
#	Copyright (C) 2011-2012 Johannes Bauer
#
#	This file is part of jpycommon.
#
#	jpycommon is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	jpycommon is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with jpycommon; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>
#
#	File UUID 1942070a-e148-43ba-ab07-1ff75d53fe01

import math
import enum

class PnmPictureFormat(enum.IntEnum):
	Bitmap = 1
	Graymap = 2
	Pixmap = 3

# Coordinates: 0, 0 is upper left corner
class PnmPicture(object):
	_MAGIC_NUMBERS = {
		"P1":	("ascii", PnmPictureFormat.Bitmap),
		"P2":	("ascii", PnmPictureFormat.Graymap),
		"P3":	("ascii", PnmPictureFormat.Pixmap),
		"P4":	("binary", PnmPictureFormat.Bitmap),
		"P5":	("binary", PnmPictureFormat.Graymap),
		"P6":	("binary", PnmPictureFormat.Pixmap),
	}

	_SAVE_FORMAT = {
		PnmPictureFormat.Bitmap:	"P4",
		PnmPictureFormat.Graymap:	"P5",
		PnmPictureFormat.Pixmap:	"P6",
	}

	def __init__(self, width, height, data, img_format):
		assert(isinstance(width, int))
		assert(isinstance(height, int))
		assert(isinstance(data, (bytes, bytearray)))
		assert(isinstance(img_format, PnmPictureFormat))
		self._width = width
		self._height = height
		self._data = data
		self._img_format = img_format

		expected_size = self.expected_filesize(self._width, self._height, self._img_format)
		if expected_size != len(self._data):
			raise Exception("Expected %d bytes of data for a %d x %d image (type %s). Got %d bytes instead." % (expected_size, self._width, self._height, self._img_format.name, len(data)))

	@classmethod
	def new(cls, width, height):
		pixelcnt = width * height
		bytelen = 3 * pixelcnt
		data = bytearray([ 0xff ]) * bytelen
		return cls(width, height, data, PnmPictureFormat.Pixmap)

	def clone(self):
		return PnmPicture(self.width, self.height, bytearray(self.data), self.img_format)

	@classmethod
	def expected_filesize(cls, width, height, img_format):
		if img_format == PnmPictureFormat.Pixmap:
			return width * height * 3
		elif img_format == PnmPictureFormat.Graymap:
			return width * height * 1
		elif img_format == PnmPictureFormat.Bitmap:
			byte_width = (width + 7) // 8
			return byte_width * height * 1
		else:
			raise Exception(NotImplemented)

	@property
	def width(self):
		return self._width

	@property
	def height(self):
		return self._height

	@property
	def data(self):
		return bytes(self._data)

	@property
	def img_format(self):
		return self._img_format

	@property
	def pixelcnt(self):
		return self.width * self.height

	@classmethod
	def _read_line(cls, f):
		while True:
			line = f.readline()
			line = line.decode("utf-8").rstrip("\r\n")
			if not line.startswith("#"):
				return line

#	@classmethod
#	def create_from_raw_data(cls, width, height, raw_data, img_format):
#		"""This is similar to the constructor but different in one internal
#		way: It takes 'data' as raw PNM data (e.g., eight pixels per byte in
#		case of a Bitmap), while the constructor already handles the internal
#		file format."""
#		if img_format in [ PnmPictureFormat.Pixmap, PnmPictureFormat.Graymap ]:
#			data = raw_data
#		elif img_format == PnmPictureFormat.Bitmap:
#			pixelcnt = width * height
#			bytes_per_pixel = cls._BYTES_PER_PIXEL[img_format]
#			data = bytearray(pixelcnt * bytes_per_pixel)
#			byte_width = (width + 7) // 8
#			offset = 0
#			for (index, value) in enumerate(raw_data):
#				y = index // byte_width
#				for bit in range(8):
#					x = (8 * (index % byte_width)) + bit
#					if x < width:
#						pixel = int((value >> bit) != 0) * 255
#						data[offset] = pixel
#						offset += 1
#		else:
#			raise Exception(NotImplemented)
#
#		return cls(width = width, height = height, data = data, img_format = img_format)

	@classmethod
	def read_file(cls, filename):
		with open(filename, "rb") as f:
			# First line gives the data format
			data_format = cls._read_line(f)
			if data_format not in cls._MAGIC_NUMBERS:
				raise Exception("This image type (%s) is not supported at the moment." % (data_format))

			(encoding, img_format) = cls._MAGIC_NUMBERS[data_format]

			# Then the image geometry
			geometry = cls._read_line(f)
			(width, height) = (int(s) for s in geometry.split())
			pixelcnt = width * height

			# Only for non-bitmaps there's a number indicating the bpp
			if img_format == PnmPictureFormat.Bitmap:
				bpp = 1
			else:
				bpp = int(cls._read_line(f))
				assert(bpp == 255)

			if encoding == "binary":
				raw_data = bytearray(f.read())
			else:
				raw_data = bytearray(pixelcnt * bytes_per_pixel)		# TODO: undefined "bytes_per_pixel"
				for i in range(pixelcnt * bytes_per_pixel):
					raw_data[i] = int(f.readline())
			# TODO: This will fail for ASCII Bitmaps
			return cls(width = width, height = height, data = raw_data, img_format = img_format)

	@property
	def bytes_per_pixel(self):
		if self.img_format == PnmPictureFormat.Bitmap:
			raise Exception("Pixel operations on bitmaps are currently unsupported.")
		return {
			PnmPictureFormat.Graymap:	1,
			PnmPictureFormat.Pixmap:	3,
		}[self.img_format]

	def _getoffset(self, x, y):
		assert(0 <= x < self.width)
		assert(0 <= y < self.height)
		offset = self.bytes_per_pixel * ((y * self.width) + x)
		return offset

	@staticmethod
	def _blendpixel(pixel1, pixel2, opacity):
		assert(0 <= opacity <= 1)
		return tuple(round((x * (1 - opacity)) + (y * opacity)) for (x, y) in zip(pixel1, pixel2))

	def get_pixel(self, x, y):
		offset = self._getoffset(x, y)
		pixel = tuple(self._data[offset + i] for i in range(self.bytes_per_pixel))
		return pixel

	def set_pixel(self, x, y, pixel):
		assert(len(pixel) == self.bytes_per_pixel)
		offset = self._getoffset(x, y)
		for i in range(self.bytes_per_pixel):
			self._data[offset + i] = pixel[i]

	def set_pixel_antialiased(self, x, y, pixel):
		low_x = (x - 0.5)
		low_y = (y - 0.5)

		p0 = (int(low_x), int(low_y))
		p1 = (int(low_x) + 1, int(low_y))
		p2 = (int(low_x), int(low_y) + 1)
		p3 = (int(low_x) + 1, int(low_y) + 1)

		if (0 <= p0[0] < self.width) and (0 <= p0[1] < self.height):
			o0 = (1 - abs(p0[0] - low_x)) * (1 - abs(p0[1] - low_y))
			self.set_pixel(p0[0], p0[1], self._blendpixel(self.get_pixel(p0[0], p0[1]), pixel, o0))

		if (0 <= p1[0] < self.width) and (0 <= p1[1] < self.height):
			o1 = (abs(p0[0] - low_x)) * (1 - abs(p0[1] - low_y))
			self.set_pixel(p1[0], p1[1], self._blendpixel(self.get_pixel(p1[0], p1[1]), pixel, o1))

		if (0 <= p2[0] < self.width) and (0 <= p2[1] < self.height):
			o2 = (1 - abs(p0[0] - low_x)) * (abs(p0[1] - low_y))
			self.set_pixel(p2[0], p2[1], self._blendpixel(self.get_pixel(p2[0], p2[1]), pixel, o2))

		if (0 <= p3[0] < self.width) and (0 <= p3[1] < self.height):
			o3 = (abs(p0[0] - low_x)) * (abs(p0[1] - low_y))
			self.set_pixel(p3[0], p3[1], self._blendpixel(self.get_pixel(p3[0], p3[1]), pixel, o3))

	def write_file(self, filename):
		with open(filename, "wb") as f:
			save_format = self._SAVE_FORMAT[self.img_format]
			f.write(("%s\n" % (save_format)).encode("ascii"))
			f.write(b"# CREATOR: PnmPicture.py\n")
			f.write(("%d %d\n" % (self._width, self._height)).encode("ascii"))
			if self.img_format in [ PnmPictureFormat.Pixmap, PnmPictureFormat.Graymap ]:
				f.write(b"255\n")
			f.write(self._data)
		return self


#	def multiply(self, pixel):
#		(mr, mg, mb) = pixel
#		for y in range(self.height):
#			for x in range(self.width):
#				(r, g, b) = self.getpixel(x, y)
#				r = round((r * mr) / 255)
#				g = round((g * mg) / 255)
#				b = round((b * mb) / 255)
#				self.setpixel(x, y, (r, g, b))
#		return self
#
#	def downscale(self):
#		assert((self.width % 2) == 0)
#		assert((self.height % 2) == 0)
#		clone = PnmPicture().new(self.width // 2, self.height // 2)
#		for y in range(clone.height):
#			for x in range(clone.width):
#				pixel = self.getsubpicture(2 * x, 2 * y, 2, 2).avgcolor()
#				clone.setpixel(x, y, pixel)
#		return clone
#
#	def upscale(self, xmultiplicity = None, ymultiplicity = None):
#		assert((xmultiplicity is not None) or (ymultiplicity is not None))
#		if xmultiplicity is None:
#			xmultiplicity = 1
#		elif ymultiplicity is None:
#			ymultiplicity = 1
#		assert(isinstance(xmultiplicity, int))
#		assert(isinstance(ymultiplicity, int))
#		assert(xmultiplicity >= 1)
#		assert(ymultiplicity >= 1)
#		if (xmultiplicity == 1) and (ymultiplicity == 1):
#			return self
#		upscaled = PnmPicture().new(self.width * xmultiplicity, self.height * ymultiplicity)
#		for y in range(self.height):
#			for x in range(self.width):
#				pixel = self.getpixel(x, y)
#				for xoff in range(xmultiplicity):
#					for yoff in range(ymultiplicity):
#						upscaled.setpixel(xmultiplicity * x + xoff, ymultiplicity * y + yoff, pixel)
#		return upscaled
#
#	def getsubpicture(self, offsetx, offsety, width, height):
#		assert(offsetx + width <= self.width)
#		assert(offsety + height <= self.height)
#		subpic = PnmPicture().new(width, height)
#		subpic.blitsubpicture(-offsetx, -offsety, self)
#		return subpic
#
#	def blitsubpicture(self, offsetx, offsety, subpic):
#		#print("Blitting %s onto %s @ %d, %d" % (subpic, self, offsetx, offsety))
#		subdata = subpic._data
#
#		src_y_start = max(0, -offsety)
#		src_y_end = min(subpic.height, self.height - offsety)
#
#		src_x_start = max(0, -offsetx)
#		src_x_end = min(subpic.width, self.width - offsetx)
#		if src_x_start >= src_x_end:
#			# Complete X clipping, no blitting necessary
#			return
#
#		for yline in range(src_y_start, src_y_end):
#			src_o_start = subpic._getoffset(src_x_start, yline)
#			src_o_end = subpic._getoffset(src_x_end - 1, yline) + 3
#
#			dst_o_start = self._getoffset(src_x_start + offsetx, yline + offsety)
#			dst_o_end = self._getoffset(src_x_end + offsetx - 1, yline + offsety) + 3
#			self._data[dst_o_start : dst_o_end] = subpic._data[src_o_start : src_o_end]
#
#	def avgcolor(self):
#		(rsum, gsum, bsum) = (0, 0, 0)
#		for (r, g, b) in self:
#			rsum += r
#			gsum += g
#			bsum += b
#		r = round(rsum / self.pixelcnt)
#		g = round(gsum / self.pixelcnt)
#		b = round(bsum / self.pixelcnt)
#		return (r, g, b)
#
#
#
#	def blend(self, pixel, opacity):
#		for y in range(self.height):
#			for x in range(self.width):
#				self.setpixel(x, y, self._blendpixel(self.getpixel(x, y), pixel, opacity))
#		return self
#
#	def lighten(self, opacity, maxopacity = 1):
#		if opacity > maxopacity:
#			opacity = maxopacity
#		assert(0 <= opacity <= 1)
#		return self.blend((255, 255, 255), opacity)
#
#	def darken(self, opacity, maxopacity = 1):
#		if opacity > maxopacity:
#			opacity = maxopacity
#		assert(0 <= opacity <= 1)
#		return self.blend((0, 0, 0), opacity)
#
	def invert(self):
		self._data = bytearray((~x) & 0xff for x in self._data)
#
#	def setto(self, pixel):
#		self._data = bytearray([ pixel[0], pixel[1], pixel[2] ]) * self.pixelcnt
#
#	def rotate(self, degrees):
#		assert(isinstance(degrees, int))
#		degrees %= 360
#		if degrees == 90:
#			copy = PnmPicture().new(self.height, self.width)
#			for y in range(self.height):
#				for x in range(self.width):
#					pix = self.getpixel(x, y)
#					copy.setpixel(self.height - y - 1, x, pix)
#			(self._width, self._height) = (self._height, self._width)
#			self._data = copy._data
#		elif degrees == 270:
#			copy = PnmPicture().new(self.height, self.width)
#			for y in range(self.height):
#				for x in range(self.width):
#					pix = self.getpixel(x, y)
#					copy.setpixel(y, self._width - 1 - x, pix)
#			(self._width, self._height) = (self._height, self._width)
#			self._data = copy._data
#		elif degrees == 180:
#			copy = PnmPicture().new(self.height, self.width)
#			for y in range(self.height):
#				for x in range(self.width):
#					pix = self.getpixel(x, y)
#					copy.setpixel(self._width - 1 - x, self._height - 1 - y, pix)
#			self._data = copy._data
#		elif degrees == 0:
#			pass
#		else:
#			raise Exception("Only multiples of 90° are supported at the moment.")
#		return self
#
#	def applystencilpixel(self, x, y, stencil, source):
#		sumpx = [0, 0, 0]
#		for xoffset in range(stencil.width):
#			for yoffset in range(stencil.height):
#				picx = x + xoffset - stencil.xoffset
#				picy = y + yoffset - stencil.yoffset
#				if (0 <= picx < source.width) and (0 <= picy < source.height):
#					srcpix = source.getpixel(picx, picy)
#					weight = stencil[(xoffset, yoffset)]
#					sumpx[0] += weight * srcpix[0]
#					sumpx[1] += weight * srcpix[1]
#					sumpx[2] += weight * srcpix[2]
#		sumpx = [ round(element / stencil.weightsum) for element in sumpx ]
#		sumpx = [ 0 if (element < 0) else element for element in sumpx ]
#		sumpx = [ 255 if (element > 255) else element for element in sumpx ]
#		pixel = tuple(sumpx)
#		self.setpixel(x, y, pixel)
#		return self
#
#	def applystencil(self, stencil, source):
#		copy = self.clone()
#		for x in range(self.width):
#			for y in range(self.height):
#				self.applystencilpixel(x, y, stencil, copy)
#		return self
#
	def __eq__(self, other):
		return (self.width == other.width) and (self.height == other.height) and (self.img_format == other.img_format) and (self._data == other._data)

	def __hash__(self):
		return hash(self.data)

	def __str__(self):
		return "%sImg %d x %d (%d bytes)" % (self.img_format.name, self.width, self.height, len(self._data))


class FilterStencil(object):
	def __init__(self, width, height, coeffs):
		assert((width % 2) == 1)
		assert((height % 2) == 1)
		self._width = width
		self._height = height
		self._coeffs = coeffs
		self._sum = sum(coeff for coeff in coeffs if (coeff > 0))

	@property
	def width(self):
		return self._width

	@property
	def height(self):
		return self._height

	@property
	def xoffset(self):
		return self._width // 2

	@property
	def yoffset(self):
		return self._height // 2

	@property
	def weightsum(self):
		return self._sum

	def _gauss(x, sigma):
		return (1 / (math.sqrt(2 * math.pi) * sigma)) * math.exp(-(x ** 2) / (2 * sigma ** 2))

	def getgaussian(width):
		assert(width > 0)
		stencilwidth = (2 * width) + 1
		coeffs = [ ]
		for y in range(stencilwidth):
			for x in range(stencilwidth):
				dist = math.sqrt(((width - x) ** 2) + ((width - y) ** 2))
				gauss = FilterStencil._gauss(dist, width)
				coeffs.append(gauss)
		return FilterStencil(stencilwidth, stencilwidth, coeffs)

	def __getitem__(self, pos):
		(x, y) = pos
		return self._coeffs[x + (y * self.width)]

if __name__ == "__main__":
	import unittest

	class PnmPictureTest(unittest.TestCase):
		def test_new(self):
			img = PnmPicture.new(2, 2)
			self.assertEqual(img.data, bytes.fromhex("ffffff ffffff ffffff ffffff"))

		def test_set_get_pixel(self):
			img = PnmPicture.new(2, 2)
			img.set_pixel(0, 0, (0xab, 0xcd, 0xef))
			img.set_pixel(1, 1, (0x33, 0x44, 0x55))
			self.assertEqual(img.get_pixel(1, 1), (0x33, 0x44, 0x55))
			self.assertEqual(img.data, bytes.fromhex("abcdef ffffff ffffff 334455"))

		def test_set_pixel_uneven(self):
			img = PnmPicture.new(3, 3)
			img.set_pixel_antialiased(1.75, 0.9, (0xab, 0xcd, 0xef))
			self.assertEqual(img.data, bytes.fromhex("ffffff d9e8f8 f2f8fd ffffff e6f0fa f7fafd ffffff ffffff ffffff"))

	unittest.main()

#	pic = PnmPicture()
#	pic.readfile("test_rgb_bin.pnm")
#	pic.readfile("test_rgb_ascii.pnm")
	#pic.readfile("test_gray_bin.pnm")
#	pic.readfile("test_gray_ascii.pnm")
#	pic.readfile("stencil.pnm")
#	print(pic)
#	pic.setto((255, 4, 4))

#	big = PnmPicture().new(200, 200)
#	big.blitsubpicture(100, 100, pic)
#	big.writefile("out.pnm")

#	x = big.getsubpicture(100, 100, 25, 35)
#	x.writefile("out2.pnm")

#	print(pic)
#	print(pic.avgcolor())

#	import timeit
#	print(timeit.Timer("from PnmPicture import PnmPicture; PnmPicture().readfile('random.pnm')").repeat(repeat = 3, number = 100))

#	pic = PnmPicture().readfile("foo.pnm")
#	stencil = FilterStencil(3, 3, [
#		2, 0, 2,
#		0, 0, 0,
#		2, 0, 2
#	])
#	stencil = FilterStencil.getgaussian(4)
#	pic.applystencil(stencil, pic)
#	pic.writefile("bar.pnm")



#	for imgtype in [ 2, 3, 5, 6 ]:
#		infilename = "pnmtest_P%d.pnm" % (imgtype)
#		outfilename = "outtest_P%d.pnm" % (imgtype)
#		img = PnmPicture.read_file(infilename)
#		img.write_file(outfilename)
#		print(img)
