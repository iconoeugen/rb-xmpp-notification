#
# xmpp.py
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

import sys

from django.contrib.sites.models import Site

from pyxmpp2.jid import JID
from pyxmpp2.message import Message
from pyxmpp2.client import Client
from pyxmpp2.settings import XMPPSettings
from pyxmpp2.interfaces import EventHandler, event_handler, QUIT
from pyxmpp2.streamevents import AuthorizedEvent, DisconnectedEvent

def get_review_request_url(review_request):
    """
    Returns site base URL
    """
    current_site = Site.objects.get_current()
    siteconfig = current_site.config.get()
    domain_method = siteconfig.get("site_domain_method")

    base_url = u"%s://%s%s" % (domain_method, current_site.domain, review_request.get_absolute_url())
    if sys.version_info[0] < 3:
        base_url = base_url.decode("utf-8")
    return base_url

def get_users_review_request(review_request):
    """
    Returns the set of active users that are interested in the review request
    """
    users = set()
    for u in review_request.get_participants(): 
        users.add(u)

    if review_request.submitter.is_active:
        users.add(review_request.submitter)

    for u in review_request.target_people.filter(is_active=True):
        users.add(u)

    for group in review_request.target_groups.all():
        for address in group.users.filter(is_active=True):
            users.add(address)

    for profile in review_request.starred_by.all():
        if profile.user.is_active:
            users.add(profile.user)

    logging.debug("XMPP notification for review request #%s will be sent to: %s",review_request.get_display_id(), users)
    return users

class XmppClient(EventHandler):
    """
    A client to manage the XMPP connection and dispatch messages.
    """
    NAME = "Review Board XMPP Notification Client"
    VERSION = 0.1

    def __init__(self, host, port, timeout, from_jid, password, use_tls, tls_verify_peer):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.from_jid = from_jid
        self.password = password
        self.use_tls = use_tls
        self.tls_verify_peer = tls_verify_peer
        
        self.req_id = None
        self.client = None
        self.stanzas = None

    @event_handler(AuthorizedEvent)
    def handle_authorized(self, event):
        logging.debug(u"XmppClient event handler for request #%s authorized: %s", self.req_id, event)
        if self.client.stream != event.stream:
            logging.debug(u"XmppClient event handler ignore event")
            return
        for stanza in self.stanzas:
            logging.debug("XmppHandler for request #%s send message to %s", self.req_id, stanza.as_xml())
            event.stream.send(stanza)
        logging.debug(u"XmppHandler disconnecting stream for request #%s", self.req_id)
        self.client.disconnect()

    @event_handler(DisconnectedEvent)
    def handle_disconnected(self, event):
        logging.debug("XmppClient event handler for request #%s disconnected: %s", self.req_id, event)
        if self.client.stream != event.stream:
            logging.debug(u"XmppClient event handler ignore event")
            return
        logging.debug(u"XmppClient event handler closing stream for request #%s", self.req_id)
        self.client.close_stream()
        self.client = None
        return QUIT

    @event_handler()
    def handle_all(self, event):
        logging.debug(u"XmppClient event handler for request #%s: %s", self.req_id, event)

    def send(self, req_id, stanzas):
        self.req_id = req_id
        self.stanzas = stanzas
        logging.debug(u"XmppClient start sending messages for request #%s", self.req_id)
        try:
            settings = XMPPSettings({
                            u"password": self.password,
                            u"starttls": self.use_tls,
                            u"tls_verify_peer": self.tls_verify_peer,
                            u"server" : self.host,
                            u"port": self.port,
                            u"default_stanza_timeout": self.timeout,
                        })

            self.client = Client(self.from_jid, [self], settings)
            self.client.connect()
            self.client.run( timeout = self.timeout )
        except Exception, e:
            logging.error("Error sending XMPP notification for request #%s: %s",
                      req_id,
                      e,
                      exc_info=1)


