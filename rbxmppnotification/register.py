#
# register.py
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

from reviewboard.accounts.signals import user_registered
from reviewboard.reviews.models import ReviewRequest, Review
from reviewboard.reviews.signals import review_request_published, \
                                        review_published, reply_published, \
                                        review_request_closed, \
                                        review_request_reopened

from rbxmppnotification.xmpp import XmppSender

class XmppSignals(object):
    def __init__(self, extension):
        self.extension = extension
        self.sender = XmppSender(extension)

    def review_request_published_cb(self, sender, user, review_request, changedesc,
                                **kwargs):
        """
        Listens to the ``review_request_published`` signal and sends a
        notification if this type of notification is enabled (through
        ``xmpp_send_review_notify`` site configuration).
        """
        logging.debug(u"XmppSignal review_request_published_cb by %s %s for #%s; sender %s", user.first_name, user.last_name, review_request.get_display_id(),sender)
        if self.extension.settings['xmpp_send_review_notify']:
            self.sender.send_review_request_published(user, review_request, changedesc)

    def review_request_reopened_cb(self, sender, user, review_request,
                                **kwargs):
        """
        Listens to the ``review_request_published`` signal and sends a
        notification if this type of notification is enabled (through
        ``xmpp_send_review_notify`` site configuration).
        """
        logging.debug(u"XmppSignal review_request_reopened_cb by %s %s for #%s; sender %s", user.first_name, user.last_name, review_request.get_display_id(),sender)
        if self.extension.settings['xmpp_send_review_notify']:
            self.sender.send_review_request_reopened(user, review_request)

    def review_request_closed_cb(self, sender, user, review_request, **kwargs):
        """Sends notification when a review request is closed.

        Listens to the ``review_request_closed`` signal and sends a
        notification if this type of notification is enabled (through
        ``xmpp_send_review_close_notify`` site configuration).
        """
        logging.debug(u"XmppSignal review_request_closed_cb by %s %s for #%s; sender %s", user.first_name, user.last_name, review_request.get_display_id(),sender)
        if self.extension.settings['xmpp_send_review_close_notify']:
            self.sender.send_review_request_closed(user, review_request)

    def review_published_cb(self, sender, user, review, **kwargs):
        """
        Listens to the ``review_published`` signal and sends a notification if
        this type of notification is enabled (through
        ``xmpp_send_review_notify`` site configuration).
        """
        logging.debug(u"XmppSignal review_published_cb by %s %s for #%s; sender %s", user.first_name, user.last_name,
            review.review_request.get_display_id(),  sender)
        if self.extension.settings['xmpp_send_review_notify']:
            self.sender.send_review_published(user, review)

    def reply_published_cb(self, sender, user, reply, **kwargs):
        """
        Listens to the ``reply_published`` signal and sends a notification if
        this type of notification is enabled (through
        ``xmpp_send_review_notify`` site configuration).
        """
        logging.debug(u"XmppSignal reply_published_cb by %s %s for #%s; sender %s", user.first_name, user.last_name,
            reply.base_reply_to.review_request.get_display_id(), sender)
        if self.extension.settings['xmpp_send_review_notify']:
            self.sender.send_reply_published(user, reply)

    def user_registered_cb(self, user, **kwargs):
        """
        Listens for new user registrations and sends a new user registration
        notification to administrators, if enabled.
        """
        logging.debug(u"XmppSignals user_registered_cb %s %s", user.first_name, user.last_name)
        if self.extension.settings['xmpp_send_new_user_notify']:
            self.sender.send_xmpp_message(user, "Welcome to ReviewBoard")

    def register_signals(self):
            review_request_published.connect(self.review_request_published_cb,
                                             sender=ReviewRequest, dispatch_uid="rbxmppnotification")
            review_published.connect(self.review_published_cb, sender=Review, dispatch_uid="rbxmppnotification")
            reply_published.connect(self.reply_published_cb, sender=Review, dispatch_uid="rbxmppnotification")
            review_request_closed.connect(self.review_request_closed_cb,
                                          sender=ReviewRequest, dispatch_uid="rbxmppnotification")
            review_request_reopened.connect(self.review_request_reopened_cb,
                                          sender=ReviewRequest, dispatch_uid="rbxmppnotification")
            user_registered.connect(self.user_registered_cb, dispatch_uid="rbxmppnotification")

