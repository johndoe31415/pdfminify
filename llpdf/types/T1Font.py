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

import re
import enum
import struct
import logging
from llpdf.FileRepr import StreamRepr
from llpdf.types.PDFName import PDFName
from llpdf.types.PDFObject import PDFObject
from llpdf.EncodeDecode import EncodedObject
from llpdf.img.PnmPicture import PnmPicture

class _T1PRNG(object):
	_C1 = 52845
	_C2 = 22719

	def __init__(self, r):
		self._r = r & 0xffff

	def decrypt_byte(self, cipher):
		plain = (cipher ^ (self._r >> 8)) & 0xff
		self._r = (((cipher + self._r) & 0xffff) * self._C1 + self._C2) & 0xffff
		return plain

	def decrypt_bytes(self, data):
		return bytes(self.decrypt_byte(cipher) for cipher in data)[4:]

class PostScriptStandardCharacterName(enum.IntEnum):
	controlSTX = 1
	controlSOT = 2
	controlETX = 3
	controlEOT = 4
	controlENQ = 5
	controlACK = 6
	controlBEL = 7
	controlBS = 8
	controlHT = 9
	controlLF = 10
	controlVT = 11
	controlFF = 12
	controlCR = 13
	controlSO = 14
	controlSI = 15
	controlDLE = 16
	controlDC1 = 17
	controlDC2 = 18
	controlDC3 = 19
	controlDC4 = 20
	controlNAK = 21
	controlSYN = 22
	controlETB = 23
	controlCAN = 24
	controlEM = 25
	controlSUB = 26
	controlESC = 27
	controlFS = 28
	controlGS = 29
	controlRS = 30
	controlUS = 31
	space = 32
	exclam = 33
	quotedbl = 34
	numbersign = 35
	dollar = 36
	percent = 37
	ampersand = 38
	quotesingle = 39
	parenleft = 40
	parenright = 41
	asterisk = 42
	plus = 43
	comma = 44
	hyphen = 45
	period = 46
	slash = 47
	zero = 48
	one = 49
	two = 50
	three = 51
	four = 52
	five = 53
	six = 54
	seven = 55
	eight = 56
	nine = 57
	colon = 58
	semicolon = 59
	less = 60
	equal = 61
	greater = 62
	question = 63
	at = 64
	A = 65
	B = 66
	C = 67
	D = 68
	E = 69
	F = 70
	G = 71
	H = 72
	I = 73
	J = 74
	K = 75
	L = 76
	M = 77
	N = 78
	O = 79
	P = 80
	Q = 81
	R = 82
	S = 83
	T = 84
	U = 85
	V = 86
	W = 87
	X = 88
	Y = 89
	Z = 90
	bracketleft = 91
	backslash = 92
	bracketright = 93
	asciicircum = 94
	underscore = 95
	grave = 96
	a = 97
	b = 98
	c = 99
	d = 100
	e = 101
	f = 102
	g = 103
	h = 104
	i = 105
	j = 106
	k = 107
	l = 108
	m = 109
	n = 110
	o = 111
	p = 112
	q = 113
	r = 114
	s = 115
	t = 116
	u = 117
	v = 118
	w = 119
	x = 120
	y = 121
	z = 122
	braceleft = 123
	bar = 124
	braceright = 125
	asciitilde = 126
	controlDEL = 127
	nbspace = 160
	exclamdown = 161
	cent = 162
	sterling = 163
	currency = 164
	yen = 165
	brokenbar = 166
	section = 167
	dieresis = 168
	copyright = 169
	ordfeminine = 170
	guillemotleft = 171
	logicalnot = 172
	sfthyphen = 173
	registered = 174
	macron = 175
	degree = 176
	plusminus = 177
	twosuperior = 178
	threesuperior = 179
	acute = 180
	mu = 181
	paragraph = 182
	middot = 183
	cedilla = 184
	onesuperior = 185
	ordmasculine = 186
	guillemotright = 187
	onequarter = 188
	onehalf = 189
	threequarters = 190
	questiondown = 191
	Agrave = 192
	Aacute = 193
	Acircumflex = 194
	Atilde = 195
	Adieresis = 196
	Aring = 197
	AE = 198
	Ccedilla = 199
	Egrave = 200
	Eacute = 201
	Ecircumflex = 202
	Edieresis = 203
	Igrave = 204
	Iacute = 205
	Icircumflex = 206
	Idieresis = 207
	Eth = 208
	Ntilde = 209
	Ograve = 210
	Oacute = 211
	Ocircumflex = 212
	Otilde = 213
	Odieresis = 214
	multiply = 215
	Oslash = 216
	Ugrave = 217
	Uacute = 218
	Ucircumflex = 219
	Udieresis = 220
	Yacute = 221
	Thorn = 222
	germandbls = 223
	agrave = 224
	aacute = 225
	acircumflex = 226
	atilde = 227
	adieresis = 228
	aring = 229
	ae = 230
	ccedilla = 231
	egrave = 232
	eacute = 233
	ecircumflex = 234
	edieresis = 235
	igrave = 236
	iacute = 237
	icircumflex = 238
	idieresis = 239
	eth = 240
	ntilde = 241
	ograve = 242
	oacute = 243
	ocircumflex = 244
	otilde = 245
	odieresis = 246
	divide = 247
	oslash = 248
	ugrave = 249
	uacute = 250
	ucircumflex = 251
	udieresis = 252
	yacute = 253
	thorn = 254
	ydieresis = 255