class XmppSender(object):
    """
    A sender for the XMPP messages. Reports information to the server.
    """
    NAME = "Review Board XMPP Notification Sender"
    VERSION = 0.1

    def __init__(self, extension):
        self.extension = extension

    def send_review_request_published(self, user, review_request, changedesc):
        # If the review request is not yet public or has been discarded, don't send
        # any notification. Relax the "discarded" rule when notifications are sent on closing
        # review requests
        if ( not review_request.public ):
            return

        message = u"%s %s published review request #%d: \"%s\"\n%s" % (
            user.first_name, user.last_name,
            review_request.get_display_id(),
            review_request.summary,
            get_review_request_url(review_request))

        users = get_users_review_request(review_request)
        # Do not send notification to the user that triggered the update
        users.discard(user)

        self.send_xmpp_message(users, review_request.get_display_id(), message)

    def send_review_request_reopened(self, user, review_request):
        # If the review request is not yet public or has been discarded, don't send
        # any notification. Relax the "discarded" rule when notifications are sent on closing
        # review requests
        if ( not review_request.public ):
            return

        message = u"%s %s reopened review request #%d: \"%s\"\n%s" % (
            user.first_name, user.last_name,
            review_request.get_display_id(),
            review_request.summary,
            get_review_request_url(review_request))

        users = get_users_review_request(review_request)
        # Do not send notification to the user that triggered the update
        users.discard(user)

        self.send_xmpp_message(users, review_request.get_display_id(), message)

    def send_review_request_closed(self, user, review_request):
        # If the review request is not yet public or has been discarded, don't send
        # any notification. Relax the "discarded" rule when notifications are sent on closing
        # review requests
        if ( review_request.status == 'D'):
            return

        message = u"%s %s closed review request #%d: \"%s\"\n%s" % (
            user.first_name, user.last_name,
            review_request.get_display_id(),
            review_request.summary,
            get_review_request_url(review_request))

        users = get_users_review_request(review_request)
        # Do not send notification to the user that triggered the update
        users.discard(user)

        self.send_xmpp_message(users, review_request.get_display_id(), message)

    def send_review_published(self, user, review):
        review_request = review.review_request

        if not review_request.public:
            return

        message = u"%s %s reviewed request #%d: \"%s\"\n%s" % (
            user.first_name, user.last_name,
            review_request.get_display_id(), 
            review_request.summary,
            get_review_request_url(review_request))

        users = get_users_review_request(review_request)
        # Do not send notification to the user that triggered the update
        users.discard(user)

        self.send_xmpp_message(users, review_request.get_display_id(), message)

    def send_reply_published(self, user, reply):
        review = reply.base_reply_to
        review_request = review.review_request

        if not review_request.public:
            return

        message = u"%s %s replied review request #%d: \"%s\"\n%s" % (
            user.first_name, user.last_name,
            review_request.get_display_id(),
            review_request.summary,
            get_review_request_url(review_request))

        users = get_users_review_request(review_request)
        # Do not send notification to the user that triggered the update
        users.discard(user)

        self.send_xmpp_message(users, review_request.get_display_id(), message)

    def send_xmpp_message(self, receivers, req_id, message):
        """
        Formats and sends a XMPP notification with the current domain and review request
        being added to the template context. Returns the resulting message ID.
        """
        logging.info("XMPP notification send message for request #%s: %s", req_id, message)
        
        host = self.extension.settings['xmpp_host']
        port = self.extension.settings['xmpp_port']
        timeout = self.extension.settings['xmpp_timeout']
        from_jid = self.extension.settings["xmpp_sender_jid"]
        password = self.extension.settings["xmpp_sender_password"]
        use_tls = self.extension.settings["xmpp_use_tls"]
        tls_verify_peer = self.extension.settings["xmpp_tls_verify_peer"]

        if sys.version_info[0] < 3:
            from_jid = from_jid.decode("utf-8")
            password = password.decode("utf-8")
            message = message.decode("utf-8")

        try:
            from_jid = JID(from_jid)
            stanzas = set()
            for receiver in receivers:
                receiver_jid = JID( local_or_jid = receiver, domain = from_jid.domain)
                stanzas.add(Message(to_jid = receiver_jid, body = message))

            client = XmppClient(host, port, timeout, from_jid, password, use_tls, tls_verify_peer)
            client.send(req_id, stanzas)
        except Exception, e:
            logging.error("Error sending XMPP notification for request #%s: %s",
                      req_id,
                      e,
                      exc_info=1)
