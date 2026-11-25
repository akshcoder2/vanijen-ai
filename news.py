"""Public news headline research (no scraping or claims beyond the feed)."""
from html import unescape
from urllib.parse import urlencode
from urllib.request import urlopen
import xml.etree.ElementTree as ET


def headlines(query=''):
    params = {'hl': 'en-IN', 'gl': 'IN', 'ceid': 'IN:en'}
    path = '/rss'
    if query:
        path += '/search'
        params['q'] = query
    with urlopen('https://news.google.com' + path + '?' + urlencode(params), timeout=12) as response:
        data = response.read(500_001)
    if len(data) > 500_000 or b'<!DOCTYPE' in data.upper():
        raise ValueError('Unexpected feed format')
    items = []
    for entry in ET.fromstring(data).findall('./channel/item')[:5]:
        title = unescape(entry.findtext('title', '')).strip()[:240]
        link = entry.findtext('link', '').strip()
        source = entry.findtext('source', '').strip()[:100]
        published = entry.findtext('pubDate', '').strip()[:80]
        if title and link.startswith('https://news.google.com/'):
            items.append((title, link, source, published))
    return items
