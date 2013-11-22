# Copyright (C) 2003-2007, 2009, 2010 Nominum, Inc.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose with or without fee is hereby granted,
# provided that the above copyright notice and this permission notice
# appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND NOMINUM DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL NOMINUM BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""DNS RRsets (an RRset is a named rdataset)"""

from __future__ import absolute_import

from . import name as dns_name
from . import rdata as dns_rdata
from . import rdataset as dns_rdataset
from . import rdatatype as dns_rdatatype
from . import rdataclass as dns_rdataclass
#from . import renderer as dns_renderer

class RRset(dns_rdataset.Rdataset):
    """A DNS RRset (named rdataset).

    RRset inherits from Rdataset, and RRsets can be treated as
    Rdatasets in most cases.  There are, however, a few notable
    exceptions.  RRsets have different to_wire() and to_text() method
    arguments, reflecting the fact that RRsets always have an owner
    name.
    """

    __slots__ = ['name', 'deleting']

    def __init__(self, name, rdclass, rdtype, covers=dns_rdatatype.NONE,
                 deleting=None):
        """Create a new RRset."""

        super(RRset, self).__init__(rdclass, rdtype, covers)
        self.name = name
        self.deleting = deleting

    def _clone(self):
        obj = super(RRset, self)._clone()
        obj.name = self.name
        obj.deleting = self.deleting
        return obj

    def __repr__(self):
        if self.covers == 0:
            ctext = ''
        else:
            ctext = '(' + dns_rdatatype.to_text(self.covers) + ')'
        if not self.deleting is None:
            dtext = ' delete=' + dns_rdataclass.to_text(self.deleting)
        else:
            dtext = ''
        return '<DNS ' + str(self.name) + ' ' + \
               dns_rdataclass.to_text(self.rdclass) + ' ' + \
               dns_rdatatype.to_text(self.rdtype) + ctext + dtext + ' RRset>'

    def __str__(self):
        return self.to_text()

    def __eq__(self, other):
        """Two RRsets are equal if they have the same name and the same
        rdataset

        @rtype: bool"""
        if not isinstance(other, RRset):
            return False
        if self.name != other.name:
            return False
        return super(RRset, self).__eq__(other)

    def match(self, name, rdclass, rdtype, covers, deleting=None):
        """Returns True if this rrset matches the specified class, type,
        covers, and deletion state."""

        if not super(RRset, self).match(rdclass, rdtype, covers):
            return False
        if self.name != name or self.deleting != deleting:
            return False
        return True

    def to_text(self, origin=None, relativize=True, **kw):
        """Convert the RRset into DNS master file format.

        @see: L{dns_name.Name.choose_relativity} for more information
        on how I{origin} and I{relativize} determine the way names
        are emitted.

        Any additional keyword arguments are passed on to the rdata
        to_text() method.

        @param origin: The origin for relative names, or None.
        @type origin: dns_name.Name object
        @param relativize: True if names should names be relativized
        @type relativize: bool"""

        return super(RRset, self).to_text(self.name, origin, relativize,
                                          self.deleting, **kw)

    def to_wire(self, file, compress=None, origin=None, **kw):
        """Convert the RRset to wire format."""

        return super(RRset, self).to_wire(self.name, file, compress, origin,
                                          self.deleting, **kw)

    def to_rdataset(self):
        """Convert an RRset into an Rdataset.

        @rtype: dns_rdataset.Rdataset object
        """
        return dns_rdataset.from_rdata_list(self.ttl, list(self))


def from_text_list(name, ttl, rdclass, rdtype, text_rdatas):
    """Create an RRset with the specified name, TTL, class, and type, and with
    the specified list of rdatas in text format.

    @rtype: dns_rrset.RRset object
    """

    if isinstance(name, (str, unicode)):
        name = dns_name.from_text(name, None)
    if isinstance(rdclass, (str, unicode)):
        rdclass = dns_rdataclass.from_text(rdclass)
    if isinstance(rdtype, (str, unicode)):
        rdtype = dns_rdatatype.from_text(rdtype)
    r = RRset(name, rdclass, rdtype)
    r.update_ttl(ttl)
    for t in text_rdatas:
        rd = dns_rdata.from_text(r.rdclass, r.rdtype, t)
        r.add(rd)
    return r

def from_text(name, ttl, rdclass, rdtype, *text_rdatas):
    """Create an RRset with the specified name, TTL, class, and type and with
    the specified rdatas in text format.

    @rtype: dns_rrset.RRset object
    """

    return from_text_list(name, ttl, rdclass, rdtype, text_rdatas)

def from_rdata_list(name, ttl, rdatas):
    """Create an RRset with the specified name and TTL, and with
    the specified list of rdata objects.

    @rtype: dns_rrset.RRset object
    """

    if isinstance(name, (str, unicode)):
        name = dns_name.from_text(name, None)

    if len(rdatas) == 0:
        raise ValueError("rdata list must not be empty")
    r = None
    for rd in rdatas:
        if r is None:
            r = RRset(name, rd.rdclass, rd.rdtype)
            r.update_ttl(ttl)
            first_time = False
        r.add(rd)
    return r

def from_rdata(name, ttl, *rdatas):
    """Create an RRset with the specified name and TTL, and with
    the specified rdata objects.

    @rtype: dns_rrset.RRset object
    """

    return from_rdata_list(name, ttl, rdatas)
