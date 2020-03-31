import setuptools

with open("README.md") as f:
	long_description = f.read()

setuptools.setup(
	name = "pdfminify",
	packages = setuptools.find_packages(),
	version = "0.2.1",
	license = "gpl-3.0",
	description = "PDF minification tool",
	long_description = long_description,
	long_description_content_type = "text/markdown",
	author = "Johannes Bauer",
	author_email = "joe@johannes-bauer.com",
	url = "https://github.com/johndoe31415/pdfminify",
	download_url = "https://github.com/johndoe31415/pdfminify/archive/0.2.1.tar.gz",
	keywords = [ "pdf", "minifier" ],
	install_requires = [ "llpdf>=0.0.4" ],
	entry_points = {
		"console_scripts": [
			"pdfminify = pdfminify.__main__:main"
		]
	},
	classifiers = [
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: End Users/Desktop",
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3 :: Only",
		"Programming Language :: Python :: 3.5",
		"Programming Language :: Python :: 3.6",
		"Programming Language :: Python :: 3.7",
		"Programming Language :: Python :: 3.8",
	],
)
