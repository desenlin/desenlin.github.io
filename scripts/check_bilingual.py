"""Check the generated deployment, including user-specified research exclusions."""
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from build_bilingual import SITE, pages


def main():
    checked = 0
    for name, english in pages().items():
        target = SITE / 'zh' / name
        assert target.exists(), f'Missing counterpart: {name}'
        chinese = BeautifulSoup(target.read_text(encoding='utf-8'), 'html.parser')
        assert chinese.html['lang'] == 'zh-CN', name
        assert chinese.select_one('.site-language-switch')['href'] == '/' + name, name
        assert english.select_one('.site-language-switch')['href'] == '/zh/' + name, name
        for selector in ('.paper-card h3', '.paper-meta-items', '.paper-authors', '.paper-venue-line', '.citation-dialog p', '.summary-citation', '.research-summary-page h1.title'):
            assert [n.get_text() for n in english.select(selector)] == [n.get_text() for n in chinese.select(selector)], f'Protected text changed: {name}: {selector}'
        assert chinese.select_one('script[data-ga-id="G-MDGMSFPEH2"]'), f'Analytics missing: {name}'
        assert chinese.select_one('link[rel="canonical"]')['href'].endswith('/zh/' + name), name
        for node in chinese.select('[src], link[rel="stylesheet"], a[href]'):
            value = node.get('src') or node.get('href') or ''
            url = urlsplit(value)
            if url.scheme or url.netloc or not url.path.startswith('/'):
                continue
            path = SITE / url.path.lstrip('/')
            # Other repositories share the domain and are intentionally not copied.
            if not path.exists() and not url.path.startswith(('/zh/', '/assets/', '/images/', '/site_libs/', '/files/')):
                continue
            assert path.exists(), f'Broken local resource: {name}: {value}'
            if url.fragment and path.suffix == '.html':
                linked = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
                assert linked.find(id=url.fragment), f'Broken fragment: {name}: {value}'
        checked += 1
    assert checked >= 5, 'Main academic pages missing'
    print(f'Validated {checked} Chinese counterparts, language links, shared assets, analytics, and protected research records.')


if __name__ == '__main__':
    main()