class T1CommandCode(enum.IntEnum):
	hstem = 1
	vstem = 3
	vmoveto = 4
	rlineto = 5
	hlineto = 6
	vlineto = 7
	rrcurveto = 8
	closepath = 9
	callsubr = 10
	retrn = 11
	escape = 12
	hsbw = 13
	endchar = 14
	rmoveto = 21
	hmoveto = 22
	vhcurveto = 30
	hvcurveto = 31

	dotsection = (escape << 8) | 0
	vstem3 = (escape << 8) | 1
	hstem3 = (escape << 8) | 2
	seac = (escape << 8) | 6
	sbw = (escape << 8) | 7
	div = (escape << 8) | 12
	callothersubr = (escape << 8) | 16
	pop = (escape << 8) | 17
	setcurrentpoint = (escape << 8) | 33

class T1Command(object):
	def __init__(self, cmdcode, *args):
		self._cmdcode = cmdcode
		self._args = args

	@property
	def cmdcode(self):
		return self._cmdcode

	def __getitem__(self, index):
		return self._args[index]

	def __iter__(self):
		return iter(self._args)

	def __repr__(self):
		return str(self)

	def __str__(self):
		if len(self._args) == 0:
			return str(self._cmdcode.name)
		else:
			return "%s(%s)" % (self._cmdcode.name, ", ".join(str(arg) for arg in self._args))

class NaiveDebuggingCanvas(object):
	_STEP_COUNT = 100
	_SCALE_FACTOR = 7
	_OFFSET_X = round(1000 / _SCALE_FACTOR)
	_OFFSET_Y = round(1000 / _SCALE_FACTOR)
	_WIDTH = round(2.5 * _OFFSET_X)
	_HEIGHT = round(2.5 * _OFFSET_Y)

	def __init__(self):
		self._image = PnmPicture.new(self._WIDTH, self._HEIGHT)

	@property
	def image(self):
		return self._image

	def _t_range(self):
		yield from (x / (self._STEP_COUNT - 1) for x in range(self._STEP_COUNT))

	def _emit(self, x, y):
		(x, y) = (round(x), round(y))
		x = round((x / self._SCALE_FACTOR) + self._OFFSET_X)
		y = self._HEIGHT - 1 - (round((y / self._SCALE_FACTOR) + self._OFFSET_Y))
		self._image.set_pixel(x, y, (0, 0, 0))

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


