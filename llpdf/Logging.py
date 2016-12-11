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

import logging
import enum

class LogLevel(enum.IntEnum):
	Silent = 0
	Normal = 1
	Verbose = 2
	Debug = 3

	@classmethod
	def getbyname(cls, name):
		lookup = { level.name.lower(): level for level in cls }
		return lookup[name.lower()]

	@classmethod
	def getnames(cls):
		levels = list(cls)
		levels.sort(key = lambda level: int(level))
		return [ level.name for level in levels ]

	@classmethod
	def getbyverbosity(cls, intvalue):
		maxvalue = max(int(level) for level in cls)
		if intvalue > maxvalue:
			intvalue = maxvalue
		return cls(intvalue)


def configure_logging(verbosity_loglevel):
	llvl = LogLevel.getbyverbosity(verbosity_loglevel)

	logging.TRACE = logging.DEBUG - 1
	logging.addLevelName(logging.TRACE, "TRACE")

	logging_loglevel = {
		LogLevel.Silent:	logging.WARNING,
		LogLevel.Normal:	logging.INFO,
		LogLevel.Verbose:	logging.DEBUG,
		LogLevel.Debug:		logging.TRACE,
	}[llvl]

	def __log_trace(self, message, *args, **kwargs):
		if self.isEnabledFor(logging.TRACE):
			self._log(logging.TRACE, message, args, **kwargs)
	logging.Logger.trace = __log_trace

	logging.basicConfig(format = " {name:>20s} [{levelname:.1s}]: {message}", style = "{", level = logging_loglevel)

if __name__ == "__main__":
	configure_logging(LogLevel.Debug)

	log = logging.getLogger("llpdf.foobar.barfoo")
	log.error("This is an error")
	log.warning("This is a warning")
	log.info("This is an information")
	log.debug("This is debug drivel")
	log.trace("Trace message")

	logger = logging.getLogger("llpdf")
	logger.warning("foo bar")

	print(LogLevel.getbyname("nOrMaL"))
	print(LogLevel.getnames())
