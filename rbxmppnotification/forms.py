#
# forms.py
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

import sys

from pyxmpp2.jid import JID
from pyxmpp2.jid import JIDError

from django import forms
from django.utils.translation import ugettext as _
from djblets.extensions.forms import SettingsForm

class RBXmppNotificationSettingsForm(SettingsForm):
    """
    XMPP settings for Review Board admin form.
    """
    xmpp_send_review_notify = forms.BooleanField(
        label="Send notification for review requests and reviews",
        required=False)
    xmpp_send_review_close_notify = forms.BooleanField(
        label="Send notification when review requests are closed",
        required=False)
    xmpp_send_new_user_notify = forms.BooleanField(
        label="Send notification when new users register an account",
        required=False)
    xmpp_host = forms.CharField(
        label="Server Hostname",
        required=True,
        widget=forms.TextInput(attrs={'size': '50'}))
    xmpp_port = forms.IntegerField(
        label="Server Port",
        help_text="The port number where the XMPP server, the default port number is 5222.",
        required=True,
        widget=forms.TextInput(attrs={'size': '5'}))
    xmpp_timeout = forms.IntegerField(
        label="Server Connection Timeout",
        help_text="The number of seconds to wait for the XMPP messages to be sent.",
        required=False,
        widget=forms.TextInput(attrs={'size': '3'}))
    xmpp_sender_jid = forms.CharField(
        label="Sender XMPP JID",
        help_text=" JID is structured like an email address with a username and a domain name"
            " (or IP address[15]) for the server where that user resides, separated by an at sign (@),"
            " such as username@example.com."
            " A resource identifies a particular client belonging to the user (for example home, work, or mobile)."
            " This may be included in the JID by appending a slash followed by the name of the resource."
            " For example, the full JID of a user's mobile account would be username@example.com/mobile.",
        required=True,
        widget=forms.TextInput(attrs={'size': '50'}))
    xmpp_sender_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'size': '30'}),
        label="Sender XMPP Password",
        required=False)
    xmpp_use_tls = forms.BooleanField(
        label="Use TLS for XMPP authentication",
        required=False)
    xmpp_tls_verify_peer = forms.BooleanField(
        label="Verify peer self signed certificate",
        required=False)
    xmpp_partychat = forms.CharField(
        label="Partychat room JID",
        help_text="Send notifications to a partychat room. Multiple rooms can"
                  " be separated with spaces.",
        required=False,
        widget=forms.TextInput(attrs={'size': '50'}))
    xmpp_partychat_only = forms.BooleanField(
        label="Send partychat notifications only.",
        help_text="Do not send notifications to individual users.",
        required=False)

    def clean_xmpp_host(self):
        # Strip whitespaces from the Server address.
        h = self.cleaned_data['xmpp_host'].strip()
        if not h:
            raise forms.ValidationError('Enter a valid hostname.')
        return h

    def clean_xmpp_sender_jid(self):
        j = self.cleaned_data['xmpp_sender_jid'].strip()
        if sys.version_info[0] < 3:
            j = j.decode("utf-8")
        try:
            JID(j)
        except JIDError:
            raise forms.ValidationError('Enter a valid JID.')
        return j

    def clean_xmpp_partychat(self):
        xmpp_partychat = self.cleaned_data['xmpp_partychat']
        rooms = xmpp_partychat.split()
        if sys.version_info[0] < 3:
            rooms = [room.decode("utf-8") for room in rooms]
        for room in rooms:
            try:
                JID(room)
            except JIDError:
                raise forms.ValidationError('Enter a valid room JID.')
        return xmpp_partychat

    def save(self):
        super(RBXmppNotificationSettingsForm, self).save()

    class Meta:
        title = "XMPP Notify Settings"
