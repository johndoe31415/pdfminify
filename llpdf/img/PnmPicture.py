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

# Coordinates: 0, 0 is upper left corner
class PnmPicture(object):
	def __init__(self):
		self._data = None
		self._width = None
		self._height = None

	def new(self, width, height):
		assert(isinstance(width, int))
		assert(isinstance(height, int))
		self._width = width
		self._height = height
		self._data = bytearray(self.pixelcnt * 3)
		return self

	def clone(self):
		clone = PnmPicture().new(self.width, self.height)
		clone._data = bytearray(self._data)
		return clone

	@property
	def data(self):
		if self._data is None:
			raise Exception("No image loaded.")
		return bytes(self._data)

	@property
	def width(self):
		if self._width is None:
			raise Exception("No image loaded.")
		return self._width

	@property
	def height(self):
		if self._height is None:
			raise Exception("No image loaded.")
		return self._height

	@property
	def pixelcnt(self):
		return self.width * self.height

	@classmethod
	def fromdata(cls, width, height, data):
		assert(width * height * 3 == len(data))
		img = cls()
		img._width = width
		img._height = height
		img._data = bytearray(data)
		return img

	def readfile(self, filename):
		f = open(filename, "rb")
		metadata = { }
		lines = [ ]
		while True:
			line = f.readline().decode("utf-8")[:-1]
			if line.startswith("#"):
				continue
			lines.append(line)
			if len(lines) == 3:
				break

		metadata["format"] = lines[0]
		metadata["geometry"] = lines[1]
		metadata["bpp"] = int(lines[2])

		(self._width, self._height) = [ int(s) for s in metadata["geometry"].split()]
		# P2 = Grayscale ASCII
		# P3 = RGB ASCII
		# P5 = Grayscale binary
		# P6 = RGB binary
		assert(metadata["format"] in [ "P2", "P3", "P5", "P6" ])
		assert(metadata["bpp"] == 255)

		fmt_binary = metadata["format"] in [ "P5", "P6" ]
		rgb = metadata["format"] in [ "P3", "P6" ]
		if rgb:
			# RGB
			if fmt_binary:
				self._data = bytearray(f.read())
			else:
				self._data = bytearray(self.pixelcnt * 3)
				for i in range(self.pixelcnt * 3):
					self._data[i] = int(f.readline())
		else:
			# Grayscale
			if fmt_binary:
				self._data = bytearray().join(bytes([c, c, c]) for c in f.read())
			else:
				self._data = bytearray()
				for i in range(self.pixelcnt):
					c = int(f.readline())
					self._data += bytes([ c, c, c ])
		f.close()
		assert(self.pixelcnt * 3 == len(self._data))
		return self

	def _getoffset(self, x, y):
		assert(0 <= x < self.width)
		assert(0 <= y < self.height)
		offset = 3 * ((y * self.width) + x)
		return offset

	def multiply(self, pixel):
		(mr, mg, mb) = pixel
		for y in range(self.height):
			for x in range(self.width):
				(r, g, b) = self.getpixel(x, y)
				r = round((r * mr) / 255)
				g = round((g * mg) / 255)
				b = round((b * mb) / 255)
				self.setpixel(x, y, (r, g, b))
		return self

	def downscale(self):
		assert((self.width % 2) == 0)
		assert((self.height % 2) == 0)
		clone = PnmPicture().new(self.width // 2, self.height // 2)
		for y in range(clone.height):
			for x in range(clone.width):
				pixel = self.getsubpicture(2 * x, 2 * y, 2, 2).avgcolor()
				clone.setpixel(x, y, pixel)
		return clone

	def upscale(self, xmultiplicity = None, ymultiplicity = None):
		assert((xmultiplicity is not None) or (ymultiplicity is not None))
		if xmultiplicity is None:
			xmultiplicity = 1
		elif ymultiplicity is None:
			ymultiplicity = 1
		assert(isinstance(xmultiplicity, int))
		assert(isinstance(ymultiplicity, int))
		assert(xmultiplicity >= 1)
		assert(ymultiplicity >= 1)
		if (xmultiplicity == 1) and (ymultiplicity == 1):
			return self
		upscaled = PnmPicture().new(self.width * xmultiplicity, self.height * ymultiplicity)
		for y in range(self.height):
			for x in range(self.width):
				pixel = self.getpixel(x, y)
				for xoff in range(xmultiplicity):
					for yoff in range(ymultiplicity):
						upscaled.setpixel(xmultiplicity * x + xoff, ymultiplicity * y + yoff, pixel)
		return upscaled

	def getpixel(self, x, y):
		offset = self._getoffset(x, y)
		(r, g, b) = (self._data[offset + 0], self._data[offset + 1], self._data[offset + 2])
		return (r, g, b)

	def setpixel(self, x, y, pixel):
		offset = self._getoffset(x, y)
		(r, g, b) = pixel
		self._data[offset + 0] = r
		self._data[offset + 1] = g
		self._data[offset + 2] = b
		return self

	def writefile(self, filename, channel = None):
		if channel is not None:
			# grayscale picture
			stride = 3
			offset = channel % 3
		else:
			stride = 1
			offset = 0
		f = open(filename, "wb")
		if channel is None:
			f.write("P6\n".encode("utf-8"))
		else:
			f.write("P5\n".encode("utf-8"))
		f.write("# CREATOR: PnmPicture.py\n".encode("utf-8"))
		f.write(("%d %d\n" % (self._width, self._height)).encode("utf-8"))
		f.write("255\n".encode("utf-8"))
		f.write(self._data[offset :: stride])
		f.close()
		return self

	def getsubpicture(self, offsetx, offsety, width, height):
		assert(offsetx + width <= self.width)
		assert(offsety + height <= self.height)
		subpic = PnmPicture().new(width, height)
		subpic.blitsubpicture(-offsetx, -offsety, self)
		return subpic

	def blitsubpicture(self, offsetx, offsety, subpic):
		#print("Blitting %s onto %s @ %d, %d" % (subpic, self, offsetx, offsety))
		subdata = subpic._data

		src_y_start = max(0, -offsety)
		src_y_end = min(subpic.height, self.height - offsety)

		src_x_start = max(0, -offsetx)
		src_x_end = min(subpic.width, self.width - offsetx)
		if src_x_start >= src_x_end:
			# Complete X clipping, no blitting necessary
			return

		for yline in range(src_y_start, src_y_end):
			src_o_start = subpic._getoffset(src_x_start, yline)
			src_o_end = subpic._getoffset(src_x_end - 1, yline) + 3

			dst_o_start = self._getoffset(src_x_start + offsetx, yline + offsety)
			dst_o_end = self._getoffset(src_x_end + offsetx - 1, yline + offsety) + 3
			self._data[dst_o_start : dst_o_end] = subpic._data[src_o_start : src_o_end]

	def avgcolor(self):
		(rsum, gsum, bsum) = (0, 0, 0)
		for (r, g, b) in self:
			rsum += r
			gsum += g
			bsum += b
		r = round(rsum / self.pixelcnt)
		g = round(gsum / self.pixelcnt)
		b = round(bsum / self.pixelcnt)
		return (r, g, b)

	@staticmethod
	def _blendpixel(pixel1, pixel2, opacity):
		(r1, g1, b1) = pixel1
		(r2, g2, b2) = pixel2
		return (round((r1 * (1 - opacity)) + (r2 * opacity)),
					round((g1 * (1 - opacity)) + (g2 * opacity)),
					round((b1 * (1 - opacity)) + (b2 * opacity)))


	def blend(self, pixel, opacity):
		for y in range(self.height):
			for x in range(self.width):
				self.setpixel(x, y, self._blendpixel(self.getpixel(x, y), pixel, opacity))
		return self

	def lighten(self, opacity, maxopacity = 1):
		if opacity > maxopacity:
			opacity = maxopacity
		assert(0 <= opacity <= 1)
		return self.blend((255, 255, 255), opacity)

	def darken(self, opacity, maxopacity = 1):
		if opacity > maxopacity:
			opacity = maxopacity
		assert(0 <= opacity <= 1)
		return self.blend((0, 0, 0), opacity)

	def invert(self):
		for i in range(len(self._data)):
			self._data[i] = 255 - self._data[i]
		return self

	def setto(self, pixel):
		self._data = bytearray([ pixel[0], pixel[1], pixel[2] ]) * self.pixelcnt

	def rotate(self, degrees):
		assert(isinstance(degrees, int))
		degrees %= 360
		if degrees == 90:
			copy = PnmPicture().new(self.height, self.width)
			for y in range(self.height):
				for x in range(self.width):
					pix = self.getpixel(x, y)
					copy.setpixel(self.height - y - 1, x, pix)
			(self._width, self._height) = (self._height, self._width)
			self._data = copy._data
		elif degrees == 270:
			copy = PnmPicture().new(self.height, self.width)
			for y in range(self.height):
				for x in range(self.width):
					pix = self.getpixel(x, y)
					copy.setpixel(y, self._width - 1 - x, pix)
			(self._width, self._height) = (self._height, self._width)
			self._data = copy._data
		elif degrees == 180:
			copy = PnmPicture().new(self.height, self.width)
			for y in range(self.height):
				for x in range(self.width):
					pix = self.getpixel(x, y)
					copy.setpixel(self._width - 1 - x, self._height - 1 - y, pix)
			self._data = copy._data
		elif degrees == 0:
			pass
		else:
			raise Exception("Only multiples of 90° are supported at the moment.")
		return self

	def applystencilpixel(self, x, y, stencil, source):
		sumpx = [0, 0, 0]
		for xoffset in range(stencil.width):
			for yoffset in range(stencil.height):
				picx = x + xoffset - stencil.xoffset
				picy = y + yoffset - stencil.yoffset
				if (0 <= picx < source.width) and (0 <= picy < source.height):
					srcpix = source.getpixel(picx, picy)
					weight = stencil[(xoffset, yoffset)]
					sumpx[0] += weight * srcpix[0]
					sumpx[1] += weight * srcpix[1]
					sumpx[2] += weight * srcpix[2]
		sumpx = [ round(element / stencil.weightsum) for element in sumpx ]
		sumpx = [ 0 if (element < 0) else element for element in sumpx ]
		sumpx = [ 255 if (element > 255) else element for element in sumpx ]
		pixel = tuple(sumpx)
		self.setpixel(x, y, pixel)
		return self

	def applystencil(self, stencil, source):
		copy = self.clone()
		for x in range(self.width):
			for y in range(self.height):
				self.applystencilpixel(x, y, stencil, copy)
		return self

	def __eq__(self, other):
		return (self.width == other.width) and (self.height == other.height) and (self._data == other._data)

	def __hash__(self):
		return hash(self.data)

	def __iter__(self):
		for i in range(0, len(self._data), 3):
			yield (self._data[i + 0], self._data[i + 1], self._data[i + 2])

	def __str__(self):
		if self._data is None:
			return "No picture data loaded"
		else:
			return "%d x %d (%d bytes)" % (self._width, self._height, len(self._data))


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

	pic = PnmPicture().readfile("foo.pnm")
	stencil = FilterStencil(3, 3, [
		2, 0, 2,
		0, 0, 0,
		2, 0, 2
	])
#	stencil = FilterStencil.getgaussian(4)
	pic.applystencil(stencil, pic)
	pic.writefile("bar.pnm")



