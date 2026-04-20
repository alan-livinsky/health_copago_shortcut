#!/usr/bin/env python

from setuptools import setup
import configparser
import os
import re


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname),
                encoding='utf-8').read()


config = configparser.ConfigParser()
config.read_file(open('tryton.cfg'))
info = dict(config.items('tryton'))

for key in ('depends', 'extras_depend', 'xml'):
    if key in info:
        info[key] = info[key].strip().splitlines()
major_version, minor_version = 6, 0

requires = []
for dep in info.get('depends', []):
    if dep == 'health':
        requires.append('gnuhealth == %s' % info.get('version'))
    elif dep.startswith('health_'):
        health_package = dep.split('_', 1)[1]
        requires.append(
            'gnuhealth_%s == %s' % (health_package, info.get('version')))
    else:
        if not re.match(r'(ir|res|webdav)(\W|$)', dep):
            requires.append(
                'trytond_%s >= %s.%s, < %s.%s' % (
                    dep, major_version, minor_version,
                    major_version, minor_version + 1))

setup(
    name='gnuhealth_copago_shortcut',
    version=info.get('version', '0.0.1'),
    description='GNU Health shortcuts for copago generation from appointments',
    long_description=read('README.rst'),
    author='OpenAI',
    author_email='support@openai.com',
    url='https://www.gnuhealth.org',
    package_dir={'trytond.modules.health_copago_shortcut': '.'},
    packages=[
        'trytond.modules.health_copago_shortcut',
        'trytond.modules.health_copago_shortcut.wizard',
    ],
    package_data={
        'trytond.modules.health_copago_shortcut': info.get('xml', [])
        + ['tryton.cfg', 'report/*.fodt'],
    },
    license='GPL-3',
    install_requires=requires,
    zip_safe=False,
    entry_points="""
    [trytond.modules]
    health_copago_shortcut = trytond.modules.health_copago_shortcut
    """,
)
