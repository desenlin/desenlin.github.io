"""Generate static Chinese counterparts from the current rendered English pages.

English remains the only layout/content source. Reviewed translations override a
source-text-keyed machine cache; changed text cannot silently reuse an old entry.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import posixpath
import re
import shutil
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup, Comment, NavigableString

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
CACHE = ROOT / ".cache" / "i18n"
ORIGIN = "https://desenlin.com"
PROTECTED = (
    "script, style, code, pre, svg, math, [translate=no], .notranslate, "
    ".paper-card h3, .paper-authors, .paper-venue-line, .paper-meta-items, "
    ".citation-dialog p, .summary-citation, .research-summary-page h1.title, "
    ".navbar-brand, .contact-address, .course-code, .course-collection-code"
)
RETAIN = {
    "Desen Lin", "Wei Lai", "Wei Lai and Desen Lin", "Housing Market Lab",
    "Linguistics Teaching Labs", "Nature of Language Lab",
    "Computational Linguistics Lab", "Site Feasibility Sandbox", "Ame Quarter",
    "Google Scholar", "SSRN", "ORCID", "LinkedIn", "© Desen Lin",
}
ATTRS = ("alt", "title", "aria-label", "placeholder")


def normalize(text):
    return re.sub(r"\s+", " ", str(text)).strip()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pages():
    # Only Quarto-generated academic pages; never clone assets or linked labs.
    found = {}
    for path in sorted(SITE.rglob("*.html")):
        relative = path.relative_to(SITE)
        if any(part in relative.parts for part in ("zh", "docs", "site_libs")):
            continue
        if path.name in {"LICENSE.html", "CONTRIBUTING.html", "README.html"}:
            continue
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        generator = soup.find("meta", attrs={"name": "generator"})
        if generator and generator.get("content", "").startswith("quarto-"):
            found[relative.as_posix()] = soup
    return found


def protect(soup):
    for tag in soup.select(PROTECTED):
        tag["translate"] = "no"
    # Research summary titles are also paper titles, including social metadata.
    if soup.select_one(".research-summary-page"):
        for tag in soup.select('title, meta[property="og:title"], meta[name="twitter:title"]'):
            tag["data-i18n-protected"] = "true"


def blocked(tag):
    while tag and getattr(tag, "name", None):
        if tag.get("translate") == "no" or tag.get("data-i18n-protected"):
            return True
        if tag.name in {"script", "style", "code", "pre", "svg", "math"}:
            return True
        tag = tag.parent
    return False


def eligible(text):
    text = normalize(text)
    return bool(re.search(r"[A-Za-z]", text)) and text not in RETAIN and not re.match(r"^(https?://|\S+@\S+)", text)


def units(soup):
    for node in soup.find_all(string=True):
        if type(node) is not NavigableString or not node.parent or blocked(node.parent):
            continue
        if eligible(node):
            yield node, None, normalize(node)
    for tag in soup.find_all(True):
        if blocked(tag):
            continue
        for attr in ATTRS:
            if tag.get(attr) and eligible(tag[attr]):
                yield tag, attr, normalize(tag[attr])
        if tag.name == "meta" and (tag.get("name") in {"description", "twitter:title", "twitter:description"}
                                    or tag.get("property") in {"og:title", "og:description"}):
            if eligible(tag.get("content", "")):
                yield tag, "content", normalize(tag["content"])


def translated_soup(source, memory):
    soup = copy.deepcopy(source)
    for node, attr, text in list(units(soup)):
        translated = memory[text]
        if attr:
            node[attr] = translated
        else:
            raw = str(node)
            # Preserve boundaries around inline links/emphasis.
            before = re.match(r"^\s*", raw).group()
            after = re.search(r"\s*$", raw).group()
            node.replace_with(NavigableString(before + translated + after))
    soup.html["lang"] = "zh-CN"
    soup.html["xml:lang"] = "zh-CN"
    soup.html["data-site-language"] = "zh"
    if soup.body:
        soup.body["class"] = soup.body.get("class", []) + ["chinese-page"]
    for tag in soup.select('meta[property="og:locale"]'):
        tag["content"] = "zh_CN"
    return soup


def rewrite_url(value, page, available, chinese, navigation=False):
    if not value or value.startswith(("#", "data:", "mailto:", "tel:", "javascript:")):
        return value
    parts = urlsplit(urljoin(ORIGIN + "/" + page, value))
    if parts.netloc not in {"desenlin.com", "www.desenlin.com"}:
        return value
    path = parts.path
    candidate = path.lstrip("/")
    if not candidate or path.endswith("/"):
        candidate += "index.html"
    elif "." not in candidate.rsplit("/", 1)[-1]:
        candidate += ".html"
    if chinese and navigation and candidate in available:
        path = "/zh/" + candidate
    return urlunsplit(("", "", path, parts.query, parts.fragment))


def navigation(soup, page, available, chinese):
    for tag in soup.find_all(True):
        for attr in ("href", "src", "poster", "data-src", "action"):
            if tag.get(attr):
                tag[attr] = rewrite_url(tag[attr], page, available, chinese, tag.name == "a" and attr == "href")
        if tag.get("srcset"):
            tag["srcset"] = ", ".join(
                " ".join([rewrite_url(item.strip().split()[0], page, available, chinese)] + item.strip().split()[1:])
                for item in tag["srcset"].split(",")
            )
    own = ORIGIN + ("/zh/" if chinese else "/") + page
    for tag in soup.select('link[rel="canonical"], link[hreflang]'):
        tag.decompose()
    soup.head.append(soup.new_tag("link", rel="canonical", href=own))
    for lang, prefix in (("en", "/"), ("zh-CN", "/zh/"), ("x-default", "/")):
        soup.head.append(soup.new_tag("link", rel="alternate", hreflang=lang, href=ORIGIN + prefix + page))
    for tag in soup.select('meta[property="og:url"], meta[name="twitter:url"]'):
        tag["content"] = own
    for tag in soup.select(".site-language-switch"):
        tag.decompose()
    switch = soup.new_tag("a", href=("/" if chinese else "/zh/") + page)
    switch["class"] = ["site-language-switch"]
    switch["lang"] = "en" if chinese else "zh-CN"
    switch["hreflang"] = switch["lang"]
    switch["aria-label"] = "Read this page in English" if chinese else "阅读此页中文版"
    switch["data-analytics-event"] = "language_switch"
    switch["data-analytics-location"] = "navbar"
    switch.string = "EN" if chinese else "中文"
    theme = soup.select_one(".quarto-color-scheme-toggle")
    if theme:
        theme.insert_before(switch)
    else:
        navbar = soup.select_one(".navbar-container")
        if navbar:
            navbar.append(switch)
    # Retain the current fragment when switching languages; no automatic redirect.
    if not soup.select_one('script[src="/assets/language-switch.js"]'):
        script = soup.new_tag("script", src="/assets/language-switch.js", defer="")
        soup.body.append(script)
    if not soup.select_one('link[href="/assets/chinese-font.css"]'):
        soup.head.append(soup.new_tag("link", rel="stylesheet", href="/assets/chinese-font.css"))


def build_fonts(documents):
    from fontTools import subset
    from fontTools.ttLib import TTFont
    from urllib.request import urlopen

    CACHE.mkdir(parents=True, exist_ok=True)
    source = CACHE / "noto-serif-sc.ttf"
    if not source.exists():
        url = "https://raw.githubusercontent.com/google/fonts/2e61f4355afd22b801791b0df176065082423b87/ofl/notoserifsc/NotoSerifSC%5Bwght%5D.ttf"
        with urlopen(url, timeout=90) as response:
            source.write_bytes(response.read())
    names = set("林的森中文")
    chars = names | {c for html in documents for c in html if "\u3000" <= c <= "\u9fff" or "\uff00" <= c <= "\uffef"}
    destination = SITE / "assets"
    destination.mkdir(exist_ok=True)
    css = []
    for label, glyphs in (("name", names), ("text", chars - names)):
        if not glyphs:
            continue
        digest = hashlib.sha256("".join(sorted(glyphs)).encode()).hexdigest()[:12]
        filename = f"noto-serif-sc-{label}-{digest}.woff2"
        font = TTFont(source)
        options = subset.Options()
        options.flavor = "woff2"
        subsetter = subset.Subsetter(options=options)
        subsetter.populate(text="".join(sorted(glyphs)))
        subsetter.subset(font)
        font.flavor = "woff2"
        font.save(destination / filename)
        ranges = ",".join(f"U+{ord(c):X}" for c in sorted(glyphs))
        css.append('@font-face {font-family:"Noto Serif SC Site";font-style:normal;'
                   'font-weight:200 900;font-display:swap;'
                   f'src:url("/assets/{filename}") format("woff2");unicode-range:{ranges};}}')
    (destination / "chinese-font.css").write_text("\n".join(css), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--auto", action="store_true", help="Translate uncached text with the local CPU model")
    args = parser.parse_args()
    sources = pages()
    if not sources:
        raise SystemExit("No rendered academic pages found. Run quarto render first.")
    required = set()
    for soup in sources.values():
        protect(soup)
        required.update(text for _, _, text in units(soup))
    overrides = load_json(ROOT / "translations" / "zh-CN.json")
    machine = load_json(CACHE / "machine.json")
    memory = {**machine, **overrides}
    missing = sorted(required - memory.keys())
    write_json(CACHE / "missing.json", missing)
    if args.extract:
        print(f"{len(sources)} pages; {len(required)} unique text segments; {len(missing)} need translation.")
        return
    if missing and args.auto:
        from translate_new_text import translate
        machine.update(translate(missing))
        write_json(CACHE / "machine.json", machine)
        memory = {**machine, **overrides}
    elif missing:
        raise SystemExit(f"{len(missing)} untranslated segments. See .cache/i18n/missing.json or use --auto.")
    generated = {}
    for page, english in sources.items():
        chinese = translated_soup(english, memory)
        navigation(chinese, page, sources, True)
        navigation(english, page, sources, False)
        generated[page] = str(english)
        generated["zh/" + page] = str(chinese)
    # Complete translation and font generation before replacing any output.
    build_fonts(list(generated.values()))
    shutil.copyfile(ROOT / "assets" / "language-switch.js", SITE / "assets" / "language-switch.js")
    shutil.copyfile(ROOT / "translations" / "NotoSerifSC-OFL.txt", SITE / "assets" / "NotoSerifSC-OFL.txt")
    for page, html in generated.items():
        destination = SITE / page
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(html, encoding="utf-8")
    report = {"pages": len(sources), "segments": len(required), "reviewed": len(required & overrides.keys()),
              "automatic": len(required - overrides.keys()), "new_automatic": len(missing),
              "source_commit": os.getenv("GITHUB_SHA", "local")}
    write_json(CACHE / "report.json", report)
    # Keep an inspectable translation memory with each deployment, not in browser bundles.
    write_json(CACHE / "used-translations.json", {s: memory[s] for s in sorted(required)})
    import xml.etree.ElementTree as ET
    sitemap = SITE / "sitemap.xml"
    if sitemap.exists():
        ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
        ET.register_namespace("", ns)
        tree = ET.parse(sitemap)
        root = tree.getroot()
        for node in list(root):
            loc = node.find(f"{{{ns}}}loc")
            if loc is not None and loc.text and "/zh/" in loc.text:
                root.remove(node)
        for page in sources:
            node = ET.SubElement(root, f"{{{ns}}}url")
            ET.SubElement(node, f"{{{ns}}}loc").text = ORIGIN + "/zh/" + page
        tree.write(sitemap, encoding="utf-8", xml_declaration=True)
    print(json.dumps(report))


if __name__ == "__main__":
    main()
