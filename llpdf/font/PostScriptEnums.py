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
from llpdf.types.PDFName import PDFName

class PostScriptStandardCharacterName(enum.IntEnum):
	space = 32
	exclam = 33
	quotedbl = 34
	numbersign = 35
	dollar = 36
	percent = 37
	ampersand = 38
	quoteright = 39
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
	quoteleft = 96
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
	exclamdown = 161
	cent = 162
	sterling = 163
	fraction = 164
	yen = 165
	florin = 166
	section = 167
	currency = 168
	quotesingle = 169
	quotedblleft = 170
	guillemotleft = 171
	guilsinglleft = 172
	guilsinglright = 173
	fi = 174
	fl = 175
	endash = 177
	dagger = 178
	daggerdbl = 179
	periodcentered = 180
	paragraph = 182
	bullet = 183
	quotesinglbase = 184
	quotedblbase = 185
	quotedblright = 186
	guillemotright = 187
	ellipsis = 188
	perthousand = 189
	questiondown = 191
	grave = 193
	acute = 194
	circumflex = 195
	tilde = 196
	macron = 197
	breve = 198
	dotaccent = 199
	dieresis = 200
	ring = 202
	cedilla = 203
	hungarumlaut = 205
	ogonek = 206
	caron = 207
	emdash = 208
	AE = 225
	ordfeminine = 227
	Lslash = 232
	Oslash = 233
	OE = 234
	ordmasculine = 235
	ae = 241
	dotlessi = 245
	lslash = 248
	oslash = 249
	oe = 250
	germandbls = 251

class Latin1CharacterName(enum.IntEnum):
	space = 32
	exclam = 33
	quotedbl = 34
	numbersign = 35
	dollar = 36
	percent = 37
	ampersand = 38
	quoteright = 39
	parenleft = 40
	parenright = 41
	asterisk = 42
	plus = 43
	comma = 44
	minus = 45
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
	quoteleft = 96
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
	dotlessi = 144
	grave = 145
	circumflex = 147
	tilde = 148
	breve = 150
	dotaccent = 151
	ring = 154
	hungarumlaut = 157
	ogonek = 158
	caron = 159
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
	hyphen = 173
	registered = 174
	macron = 175
	degree = 176
	plusminus = 177
	twosuperior = 178
	threesuperior = 179
	acute = 180
	mu = 181
	paragraph = 182
	periodcentered = 183
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

