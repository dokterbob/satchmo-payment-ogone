#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

try:
    README = open('README.rst').read()
except:
    README = None

try:
    REQUIREMENTS = open('requirements.txt').lines()
except:
    REQUIREMENTS = None

setup(
    name='satchmo-payment-ogone',
    version='0.1',
    description='Satchmo payment module for Ogone.',
    long_description=README,
    install_requires=REQUIREMENTS,
    author='Mathijs de Bruin',
    author_email='mathijs@mathijsfietst.nl',
    url='http://github.com/dokterbob/satchmo-payment-ogone',
    packages = find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)
