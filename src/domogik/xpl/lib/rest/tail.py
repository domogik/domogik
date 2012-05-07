# -*- coding: utf-8 -*-                                                                           

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Purpose
==============

Tail functionnality

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import os
import itertools
import re
import urllib

class Tail():
    """ Tail tool
    """

    def __init__(self, file, number, offset = 0):
        """ Return the N last lines of a file as a string
        """
        f=open(file,'rb')
        self.result = ""
        for line in self.tail(f, number, offset):
            self.result += "%s\n" % line

    def get(self):
        """ return result
        """
        return self.result

    def get_html(self):
        """ return result in html
        """
        result = self.result
        unknown = "<div class='unknown'>"
        error = "<div class='error'>"
        warning = "<div class='warning'>"
        info = "<div class='info'>"
        debug = "<div class='debug'>"
        date = "<span class='date'>"
        type = "<span class='type'>"
        text = "<span class='text'>"
        end_span = "</span>"
        end_div = "</div>"
        result = re.sub(r'(.*)(ERROR)(.*)', 
                            "%s%s%s%s\\1%s%s\\2%s%s\\3" % (end_span,
                                                           end_div,
                                                           error, date,
                                                           end_span, type,
                                                           end_span, text),
                            result)
        result = re.sub(r'(.*)(WARNING)(.*)', 
                            "%s%s%s%s\\1%s%s\\2%s%s\\3" % (end_span,
                                                           end_div,
                                                           warning, date,
                                                           end_span, type,
                                                           end_span, text),
                            result)
        result = re.sub(r'(.*)(INFO)(.*)', 
                            "%s%s%s%s\\1%s%s\\2%s%s\\3" % (end_span,
                                                           end_div,
                                                           info, date,
                                                           end_span, type,
                                                           end_span, text),
                            result)
        result = re.sub(r'(.*)(DEBUG)(.*)', 
                            "%s%s%s%s\\1%s%s\\2%s%s\\3" % (end_span,
                                                           end_div,
                                                           debug, date,
                                                           end_span, type,
                                                           end_span, text),
                            result)
        return "%s%s%s%s%s%s%s%s%s" % (unknown,
                                 date, end_span,
                                 type, end_span,
                                 text, result,
                                 end_span, end_div)

    def rblocks(self, f, blocksize=4096):
        """Read file as series of blocks from end of file to start.
    
        The data itself is in normal order, only the order of the blocks is reversed.
        ie. "hello world" -> ["ld","wor", "lo ", "hel"]
        Note that the file must be opened in binary mode.
        """
        if 'b' not in f.mode.lower():
            raise Exception("File must be opened using binary mode.")
        size = os.stat(f.name).st_size
        fullblocks, lastblock = divmod(size, blocksize)
    
        # The first(end of file) block will be short, since this leaves 
        # the rest aligned on a blocksize boundary.  This may be more 
        # efficient than having the last (first in file) block be short
        f.seek(-lastblock,2)
        yield f.read(lastblock)
    
        for i in range(fullblocks-1,-1, -1):
            f.seek(i * blocksize)
            yield f.read(blocksize)
    
    def tail(self, f, nlines, offset):
        """ tail
            @param nlines : number of lines to get
            @param offset : start at N lines from the end
        """
        buf = ''
        result = []
        for block in self.rblocks(f):
            buf = block + buf
            lines = buf.splitlines()
    
            # Return all lines except the first (since may be partial)
            if lines:
                result.extend(lines[1:]) # First line may not be complete
                if(len(result) >= nlines + offset):
                    if offset == 0:
                        return result[-nlines - offset:]
                    else:
                        return result[-nlines - offset:-offset]
    
                buf = lines[0]
    
        if offset == 0:
            return ([buf]+result)[-nlines - offset:]
        else:
            return ([buf]+result)[-nlines - offset:-offset]
    
if __name__ == "__main__":
    print(Tail("/tmp/tail", 5).get())
    print("----")
    print(Tail("/tmp/tail", 5, 3).get())
