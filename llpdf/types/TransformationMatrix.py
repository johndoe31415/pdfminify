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


#> x := Matrix([[a,b,0],[c,d,0],[e,f,1]]);
#                                                                                   [a    b    0]
#                                                                                   [           ]
#                                                                              x := [c    d    0]
#                                                                                   [           ]
#                                                                                   [e    f    1]
#
#> y := Matrix([[a_,b_,0],[c_,d_,0],[e_,f_,1]]);
#                                                                                  [a_    b_    0]
#                                                                                  [             ]
#                                                                             y := [c_    d_    0]
#                                                                                  [             ]
#                                                                                  [e_    f_    1]
#
#> evalm(x&*y);
#                                                                 [  a a_ + b c_         a b_ + b d_       0]
#                                                                 [                                         ]
#                                                                 [  c a_ + d c_         c b_ + d d_       0]
#                                                                 [                                         ]
#                                                                 [e a_ + f c_ + e_    e b_ + f d_ + f_    1]

from llpdf.Measurements import Measurements

class NativeImageExtents(object):
	def __init__(self, x, y, width, height):
		self._x = x
		self._y = y
		self._width = width
		self._height = height

	@property
	def x(self):
		return self._x

	@property
	def y(self):
		return self._y

	@property
	def width(self):
		return self._width

	@property
	def height(self):
		return self._height

	def dpi(self, dots_width, dots_height):
		"""Calculates the resolution (in dpi, dots per inch) for a given pixel
		resolution."""
		dpi_x = dots_width / Measurements.convert(self.width, "native", "inch")
		dpi_y = dots_height / Measurements.convert(self.height, "native", "inch")
		return min(dpi_x, dpi_y)

	def format(self):
		return "at %s, %s extent %s x %s" % (Measurements.format(self.x, "native", suffix = False), Measurements.format(self.y, "native"), Measurements.format(self.width, "native", suffix = False), Measurements.format(self.height, "native"))

	def __str__(self):
		return "x, y, w, h = %.0f, %.0f, %.0f, %.0f" % (self.x, self.y, self.width, self.height)


class TransformationMatrix(object):
	def __init__(self, a, b, c, d, e, f):
		self._a = a
		self._b = b
		self._c = c
		self._d = d
		self._e = e
		self._f = f

	@property
	def a(self):
		return self._a

	@property
	def b(self):
		return self._b

	@property
	def c(self):
		return self._c

	@property
	def d(self):
		return self._d

	@property
	def e(self):
		return self._e

	@property
	def f(self):
		return self._f

	@property
	def aslist(self):
		return [ self.a, self.b, self.c, self.d, self.e, self.f ]

	def apply(self, x, y):
		return (
			self.a * x + self.c * y + self.e,
			self.b * x + self.d * y + self.f,
		)

	def extents(self, bounding_box):
		(x0, y0) = self.apply(bounding_box[0], bounding_box[1])
		(x1, y1) = self.apply(bounding_box[2], bounding_box[3])
		(width, height) = (abs(x1 - x0), abs(y1 - y0))
		(xoffset, yoffset) = (min(x0, x1), min(y0, y1))
		return NativeImageExtents(x = xoffset, y = yoffset, width = width, height = height)

	def __eq__(self, other):
		abs_diff_sum = sum(abs(x - y) for (x, y) in zip(self.aslist, other.aslist))
		return abs_diff_sum < 1e-6

	def __imul__(self, other):
		return TransformationMatrix(
			self.a * other.a + self.b * other.c,
			self.a * other.b + self.b * other.d,
			self.c * other.a + self.d * other.c,
			self.c * other.b + self.d * other.d,
			self.e * other.a + self.f * other.c + other.e,
			self.e * other.b + self.f * other.d + other.f,
		)

	@property
	def is_identity(self):
		return self == self.identity()

	@classmethod
	def scale(cls, scale_factor):
		return cls(scale_factor, 0, 0, scale_factor, 0, 0)

	@classmethod
	def identity(cls):
		return cls.scale(1)

	def __repr__(self):
		return str(self)

	@staticmethod
	def _float_format(value):
		value = "%.3f" % (value)
		if value.endswith(".000"):
			value = value[:-4]
		return value

	def __str__(self):
		if self.is_identity:
			values = "identity"
		else:
			values = (self.a, self.b, self.c, self.d, self.e, self.f)
			values = ", ".join(self._float_format(value) for value in values)
		return "Matrix<%s>" % (values)
