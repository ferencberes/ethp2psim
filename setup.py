#!/usr/bin/env python

from distutils.core import setup

setup(name='ethp2psim',
	version='1.0',
	description='Ethereum peer-to-peer network simulator',
	author='Ferenc Béres, Istvan Andras Seres, Domokos Miklos Kelen',
	author_email='beres@sztaki.hu',
	packages=['ethp2psim'],
	install_requires=[
		"numpy",
		"scipy",
		"pandas",
		"networkx",
		"pytest",
		"pytest-cov",
		"matplotlib",
		"plotly",
		"kaleido",
		"tqdm",
		"wget",
	],
)