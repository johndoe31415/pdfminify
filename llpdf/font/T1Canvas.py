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

from llpdf.img.PnmPicture import PnmPicture

class NaiveDebuggingCanvas(object):
	_STEP_COUNT = 100
	_SCALE_FACTOR = 7

	_OFFSET_X = 750
	_OFFSET_Y = 750
	_WIDTH = 2000
	_HEIGHT = 2000

	def __init__(self):
		self._image = PnmPicture.new(round(self._WIDTH / self._SCALE_FACTOR), round(self._HEIGHT / self._SCALE_FACTOR))

	@property
	def image(self):
		return self._image

	def _t_range(self):
		yield from (x / (self._STEP_COUNT - 1) for x in range(self._STEP_COUNT))

	def _emit(self, x, y):
		x = (x + self._OFFSET_X) / self._SCALE_FACTOR
		y = (y + self._OFFSET_Y) / self._SCALE_FACTOR
		y = self._image.height - 1 - y
		self._image.set_pixel_antialiased(x, y, (0, 0, 0))

	@staticmethod
	def _cubic_bezier(t, pt1, pt2, pt3, pt4):
		t2 = t ** 2
		t3 = t ** 3
		mt = 1 - t
		mt2 = mt ** 2
		mt3 = mt ** 3
		x = (pt1[0] * mt3) + (3 * pt2[0] * mt2 * t) + (3 * pt3[0] * mt * t2) + (pt4[0] * t3)
		y = (pt1[1] * mt3) + (3 * pt2[1] * mt2 * t) + (3 * pt3[1] * mt * t2) + (pt4[1] * t3)
		return (x, y)

	def bezier(self, pt1, pt2, pt3, pt4):
#		print("BEZIER", pt1, pt2, pt3, pt4)
		for t in self._t_range():
			(x, y) = self._cubic_bezier(t, pt1, pt2, pt3, pt4)
			self._emit(x, y)

	def line(self, pt1, pt2):
#		print("LINE", pt1, pt2)
		for t in self._t_range():
			mt = 1 - t
			x = (pt1[0] * t) + (pt2[0] * mt)
			y = (pt1[1] * t) + (pt2[1] * mt)
			self._emit(x, y)