character_names = {
	"!": "exclam",
	"\"": "quotedbl",
	" ": "space",
	"$": "dollar",
	"%": "percent",
	"&": "ampersand",
	"'": "quotesingle",
	"(": "parenleft",
	")": "parenright",
	"*": "asterisk",
	"+": "plus",
	",": "comma",
	"-": "hyphen",
	".": "period",
	"/": "slash",
	"0": "zero",
	"1": "one",
	"2": "two",
	"3": "three",
	"4": "four",
	"5": "five",
	"6": "six",
	"7": "seven",
	"8": "eight",
	"9": "nine",
	":": "colon",
	";": "semicolon",
	"<": "less",
	"=": "equal",
	">": "greater",
	"?": "question",
	"@": "at",
	"A": "A",
	"B": "B",
	"C": "C",
	"D": "D",
	"E": "E",
	"F": "F",
	"G": "G",
	"H": "H",
	"I": "I",
	"J": "J",
	"K": "K",
	"L": "L",
	"M": "M",
	"N": "N",
	"O": "O",
	"P": "P",
	"Q": "Q",
	"R": "R",
	"S": "S",
	"T": "T",
	"U": "U",
	"V": "V",
	"W": "W",
	"X": "X",
	"Y": "Y",
	"Z": "Z",
	"[": "bracketleft",
	"\\": "backslash",
	"]": "bracketright",
	"^": "asciicircum",
	"_": "underscore",
	"`": "grave",
	"a": "a",
	"b": "b",
	"c": "c",
	"d": "d",
	"e": "e",
	"f": "f",
	"fi": "fi",
	"fl": "fl",
	"g": "g",
	"h": "h",
	"i": "i",
	"j": "j",
	"k": "k",
	"l": "l",
	"m": "m",
	"n": "n",
	"o": "o",
	"p": "p",
	"q": "q",
	"r": "r",
	"s": "s",
	"t": "t",
	"u": "u",
	"v": "v",
	"w": "w",
	"x": "x",
	"y": "y",
	"z": "z",
	"{": "braceleft",
	"|": "bar",
	"}": "braceright",
	"~": "asciitilde",
	"¡": "exclamdown",
	"¢": "cent",
	"£": "sterling",
	"¤": "currency",
	"¥": "yen",
	"¦": "brokenbar",
	"§": "section",
	"¨": "dieresis",
	"©": "copyright",
	"ª": "ordfeminine",
	"«": "guillemotleft",
	"¬": "logicalnot",
	"®": "registered",
	"¯": "macron",
	"°": "degree",
	"±": "plusminus",
	"²": "twosuperior",
	"³": "threesuperior",
	"´": "acute",
	"µ": "mu",
	"¶": "paragraph",
	"·": "periodcentered",
	"¸": "cedilla",
	"¹": "onesuperior",
	"º": "ordmasculine",
	"»": "guillemotright",
	"¼": "onequarter",
	"½": "onehalf",
	"¾": "threequarters",
	"¿": "questiondown",
	"À": "Agrave",
	"Á": "Aacute",
	"Â": "Acircumflex",
	"Ã": "Atilde",
	"Ä": "Adieresis",
	"Å": "Aring",
	"Æ": "AE",
	"Ç": "Ccedilla",
	"È": "Egrave",
	"É": "Eacute",
	"Ê": "Ecircumflex",
	"Ë": "Edieresis",
	"Ì": "Igrave",
	"Í": "Iacute",
	"Î": "Icircumflex",
	"Ï": "Idieresis",
	"Ð": "Eth",
	"Ñ": "Ntilde",
	"Ò": "Ograve",
	"Ó": "Oacute",
	"Ô": "Ocircumflex",
	"Õ": "Otilde",
	"Ö": "Odieresis",
	"×": "multiply",
	"Ø": "Oslash",
	"Ù": "Ugrave",
	"Ú": "Uacute",
	"Û": "Ucircumflex",
	"Ü": "Udieresis",
	"Ý": "Yacute",
	"Þ": "Thorn",
	"ß": "germandbls",
	"à": "agrave",
	"á": "aacute",
	"â": "acircumflex",
	"ã": "atilde",
	"ä": "adieresis",
	"å": "aring",
	"æ": "ae",
	"ç": "ccedilla",
	"è": "egrave",
	"é": "eacute",
	"ê": "ecircumflex",
	"ë": "edieresis",
	"ì": "igrave",
	"í": "iacute",
	"î": "icircumflex",
	"ï": "idieresis",
	"ð": "eth",
	"ñ": "ntilde",
	"ò": "ograve",
	"ó": "oacute",
	"ô": "ocircumflex",
	"õ": "otilde",
	"ö": "odieresis",
	"÷": "divide",
	"ø": "oslash",
	"ù": "ugrave",
	"ú": "uacute",
	"û": "ucircumflex",
	"ü": "udieresis",
	"ý": "yacute",
	"þ": "thorn",
	"ÿ": "ydieresis",
	"Ā": "Amacron",
	"ā": "amacron",
	"Ă": "Abreve",
	"ă": "abreve",
	"Ą": "Aogonek",
	"ą": "aogonek",
	"Ć": "Cacute",
	"ć": "cacute",
	"Č": "Ccaron",
	"č": "ccaron",
	"Ď": "Dcaron",
	"ď": "dcaron",
	"Đ": "Dcroat",
	"đ": "dcroat",
	"Ē": "Emacron",
	"ē": "emacron",
	"Ė": "Edotaccent",
	"ė": "edotaccent",
	"Ę": "Eogonek",
	"ę": "eogonek",
	"Ě": "Ecaron",
	"ě": "ecaron",
	"Ğ": "Gbreve",
	"ğ": "gbreve",
	"Ģ": "Gcommaaccent",
	"ģ": "gcommaaccent",
	"Ī": "Imacron",
	"ī": "imacron",
	"Į": "Iogonek",
	"į": "iogonek",
	"İ": "Idotaccent",
	"ı": "dotlessi",
	"Ķ": "Kcommaaccent",
	"ķ": "kcommaaccent",
	"Ĺ": "Lacute",
	"ĺ": "lacute",
	"Ļ": "Lcommaaccent",
	"ļ": "lcommaaccent",
	"Ľ": "Lcaron",
	"ľ": "lcaron",
	"Ł": "Lslash",
	"ł": "lslash",
	"Ń": "Nacute",
	"ń": "nacute",
	"Ņ": "Ncommaaccent",
	"ņ": "ncommaaccent",
	"Ň": "Ncaron",
	"ň": "ncaron",
	"Ō": "Omacron",
	"ō": "omacron",
	"Ő": "Ohungarumlaut",
	"ő": "ohungarumlaut",
	"Œ": "OE",
	"œ": "oe",
	"Ŕ": "Racute",
	"ŕ": "racute",
	"Ŗ": "Rcommaaccent",
	"ŗ": "rcommaaccent",
	"Ř": "Rcaron",
	"ř": "rcaron",
	"Ś": "Sacute",
	"ś": "sacute",
	"Ş": "Scedilla",
	"ş": "scedilla",
	"Š": "Scaron",
	"š": "scaron",
	"Ţ": "Tcommaaccent",
	"ţ": "tcommaaccent",
	"Ť": "Tcaron",
	"ť": "tcaron",
	"Ū": "Umacron",
	"ū": "umacron",
	"Ů": "Uring",
	"ů": "uring",
	"Ű": "Uhungarumlaut",
	"ű": "uhungarumlaut",
	"Ų": "Uogonek",
	"ų": "uogonek",
	"Ÿ": "Ydieresis",
	"Ź": "Zacute",
	"ź": "zacute",
	"Ż": "Zdotaccent",
	"ż": "zdotaccent",
	"Ž": "Zcaron",
	"ž": "zcaron",
	"ƒ": "florin",
	"Ș": "Scommaaccent",
	"ș": "scommaaccent",
	"ˆ": "circumflex",
	"ˇ": "caron",
	"˘": "breve",
	"˙": "dotaccent",
	"˚": "ring",
	"˛": "ogonek",
	"˜": "tilde",
	"˝": "hungarumlaut",
	"–": "endash",
	"—": "emdash",
	"‘": "quoteleft",
	"’": "quoteright",
	"‚": "quotesinglbase",
	"“": "quotedblleft",
	"”": "quotedblright",
	"„": "quotedblbase",
	"†": "dagger",
	"‡": "daggerdbl",
	"•": "bullet",
	"…": "ellipsis",
	"‰": "perthousand",
	"‹": "guilsinglleft",
	"›": "guilsinglright",
	"⁄": "fraction",
	"™": "trademark",
	"∂": "partialdiff",
	"∆": "Delta",
	"∑": "summation",
	"−": "minus",
	"√": "radical",
	"≠": "notequal",
	"≤": "lessequal",
	"≥": "greaterequal",
	"◊": "lozenge",
	"": "commaaccent",
}

def build_encoding_array(codec):
	entries = [ ]
	last_codepoint = None
	for codepoint in range(256):
		char = bytes([ codepoint ]).decode(codec)
		psname = character_names.get(char)
		if psname is not None:
			psname = PDFName("/" + psname)
			if (last_codepoint is None) or (codepoint != last_codepoint + 1):
				entries.append(codepoint)
			entries.append(psname)
			last_codepoint = codepoint
	return entries
