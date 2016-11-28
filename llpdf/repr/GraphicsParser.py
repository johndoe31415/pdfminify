#!/usr/bin/python3
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

import collections
from . import tpg
from . import ParseTools
from llpdf.types.PDFName import PDFName

class _CommandList(object):
	def _value_set(dictionary):
		result = { }
		for (key, value) in dictionary.items():
			if isinstance(value, int):
				result[key] = set([ value ])
			else:
				result[key] = set(value)
		return result

	_COMMAND_ARG_COUNT = _value_set({
		"b":	0,
		"b*":	0,
		"B":	0,
		"B*":	0,
		"BDC":	2,
		"BI":	0,
		"BMC":	1,
		"BT":	0,
		"c":	6,
		"cm":	6,
		"cs":	1,
		"CS":	1,
		"d0":	2,
		"d1":	6,
		"d":	2,
		"Do":	1,
		"DP":	2,
		"EI":	0,
		"EMC":	0,
		"ET":	0,
		"f":	0,
		"f*":	0,
		"F":	0,
		"g":	1,
		"G":	1,
		"gs":	1,
		"h":	0,
		"i":	1,
		"ID":	0,
		"j":	1,
		"J":	1,
		"k":	4,
		"K":	4,
		"l":	2,
		"M":	1,
		"m":	2,
		"MP":	1,
		"n":	0,
		"q":	0,
		"Q":	0,
		"re":	4,
		"rg":	3,
		"RG":	3,
		"ri":	1,
		"s":	0,
		"S":	0,
		"sc":	(1, 3, 4),
		"SC":	(1, 3, 4),
		"scn":	(1, 3, 4),
		"SCN":	(1, 3, 4),
		"sh":	1,
		"T*":	0,
		"Tc":	1,
		"Td":	2,
		"TD":	2,
		"Tf":	2,
		"Tj":	1,
		"TJ":	1,
		"TL":	1,
		"Tm":	6,
		"Tr":	1,
		"Ts":	1,
		"Tw":	1,
		"Tz":	1,
		"v":	4,
		"W":	0,
		"W*":	0,
		"w":	1,
		"y":	4,
	})

	@classmethod
	def cmdlengths(cls):
		return set(len(key) for key in cls._COMMAND_ARG_COUNT.keys())

	@classmethod
	def argument_count(cls, command_dict):
		counts = set()
		for lengths in command_dict.values():
			counts |= set(lengths)
		return counts

	@classmethod
	def cmds_by_length(cls):
		result = { }
		for (cmd, lengths) in cls._COMMAND_ARG_COUNT.items():
			if len(cmd) not in result:
				result[len(cmd)] = { }
			result[len(cmd)][cmd] = lengths
		return result

	@classmethod
	def _generate_lexer(cls):
		cmds_by_len = cls.cmds_by_length()
		command_lengths = sorted(cmds_by_len.keys(), reverse = True)
		for command_length in command_lengths:
			cmds = cmds_by_len[command_length]
			arg_counts = sorted(cls.argument_count(cmds))
			for arg_count in arg_counts:
				cmds_with_that_argcount = sorted(cmd for (cmd, cmd_argcnt) in cmds.items() if arg_count in cmd_argcnt)

				regex = "|".join(cmds_with_that_argcount).replace("*", "\\*")
				print("\t\ttoken cmd_%d_%d '(%s)';" % (command_length, arg_count, regex))

	@classmethod
	def _generate_parser(cls):
		arg_counts = sorted(cls.argument_count(cls._COMMAND_ARG_COUNT))
		cmd_lengths_by_arg_count = collections.defaultdict(set)
		for (cmd, cmd_arg_counts) in cls._COMMAND_ARG_COUNT.items():
			for arg_count in cmd_arg_counts:
				cmd_lengths_by_arg_count[arg_count].add(len(cmd))

		for arg_count in arg_counts:
			lhs = [ ]
			for i in range(1, arg_count + 1):
				lhs.append("GraphParam/p%d" % (i))
			cmds = [ "cmd_%d_%d/c" % (i, arg_count) for i in sorted(cmd_lengths_by_arg_count[arg_count], reverse = True) ]
			lhs.append("(" + " | ".join(cmds) + ")")

			params = [ "c" ]
			params += [ "p%d" % (i) for i in range(1, arg_count + 1) ]
			rhs = "		$ c = GraphCommand(%s)" % (", ".join(params))
			print((" ".join(lhs)), rhs)



	@classmethod
	def generate_grammar(cls):
		cls._generate_lexer()
		print()
		cls._generate_parser()