class T1Interpreter(object):
	_log = logging.getLogger("llpdf.types.T1Font.T1Interpreter")

	def __init__(self, canvas = None, parent_font = None):
		self._canvas = canvas
		self._parent_font = parent_font
		self._width = [ ]
		self._left_sidebearing = [ 0, 0 ]
		self._pos = [ 0, 0 ]
		self._path = [ ]

	def _run_command(self, cmd):
		if cmd.cmdcode == T1CommandCode.hsbw:
			# Horizontal sidebearing and width
			self._left_sidebearing = [ cmd[0], 0 ]
			self._width = [ cmd[1], 0 ]
			self._pos = [ cmd[0], 0 ]
		elif cmd.cmdcode == T1CommandCode.sbw:
			# Sidebearing and width
			self._left_sidebearing = [ cmd[0], cmd[1] ]
			self._width = [ cmd[2], cmd[3] ]
			self._pos = [ cmd[0], cmd[1] ]
		elif cmd.cmdcode in [ T1CommandCode.rmoveto, T1CommandCode.rlineto ]:
			newpos = [ self._pos[0] + cmd[0], self._pos[1] + cmd[1] ]
			if cmd.cmdcode == T1CommandCode.rlineto:
				if self._canvas is not None:
					self._canvas.line(self._pos, newpos)
			self._pos = newpos
			self._path.append(self._pos)
		elif cmd.cmdcode == T1CommandCode.rrcurveto:
			pt1 = [ self._pos[0] + cmd[0], self._pos[1] + cmd[1] ]
			pt2 = [ pt1[0] + cmd[2], pt1[1] + cmd[3] ]
			pt3 = [ pt2[0] + cmd[4], pt2[1] + cmd[5] ]
			if self._canvas is not None:
				self._canvas.bezier(self._pos, pt1, pt2, pt3)
			self._pos = pt3
			self._path.append(self._pos)
		elif cmd.cmdcode == T1CommandCode.hmoveto:
			self._run_command(T1Command(T1CommandCode.rmoveto, cmd[0], 0))
		elif cmd.cmdcode == T1CommandCode.vmoveto:
			self._run_command(T1Command(T1CommandCode.rmoveto, 0, cmd[0]))
		elif cmd.cmdcode == T1CommandCode.hlineto:
			self._run_command(T1Command(T1CommandCode.rlineto, cmd[0], 0))
		elif cmd.cmdcode == T1CommandCode.vlineto:
			self._run_command(T1Command(T1CommandCode.rlineto, 0, cmd[0]))
		elif cmd.cmdcode == T1CommandCode.hvcurveto:
			self._run_command(T1Command(T1CommandCode.rrcurveto, cmd[0], 0, cmd[1], cmd[2], 0, cmd[3]))
		elif cmd.cmdcode == T1CommandCode.vhcurveto:
			self._run_command(T1Command(T1CommandCode.rrcurveto, 0, cmd[0], cmd[1], cmd[2], cmd[3], 0))
		elif cmd.cmdcode == T1CommandCode.callsubr:
			if self._parent_font is None:
				self._log.error("Unable to call subroutine %s without parent.", cmd)
			else:
				subr = self._parent_font.get_subroutine(cmd[0])
				if subr is None:
					self._log.error("T1 font code referenced subroutine %s, but no such subroutine known. Ignoring.", cmd)
				else:
					self.run(subr.parse())
		elif cmd.cmdcode in [ T1CommandCode.vstem, T1CommandCode.hstem, T1CommandCode.vstem3, T1CommandCode.hstem3, T1CommandCode.dotsection ]:
			# Hint commands, ignore
			pass
		elif cmd.cmdcode == T1CommandCode.seac:
			accent_sidebearing = cmd[0]
			(accent_x, accent_y) = (cmd[1], cmd[2])
			(base_char_code, accented_char_code) = (cmd[3], cmd[4])
			base_char = PostScriptStandardCharacterName(base_char_code)
			accented_char = PostScriptStandardCharacterName(accented_char_code - 1)		# going on a limb
			print((base_char, accented_char))
			if self._parent_font is None:
				self._log.error("Unable to set accent %s without parent.", cmd)
			else:
				accent_name = "/" + accented_char.name[len(base_char.name):]
				print("Building", accented_char, "from", base_char, "with", accent_name)
				base_glyph = self._parent_font.charset["/" + base_char.name]
				accent_glyph = self._parent_font.charset[accent_name]

				self.run(base_glyph.parse())
				self._pos = [ accent_x, accent_y ]
				self.run(accent_glyph.parse())
		elif cmd.cmdcode == T1CommandCode.closepath:
			if self._canvas is not None:
				self._canvas.line(self._pos, self._path[0])
			self._path = [ ]
		elif cmd.cmdcode in [ T1CommandCode.endchar, T1CommandCode.retrn, T1CommandCode.div ]:
			return
		else:
			raise Exception(NotImplemented, cmd)

	def run(self, commands):
		for command in commands:
			self._run_command(command)

