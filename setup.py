#!/usr/bin/env python

from distutils.core import setup

setup(name='ethp2psim',
	version='1.0',
	description='Ethereum peer-to-peer network simulator',
	author='Ferenc Béres',
	author_email='fberes@sztaki.hu',
	packages=['ethp2psim'],
	install_requires=[
		"numpy",
		"scipy",
		"pandas",
		"networkx",
		"jupyterlab",
		"ipywidgets",
		"pytest",
		"pytest-cov",
		"matplotlib",
		"seaborn",
		"plotly",
		"kaleido",
		"ipywidgets>=7.5",
		"tqdm",
		"black",
		"black[jupyter]",
		"wget",
	],
)