class GraphCommand(object):
	def __init__(self, command, *args):
		self._command = command
		self._args = args

	@property
	def command(self):
		return self._command

	@property
	def args(self):
		return self._args

	def __eq__(self, other):
		return (self.command, self.args) == (other.command, other.args)

	def __neq__(self, other):
		return not (self == other)

	def __repr__(self):
		return str(self)

	def __str__(self):
		if len(self._args) == 0:
			return "%s" % (self._command)
		else:
			return "%s(%s)" % (self._command, ", ".join(str(arg) for arg in self._args))

class GraphicsParser(tpg.VerboseParser):
	r"""
		separator space '[\s\n]+';

		token start_dict '<<';
		token end_dict '>>';
		token start_array '\[';
		token end_array '\]';
		token float   '-?\d*\.\d+'							$ float
		token integer   '-?\d+'								$ int
		token pdfname_token '/[^\s/<>\[\]()]*'				$ PDFName
		token string '\(([^\)\\]+|\\[\)\(]|\\\d{3})*\)';
		token hexstring '<[\na-fA-F0-9]*>'					$ ParseTools.to_hexstring

		token cmd_3_0 '(EMC)';
		token cmd_3_1 '(BMC|SCN|scn)';
		token cmd_3_2 '(BDC)';
		token cmd_3_3 '(SCN|scn)';
		token cmd_3_4 '(SCN|scn)';
		token cmd_2_0 '(B\*|BI|BT|EI|ET|ID|T\*|W\*|b\*|f\*)';
		token cmd_2_1 '(CS|Do|MP|SC|TJ|TL|Tc|Tj|Tr|Ts|Tw|Tz|cs|gs|ri|sc|sh)';
		token cmd_2_2 '(DP|TD|Td|Tf|d0)';
		token cmd_2_3 '(RG|SC|rg|sc)';
		token cmd_2_4 '(SC|re|sc)';
		token cmd_2_6 '(Tm|cm|d1)';
		token cmd_1_0 '(B|F|Q|S|W|b|f|h|n|q|s)';
		token cmd_1_1 '(G|J|M|g|i|j|w)';
		token cmd_1_2 '(d|l|m)';
		token cmd_1_4 '(K|k|v|y)';
		token cmd_1_6 '(c)';

		START/e -> GraphExpression/e
		;

		GraphExpression/e ->								$ e = list()
							(
									GraphCommand/c			$ e.append(c)
							)*
		;

		GraphCommand/c -> (
			(cmd_3_0/c | cmd_2_0/c | cmd_1_0/c)																						$ c = GraphCommand(c)
			| GraphParam/p1 (cmd_3_1/c | cmd_2_1/c | cmd_1_1/c)																		$ c = GraphCommand(c, p1)
			| GraphParam/p1 GraphParam/p2 (cmd_3_2/c | cmd_2_2/c | cmd_1_2/c)														$ c = GraphCommand(c, p1, p2)
			| GraphParam/p1 GraphParam/p2 GraphParam/p3 (cmd_3_3/c | cmd_2_3/c)														$ c = GraphCommand(c, p1, p2, p3)
			| GraphParam/p1 GraphParam/p2 GraphParam/p3 GraphParam/p4 (cmd_3_4/c | cmd_2_4/c | cmd_1_4/c)							$ c = GraphCommand(c, p1, p2, p3, p4)
			| GraphParam/p1 GraphParam/p2 GraphParam/p3 GraphParam/p4 GraphParam/p5 GraphParam/p6 (cmd_2_6/c | cmd_1_6/c)			$ c = GraphCommand(c, p1, p2, p3, p4, p5, p6)
		)
		;

		GraphName/e -> pdfname_token/e
		;

		GraphDict/d -> start_dict							$ d = dict()
						(
							GraphName/k GraphParam/v		$ d[k] = v
						)*
						end_dict
		;


		GraphArray/a ->		start_array					$ a = list()
							(
								GraphParam/p			$ a.append(p)
							)* end_array
		;

		GraphParam/p -> (
							integer/p
							| float/p
							| GraphArray/p
							| string/p
							| pdfname_token/p
							| GraphDict/p
							| hexstring/p
						)
		;


	"""

	verbose = 0

def parse(text):
	return ParseTools.parse_using(text, GraphicsParser)

if __name__ == "__main__":
	examples = [
		"q q q",
		"q q q Q 1 2 3 4 5 6 cm",
		"/P <</MCID 0 >>BDC",
	]

#	_CommandList.generate_grammar()

	for example in examples:
		print(parse(example))
