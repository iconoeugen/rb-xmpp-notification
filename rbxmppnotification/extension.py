#
# extension.py -- RBXmppNotification Extension for Review Board.
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
#

import logging

from django.conf import settings
from django.conf.urls.defaults import patterns, include
from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import DashboardHook, URLHook

from rbxmppnotification.register import XmppSignals

class RBXmppNotificationURLHook(URLHook):
    def __init__(self, extension, *args, **kwargs):
        pattern = patterns('', (r'^rbxmppnotification/',
                            include('rbxmppnotification.urls')))
        super(RBXmppNotificationURLHook, self).__init__(extension, pattern)


class RBXmppNotificationDashboardHook(DashboardHook):
    def __init__(self, extension, *args, **kwargs):
        entries = [{
            'label': 'rbxmppnotification',
            'url': settings.SITE_ROOT + 'rbxmppnotification/',
        }]
        super(RBXmppNotificationDashboardHook, self).__init__(extension, entries=entries, *args, **kwargs)

class RBXmppNotification(Extension):
    is_configurable = True
    def __init__(self, *args, **kwargs):
        logging.debug(u"RBXmppNotification instantiated")
        super(RBXmppNotification, self).__init__(*args, **kwargs)
        self.url_hook = RBXmppNotificationURLHook(self)
        self.dashboard_hook = RBXmppNotificationDashboardHook(self)
        self.signals = XmppSignals(self) 
        self.signals.register_signals()
