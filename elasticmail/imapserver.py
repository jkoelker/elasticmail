from twisted.mail import imap4
from zope.interface import implements


MAILBOXDELIMITER = '.'


class ImapUserAccount(object):
    implements(imap4.IAccount, imap4.INamespacePresenter)

    def __init__(self, user):
        self.user = user

    def addMailbox(self, name, mbox=None):
        if mbox:
            # Uhh what do we do
            pass
        else:
            return self.create(name)

    def create(self, pathspec):
        pass

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
    implements(imap4.IMessage)

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

