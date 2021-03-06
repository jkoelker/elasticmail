import inspect
import sys
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import time
import urllib

import txes

from email import parser, iterators

from twisted.cred import portal
from twisted.internet import defer
from twisted.mail import imap4
from twisted.web import client
from zope.interface import implements


DELIM = '/'
ES = "192.168.56.101:9200"


emailparser = parser.Parser()


# From dectools package. This function is MIT licensed
# Copyright (c) 2010 by Charles Merriam
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
def _dict_as_called(function, args, kwargs):
    """ return a dict of all the args and kwargs as the keywords they would
    be received in a real function call.  It does not call function.
    """

    names, args_name, kwargs_name, defaults = inspect.getargspec(function)

    # assign basic args
    params = {}
    if args_name:
        basic_arg_count = len(names)
        params.update(zip(names[:], args))  # zip stops at shorter sequence
        params[args_name] = args[basic_arg_count:]
    else:
        params.update(zip(names, args))

    # assign kwargs given
    if kwargs_name:
        params[kwargs_name] = {}
        for kw, value in kwargs.iteritems():
            if kw in names:
                params[kw] = value
            else:
                params[kwargs_name][kw] = value
    else:
        params.update(kwargs)

    # assign defaults
    if defaults:
        for pos, value in enumerate(defaults):
            if names[-len(defaults) + pos] not in params:
                params[names[-len(defaults) + pos]] = value

    # check we did it correctly.  Each param and only params are set
    set1 = set(params.iterkeys())
    set2 = (set(names)|set([args_name])|set([kwargs_name]))-set([None])
    assert set1 == set2
    return params


class ElasticSearchError(Exception):
    pass


def formatName(name):
    if name.lower().startswith("inbox")
        return DELIM.join(["INBOX"] + name.split(DELIM)[1:])
    return name


class ElasticSearchPathWrapper(object):
    def __init__(self, *args, **kwargs):
        es = kwargs.get("servers") or kwargs.get("es") or ES
        self.es = txes.ElasticSearch(servers=es, discover=False)

    def _wrap_path(self, function, *args, **kwargs):
        params = _dict_as_called(function, args, kwargs)

        if "docType" in params:
            params["docType"] = urllib.quote(params["docType"], safe='')

        elif "docTypes" in params:
            if not params["docTypes"]:
                pass

            elif isinstance(docTypes, basestring):
                params["docTypes"] = urllib.quote(params["docTypes"],
                                                  safe='')

            else:
                params["docTypes"] = [urllib.quote(dt, safe='') \
                                      for dt in params["docTypes"]]
        return function(**params)

    def __getattr__(self, name):
        if hasattr(self.es, name):
            func = getattr(self.es, name)
            return lambda *args, **kwargs: self._wrap_path(func, *args,
                                                           **kwargs)
        raise AttributeError(name)


class ElasticSearchClient(object):
    def __init__(self, *args, **kwargs):
        es = kwargs.get("servers") or kwargs.get("es") or ES
        self.es = ElasticSearchPathWrapper(servers=es, discover=False)

class ImapUserAccount(ElasticSearchClient):
    implements(imap4.IAccount, imap4.INamespacePresenter)

    def __init__(self, owner, *args, **kwargs):
        ElasticSearchClient.__init__(self, *args, **kwargs)
        self.owner = owner
        self.args = args
        self.kwargs = kwargs

    def _newValidityUid(self):
        def factor(data):
            validityUid = int(time.time() % sys.maxint)
            if not data["hits"]["total"]:
                return validityUid

            hits = data["hits"]["hits"]
            usedUids = [d["fields"]["uid_validity"] for d in hits]

            while validityUid not in usedUids:
                validityUid = validityUid + 1
            return validityUid

        q = {"filter": {"exists": {"field": "uid_validity"}},
             "fields": ["uid_validity"]}
        d = self.es.search(q, self.owner, "config")
        return d.addCallback(factor)

    def _setupMailbox(self, path):
        def setup(validityUid):
            data = {"uid_validity": validityUid,
                    "owner": self.owner,
                    "path": path,
                    "search": {"query": {"term": {"path": path}}},
                    "flags": [],
                    "deleted": False,
                    "readers": [self.owner],
                    "writers": [self.owner]}
            d = self.es.index(data, self.owner, "config")
            return d.addCallback(lambda x: x["ok"] or False)

        d = self._newValidityUid()
        d.addCallback(setup)
        return d.addErrback(lambda _: False)

    def _getMailboxQuery(self, name):
        name = formatName(name)
        q = {"query": {"term": {"path": name}}}
        d = self.es.search(q, self.owner, "config")
        return d.addCallback(collision)

    def addMailbox(self, name, mbox=None):
        name = formatName(name)

        def collision(results):
            if results["hits"]["total"]:
                raise imap4.MailboxCollision(name)
            if not mbox:
                return self._setupMailbox(name)
            return False

        d = self._getMailboxQuery(name)
        return d.addCallback(collision)

    def create(self, pathspec):
        def factor(results):
            for success, value in results:
                if not success:
                    value.trap(imap4.MailboxCollision)
            return True

        pathspec = formatName(pathspec)
        paths = filter(None, pathspec.split(DELIM))
        dList = []
        for accum in range(1, len(paths)+1):
            dList.append(self.addMailbox(DELIM.join(paths[:accum])))
        return dList.addCallback(factor)
 
    def select(self, name, rw=True):
        name = formatName(name)
        def factor(results):
            if results["hits"]["total"]:
                return ElasticMailbox(self.owner, name, *self.args,
                                      rw=rw, **self.kwargs)
            return None

        d = self._getMailboxQuery(name)
        return d.addCallback(factor)

    def delete(self, name):
        name = formatName(name)

        def checkFlags(mbox):
            def raiseOrDestroy(results):
                configs = [r["source"] for r in results["hits"]["hits"]]
                for other in configs:
                    opath = other["path"]
                    if opath != name and opath.startswith(name + DELIM):
                        raise MailboxException("Hierarchically inferior "
                                               "mailboxes exist and "
                                               "\\Noselect is set")
                return mbox.destroy()

            if "\\Noselect" in mbox.getFlags():
                q = {"query": {"prefix": {"path": name}}}
                d = es.search(q, self.owner, "config")
                return d.addCallback(raiseOrDestroy)
 
            return mbox.destroy()

        def checkExists(results):
            if not results["hits"]["total"]:
                raise imap4.MailboxException("No such mailbox")

            d = self.select(name)
            return d.addCallback(checkFlagsAndDestroy)

        d = self._getMailboxQuery(name)
        return d.addCallback(checkExists)

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