class T1Glyph(object):
	def __init__(self, glyph_data):
		self._data = glyph_data

	def parse(self):
		stack = [ ]
		commands = [ ]
		index = 0
		#print(self._data.hex())
		while index < len(self._data):
			v = self._data[index]
			#print("Next %02x at %d" % (v, index))
			if 0 <= v < 32:
				# Command!
				if v == T1CommandCode.escape:
					w = self._data[index + 1]
					index += 1
					v = (v << 8) | w
				cmdcode = T1CommandCode(v)
				commands.append(T1Command(cmdcode, *stack))
				stack = [ ]
			elif 32 <= v <= 246:
				stack.append(v - 139)
			elif 247 <= v <= 250:
				w = self._data[index + 1]
				index += 1
				stack.append(((v - 247) * 256) + w + 108)
			elif 251 <= v <= 254:
				w = self._data[index + 1]
				index += 1
				stack.append(-(((v - 251) * 256) + w + 108))
			elif v == 255:
				value = self._data[index + 1 : index + 5]
				value = int.from_bytes(value, byteorder = "big", signed = True)
				stack.append(value)
				index += 4
			index += 1
		return commands

	def interpret(self, canvas = None, parent_font = None):
		interpreter = T1Interpreter(canvas = canvas, parent_font = parent_font)
		interpreter.run(self.parse())
		return interpreter

	@property
	def data(self):
		return self._data

	def __repr__(self):
		return str(self)

	def __str__(self):
		return "Glyph<%d bytes>" % (len(self._data))

