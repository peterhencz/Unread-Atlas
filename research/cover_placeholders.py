"""Stable, accessible gradient placeholders for books without matched covers."""
from html import escape
PALETTES = [('a7b8ee','eadbeb'),('e9b5a4','f0ddbc'),('a5c4c2','dce5d1'),('b6afe0','e8cbd4'),('9fbfd9','e2dfe9'),('c4c5a4','e9d5ba')]
def placeholder(title, author):
    seed = sum((i+1)*ord(ch) for i,ch in enumerate(title+'|'+author))
    start,end=PALETTES[seed%len(PALETTES)]
    return '<span class="nocover" role="img" aria-label="'+escape('Cover unavailable: '+title,quote=True)+'" style="--cover-start:#'+start+';--cover-end:#'+end+';--cover-angle:'+str(120+seed%4*20)+'deg"></span>'
