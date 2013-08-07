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

class XmppHandler(EventHandler):
    def __init__(self, target_jids, req_id, message):
        self.target_jids = target_jids
        self.req_id = req_id
        self.message = message

    @event_handler(AuthorizedEvent)
    def handle_authorized(self, event):
        logging.debug(u"XmppHandler for request #%s authorized: %s", self.req_id, event)
        for jid in self.target_jids:
            logging.debug("XmppHandler for request #%s send message to %s", self.req_id, jid.as_string())
            message = Message(to_jid = jid, body = self.message)
            event.stream.send(message)
        event.stream.disconnect()

    @event_handler(DisconnectedEvent)
    def handle_disconnected(self, event):
        logging.debug("XmppHandler for request #%s disconnected: %s", self.req_id, event)
        return QUIT

    @event_handler()
    def handle_all(self, event):
        logging.info(u"XmppHandler for request #%s: %s", self.req_id, event)


class XmppClient(object):
    """
    A client for the XMPP servers. Reports information to the server.
    """
    NAME = "Review Board XMPP Notification Client"
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

        xmpp_host = self.extension.settings['xmpp_host']
        xmpp_port = self.extension.settings['xmpp_port']
        xmpp_timeout = self.extension.settings['xmpp_timeout']
        xmpp_sender_jid = self.extension.settings["xmpp_sender_jid"]
        xmpp_sender_password = self.extension.settings["xmpp_sender_password"]
        xmpp_use_tls = self.extension.settings["xmpp_use_tls"]
        xmpp_tls_verify_peer = self.extension.settings["xmpp_tls_verify_peer"]

        if sys.version_info[0] < 3:
            xmpp_sender_jid = xmpp_sender_jid.decode("utf-8")
            xmpp_sender_password = xmpp_sender_password.decode("utf-8")
            message = message.decode("utf-8")

        try:
            xmpp_sender_jid = JID(xmpp_sender_jid)
            receiver_jids = set()
            for receiver in receivers:
                receiver_jid = JID( local_or_jid = receiver, domain = xmpp_sender_jid.domain)
                receiver_jids.add(receiver_jid)

            handler = XmppHandler(receiver_jids, req_id, message)
            settings = XMPPSettings({
                            u"password": xmpp_sender_password,
                            u"starttls": xmpp_use_tls,
                            u"tls_verify_peer": xmpp_tls_verify_peer,
                            u"server" : xmpp_host,
                            u"port": xmpp_port,
                            u"default_stanza_timeout": xmpp_timeout,
                        })

            client = Client(xmpp_sender_jid, [handler], settings)
            client.connect()
            client.run( timeout = xmpp_timeout )
        except Exception, e:
            logging.error("Error sending XMPP notification for request #%s: %s",
                      req_id,
                      e,
                      exc_info=1)