class T1Font(object):
	_T1_FONT_KEY = 55665
	_T1_GLYPH_KEY = 4330
	_PFB_HEADER = struct.Struct("< H L")
	_FONT_BBOX_RE = re.compile(r"/FontBBox\s*{(?P<v1>-?\d+)\s+(?P<v2>-?\d+)\s+(?P<v3>-?\d+)\s+(?P<v4>-?\d+)\s*}")

	def __init__(self, cleardata, cipherdata, trailerdata):
		self._cleardata = cleardata
		self._cipherdata = cipherdata
		self._trailerdata = trailerdata
		self._charset = None
		self._subroutines = None
		self._numeric_glyph_map = { }

	def _decrypt_cipherdata(self):
		decrypted_data = _T1PRNG(self._T1_FONT_KEY).decrypt_bytes(self._cipherdata)
		return decrypted_data

	@property
	def charset(self):
		if self._charset is None:
			self._parse_font()
		return self._charset

	@property
	def charset_string(self):
		return "".join(sorted(self.charset.keys())).encode("ascii")

	@classmethod
	def _parse_glyphs(cls, data):
		glyphs = { }
		numeric_glyph_map = { }
		strm = StreamRepr(data[data.index(b"/CharStrings") : ])
		header = strm.read_n_tokens(5)
		glyph_count = int(header[1].decode("ascii"))
		for i in range(glyph_count):
			definition = strm.read_n_tokens(3)
			name = definition[0].decode("ascii")
			length = int(definition[1].decode("ascii"))
			encoded_glyph_data = strm.read(length)
			decoded_glyph_data = _T1PRNG(cls._T1_GLYPH_KEY).decrypt_bytes(encoded_glyph_data)
			glyph = T1Glyph(decoded_glyph_data)
			strm.read_next_token()
			if name != "/.notdef":
				glyphs[name] = glyph
				numeric_glyph_map[i] = name
		return (glyphs, numeric_glyph_map)

	@classmethod
	def _parse_subroutines(cls, data):
		subroutines = { }
		strm = StreamRepr(data[data.index(b"/Subrs") : ])
		header = strm.read_n_tokens(3)
		subroutine_count = int(header[1].decode("ascii"))
		for i in range(subroutine_count):
			(dup, subroutine_id, subroutine_length, start_subr_marker) = strm.read_n_tokens(4)
			subroutine_id = int(subroutine_id)
			subroutine_length = int(subroutine_length)
			encoded_subroutine_data = strm.read(subroutine_length)
			decoded_subroutine_data = _T1PRNG(cls._T1_GLYPH_KEY).decrypt_bytes(encoded_subroutine_data)
			subroutines[subroutine_id] = T1Glyph(decoded_subroutine_data)
			end_subr_marker = strm.read_next_token()
		return subroutines

	def get_subroutine(self, subroutine_id):
		return self._subroutines.get(subroutine_id)

	def get_glyph(self, numeric_glyph_id):
		char = PostScriptStandardCharacterName(numeric_glyph_id)
		name = "/" + char.name
		return self.charset[name]

	def get_font_bbox(self):
		cleartext = self._cleardata.decode("ascii")
		result = self._FONT_BBOX_RE.search(cleartext)
		if result is None:
			raise Exception("/FontBBox not found in clear text data of T1 font.")
		result = result.groupdict()
		return [ int(result["v1"]), int(result["v2"]), int(result["v3"]), int(result["v4"]) ]

	def _parse_font(self):
		decrypted_data = self._decrypt_cipherdata()
		(self._charset, self._numeric_glyph_map) = self._parse_glyphs(decrypted_data)
		self._subroutines = self._parse_subroutines(decrypted_data)

	@classmethod
	def from_fontfile_obj(cls, fontfile_object):
		length1 = fontfile_object.content[PDFName("/Length1")]
		length2 = fontfile_object.content[PDFName("/Length2")]
		length3 = fontfile_object.content[PDFName("/Length3")]
		data = fontfile_object.stream.decode()

		cleardata = data[ : length1]
		cipherdata = data[length1 : length1 + length2]
		trailerdata = data[length1 + length2 : ]
		return cls(cleardata, cipherdata, trailerdata)

	@classmethod
	def from_pfb_file(cls, filename):
		with open(filename, "rb") as f:
			data = [ ]
			for expect_magic in [ 0x180, 0x280, 0x180]:
				(magic, length) = cls._PFB_HEADER.unpack(f.read(6))
				assert(magic == expect_magic)
				data.append(f.read(length))
			(cleardata, cipherdata, trailerdata) = data
		return cls(cleardata, cipherdata, trailerdata)

	def to_fontfile_obj(self, objid):
		content = {
			PDFName("/Length1"):	len(self._cleardata),
			PDFName("/Length2"):	len(self._cipherdata),
			PDFName("/Length3"):	len(self._trailerdata),
		}
		stream = EncodedObject.create(self._cleardata + self._cipherdata + self._trailerdata, compress = True)
		obj = PDFObject.create(objid, 0, content, stream)
		return obj

	def dump(self, filename_prefix):
		with open(filename_prefix + "1", "wb") as f:
			f.write(self._cleardata)
		with open(filename_prefix + "2", "wb") as f:
			f.write(self._decrypt_cipherdata())
		with open(filename_prefix + "3", "wb") as f:
			f.write(self._trailerdata)

	def __str__(self):
		return "T1Font<%d, %d, %d>" % (len(self._cleardata), len(self._cipherdata), 0)

if __name__ == "__main__":
#	with open("ff1", "rb") as f1,  open("ff2", "rb") as f2:
#		f1 = f1.read()
#		f2 = f2.read()
#	t1 = T1Font(f1, f2, b"")
#	print(t1)
#	print("".join(t1.get_charstrings()))
#	print(len(list(t1.get_charstrings())))
#	t1 = T1Font.from_pfb_file("/usr/share/texlive/texmf-dist/fonts/type1/public/bera/fver8a.pfb")
	t1 = T1Font.from_pfb_file("/usr/share/texlive/texmf-dist/fonts/type1/adobe/courier/pcrb8a.pfb")
	t1.dump("font_dump")
	print(t1.charset_string)


#	charname = "/Aacute"
	charname = "/Adieresis"
	for glyph in [ t1.charset[charname] ]:
#	for (charname, glyph) in sorted(t1.charset.items()):
		print(charname)
		canvas = NaiveDebuggingCanvas()
		commands = glyph.interpret(canvas = canvas, parent_font = t1)
		canvas.image.write_file("chars/" + charname[1:] + ".pnm")

	#for (name, glyph) in sorted(t1.charset.items()):
	#	print(name)
	#	print(glyph.parse())
	#	print()
	#	print()
	#	print()