class ElasticMessagePart(object):
    implements(imap4.IMessagePart)

    def __init__(self, message):
        self.message = message
        self.data = str(self.message)

    def getBodyFile(self):
        return StringIO(str(self.message.get_payload()))

    def getHeaders(self, negate, *names):
        names = set([name.lower() for name in names])
        if negate:
            headers = [name.lower() for name in self.message.keys() \
                       if name not in names]
        else:
            headers = names
        return dict([(name, self.message[name]) for name in headers \
                     if name in self.message])

    def getSize(self):
        return len(self.data)

    def getSubPart(self, index):
        return ElasticMessagePart(self.message.get_payload(index))

    def isMultipart(self):
        return self.message.is_multipart()


class ElasticMessage(ElasticMessagePart):
    implements(imap4.IMessage, imap4.IMessageFile)

    def __init__(self, uid, flags, msg):
        self.data = mmsg
        self.message = email.message_from_string(self.data)
        self.uid = uid
        self.flags = flags

    def getUID(self):
        return self.uid

    def getFlags(self):
        return self.flags

    def getInternalDate(self):
        return self.message.get("Date", '')

    def open(self):
        return StringIO(self.data)


class ElasticMailbox(ElasticSearchClient):
    implements(imap4.IMailbox, imap4.IMessageCopier,
               imap4.ISearchableMailbox)

    def __init__(self, owner, path, uidValidity, *args,
                 rw=True, uidNext=0, messagesMeta=None, refreshTime=30,
                 **kwargs):
        ElasticSearchClient.__init__(self, *args, **kwargs):
        self.owner = owner
        self.path = path
        self.refreshTime = refreshTime
        self.rw = rw
        self.uidValidity = uidValidity
        self.uidNext = uidNext

        if not messagesMeta:
            messagesMeta = []
        self.messagesMeta = messagesMeta

        self.listeners = []

    def copy(self, messageObject):
        deferred = None

    def getFlags(self):
        return ["\\Seen", "\\Unseen", "\\Deleted", "\\Flagged",
                "\\Answered", "\\Recent"]

    def getHierarchicalDelimiter(self):
        return DELIM

    def getUIDValidity(self):
        return self.uidValidity

    def getUIDNext(self):
        integer = None
        pass

    def getUID(self, message):
        integer = None
        pass

    def getMessageCount(self):
        integer = None
        pass

    def getRecentCount(self):
        integer = None
        pass

    def getUnseenCount(self):
        integer = None
        pass

    def isWriteable(self):
        return self.rw

    def destroy(self):
        nothing = None
        mustSet = "\\Noselect"

    def requestStatus(self, names):
        deferred = None

    def addListener(self, listener):
        self.listeners.append(listener)

    def removeListener(self, listener):
        self.listeners.remove(listener)

    def addMessage(self, message, flags=(), date=None):
        deferred = None

    def expunge(self):
        deferred = None

    def fetch(self, message, uid):
        deferred = None

    def store(self, messages, flags, mode, uid):
        deferred = None

    def search(query, uid):
        deferred = None


class ImapUserRealm(ElasticSearchClient):
    implements(portal.IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        if imap4.IAccount in interfaces:
            d = es.createIndexIfMissing(avatarId)
            return d.addCallback(lambda _: (imap4.IAccount,
                                            ImapUserAccount(avatarId),
                                            lambda: None))
        raise KeyError("None of the requested interfaces is supported")
