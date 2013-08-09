#
# setup.py
#
# Copyright (c) 2013  Horatiu Eugen Vlad
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from setuptools import setup

PACKAGE = "RBXmppNotification"
VERSION = "0.4"

setup(
    name=PACKAGE,
    version=VERSION,
    description="ReviewBoard XMPP Notification Extension",
    license="MIT",
    url="https://github.com/iconoeugen/rb-xmpp-notification",
    author="Horatiu Eugen Vlad",
    author_email="horatiuvlad[at]yahoo.com",
    packages=["rbxmppnotification"],
    entry_points={
        'reviewboard.extensions':
            '%s = rbxmppnotification.extension:RBXmppNotification' % PACKAGE,
    },
    package_data={
        'rbxmppnotification': [
            'htdocs/css/*.css',
            'htdocs/js/*.js',
            'templates/rbxmppnotification/*.txt',
            'templates/rbxmppnotification/*.html',
        ],
    },
    install_requires=[
            'pyxmpp2>=2.0alpha2',
            'argparse>=1.2',
        ],
)
