#!/usr/bin/env python
#encoding:utf-8

from setuptools import setup

setup(
    name='gnarlytvdb',
    version='0.01',
    description='A python interface to thetvdb.com xml api.',
    author='Steinthor Palsson',
    author_email='steinitzu@gmail.com',
    url='https://github.com/steinitzu',
    license='MIT',

    include_package_data=True,
    
    packages=[
        'gnarlytvdb', 
        ],
    
    install_requires=[
        'httplib2',
        'xmltodict',
        ]
    )

