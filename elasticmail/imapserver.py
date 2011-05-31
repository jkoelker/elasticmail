import urllib
import urlparse

import anyjson

from twisted.cred import portal
from twisted.internet import defer
from twisted.mail import imap4
from twisted.web import client
from zope.interface import implements


MAILBOXDELIMITER = '/'
ES_URL = "http://192.168.56.101:9200"

def getPageFactory(url, contextFactory=None, *args, **kwargs):
    return client._makeGetterFactory(url, client.HTTPClientFactory,
                                     contextFactory, *args, **kwargs)


class ElasticSearchError(Exception):
    pass


class ImapUserAccount(object):
    implements(imap4.IAccount, imap4.INamespacePresenter)

    def __init__(self, owner):
        self.owner = owner
        self.user self.domain = owner.split('@')

    def _setAlias(self, mbox, name):
        pass

    def addMailbox(self, name, mbox=None):
        if mbox:
            return self._setAlias(mbox, name)
        else:
            return self.create(name)

    def create(self, pathspec):
        pathspec = pathspec.strip(MAILBOXDELIMITER)

        d = self.ensure_path(pathspec)
        return d
            
    def ensureMailboxConfig(self, path):
        mailbox = path.split(MAILBOXDELIMITER)[-1]
        url = '/'.join([ES_URL, self.user, "config", path])
        user, domain = self.user.split('@')

        data = { "uid_validity": self.newValidityUID(),
                 "owner": self.owner,
                 "user": self.user,
                 "domain": self.domain,
                 "aliases": [],
                 "path": path,
                 "mailbox": mailbox
                 "readers": [self.owner],
                 "writers": [self.owner],
                 }
        factory = getPageFactory(url, method="PUT", postdata=data) 

        def success(body):
            res = anyjson.deserialize(body)

        def fail(error):
            raise imap4.MailboxException()

        factory.deferred.addCallbacks(callback=success, errback=fail)
        return factory.deferred

    def ensure_index(self, user):
        url = '/'.join([ES_URL, user])
        factory = getPageFactory(url, method="PUT")

        def success(body):
            res = anyjson.deserialize(body)

            if int(factory.status) != 200:
                raise ElasticSearchError(res.get("error"))
            elif not res.get("ok"):
                raise ElasticSearchError(body)

            return (imap4.IAccount, ImapUserAccount(user), lambda: None)
        
        factory.deferred.addCallback(success)
        return factory.deferred
        
    def requestAvatar(self, avatarId, mind, *interfaces):
        if imap4.IAccount in interfaces:
            return self.ensure_index(avatarId)

    def select(self, name, rw=True):
        pass

    def delete(self, name):
        pass

    def rename(self, oldname, newname):
        pass

    def isSubscribed(self, name):
        pass

    def subscribe(self, name):
        pass

    def unsubscribe(self, name):
        pass

    def listMailboxes(self, ref, wildcard):
        pass

    def getPersonalNamespaces(self):
        pass

    def getSharedNamespace(self):
        pass

    def getUserNamespaces(self):
        pass


class ElasticMessage(object):
    implements(imap4.IMessage, imap4.IMessageFile)

    def getHeaders(self, negate, *names):
        pass

    def getBodyFile(self):
        pass

    def getSize(self):
        pass

    def isMultipart(self):
        pass

    def getSubPart(self, part):
        pass

    def getUID(self):
        pass

    def getFlags(self):
        pass

    def getInternalDate(self):
        pass

    def open(self):
        pass


class ElasticMailbox(object):
    implements(imap4.IMailbox, imap4.IMessageCopier,
               imap4.ISearchableMailbox)

    def copy(self, messageObject):
        pass

    def getFlags(self):
        pass

    def getHierarchicalDelimiter(self):
        pass

    def getUIDValidity(self):
        pass

    def getUIDNext(self):
        pass

    def getUID(self, message):
        pass

    def getMessageCount(self):
        pass

    def getRecentCount(self):
        pass

    def getUnseenCount(self):
        pass

    def isWriteable(self):
        pass

    def destroy(self):
        pass

    def requestStatus(self, names):
        pass

    def addListener(self, listener):
        pass

    def removeListener(self, listener):
        pass

    def addMessage(self, message, flags=(), date=None):
        pass

    def expunge(self):
        pass

    def fetch(self, message, uid):
        pass

    def store(self, messages, flags, mode, uid):
        pass

    def search(query, uid):
        pass


class ImapUserRealm(object):
    implements(portal.IRealm)

    def ensureIndex(self, user):
        url = '/'.join([ES_URL, user])
        factory = getPageFactory(url, method="PUT")

        def success(body):
            res = anyjson.deserialize(body)

            if int(factory.status) != 200:
                raise ElasticSearchError(res.get("error"))
            elif not res.get("ok"):
                raise ElasticSearchError(body)

            return (imap4.IAccount, ImapUserAccount(user), lambda: None)
        
        factory.deferred.addCallback(success)
        return factory.deferred
        
    def requestAvatar(self, avatarId, mind, *interfaces):
        if imap4.IAccount in interfaces:
            return self.ensureIndex(avatarId)
        raise KeyError("None of the requested interfaces is supported")
