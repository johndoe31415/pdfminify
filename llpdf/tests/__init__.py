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

import os
import sys
import importlib
import unittest

def _get_test_module_names(test_module_path):
	for filename in os.listdir(test_module_path):
		full_filename = test_module_path + "/" + filename
		if filename.startswith("_") or filename.startswith("."):
			continue
		if not filename.endswith(".py"):
			continue
		if not os.path.isfile(full_filename):
			continue
		module_base = filename[:-3]
		module_name = "llpdf.tests." + module_base
		yield module_name

def _get_test_modules(test_module_path):
	for module_name in _get_test_module_names(test_module_path):
		yield importlib.import_module(module_name)

def run(terminate_after = False):
	tcloader = unittest.TestLoader()
	suite = unittest.TestSuite()

	test_module_path = os.path.dirname(__file__)
	for test_module in _get_test_modules(test_module_path):
		new_tests = tcloader.loadTestsFromModule(test_module)
		suite.addTests(new_tests)

	test_result = unittest.TextTestRunner(verbosity = 1).run(suite)
	test_success = test_result.wasSuccessful()
	if terminate_after:
		sys.exit(0 if test_success else 1)
	return test_success
