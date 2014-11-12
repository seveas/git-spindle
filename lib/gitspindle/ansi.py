import sys

class Attr(object):
    def __init__(self, **attr):
        self.attr = attr
        self.rev_attr = dict([(v,k) for k,v in attr.items()])
        for k, v in attr.items():
            setattr(self, k, v)

    def name(self, val):
        return self.rev_attr[val]

    def xterm(self, val):
        return '%d;5;%d' % (self._xterm, val)

fgcolor = Attr(black=30, red=31, green=32, yellow=33, blue=34, magenta=35, cyan=36, white=37, _xterm=38, default=39, none=None)
bgcolor = Attr(black=40, red=41, green=42, yellow=43, blue=44, magenta=45, cyan=46, white=47, _xterm=48, default=49, none=None)
attr    = Attr(normal=0, bright=1, faint=2, underline=4, negative=7, conceal=8, crossed=9, none=None)

esc = '\033'
mode = lambda *args: "%s[%sm" % (esc, ';'.join([str(x) for x in args if x is not None]))
reset = mode(attr.normal)
if sys.stdout.isatty():
    wrap = lambda text, *args: "%s%s%s" % (mode(*args), text, reset)
else:
    wrap = lambda text, *args: text

erase_line = esc + '[K'
erase_display = esc + '[2J'
save_cursor = esc + '[s'
restore_cursor = esc + '[u'

del sys
del Attr
