# Chinese academic pages

The English Quarto sources remain authoritative. `Publish Quarto website` renders
English, generates static Simplified Chinese pages under `/zh/`, validates both
languages, and publishes them together after each push to `main`. Pull requests
run the same checks without deploying. The workflow can also be run manually.

The language link beside the theme control opens the corresponding page and
preserves its section anchor. Navigation within `/zh/` stays in Chinese. Shared
images, PDFs, scripts, styles, and linked lab applications use their existing
locations. The English CV PDF remains English.

## Translation scope

The build discovers academic Quarto HTML pages automatically, including newly
added pages and research summaries. Repository maintenance documents under
`docs/`, README, CONTRIBUTING, and LICENSE are outside the translation scope.
External teaching tools and lab applications are separate projects.

Translated: navigation, interface labels, page descriptions, explanatory prose,
research abstracts, and research-summary text. Retained verbatim: paper titles,
authors and affiliations in research listings, journal names, formal citations,
and the complete presentation/conference, media, and honors entries. Established
project names also remain in their original language. Use `translate="no"` on
any new element that should retain its wording.

## Automatic updates and editorial overrides

`translations/zh-CN.json` contains reviewed English-to-Chinese text pairs. Keys
are the normalized, exact English text. Changing an English segment produces a
new key; the old translation is never silently applied to revised content.
Layout, links, dates in protected records, and new research entries are always
read from the current English build.

New or changed prose without a reviewed pair is translated on the GitHub runner
using the pinned Apache-2.0 Helsinki-NLP/opus-mt-en-zh model. The model runs on CPU;
it requires no API key, hosted translation subscription, or browser-side model.
OpenCC converts output to Simplified Chinese. Exact numbers are checked; invalid
or failed translation stops publication so stale Chinese content is not silently
published. This is a consistency check, not a guarantee of semantic accuracy.
Automatic translations can still need editorial correction.

Reviewed pairs take precedence over machine output. To refine a translation,
add or edit the corresponding pair in `translations/zh-CN.json`, then commit.
No Chinese HTML needs to be edited. GitHub caches machine translations, the
model, and the font; if a cache expires it can be regenerated. The workflow's
`chinese-translation-report` artifact contains the counts and the exact active
text pairs for inspection and promotion into the reviewed dictionary.

A deployment with no new text does not install or run the translation model.
The first update with uncached text requires a model download; subsequent builds
reuse the model and unchanged translations. Models and caches are never included
in the deployed website. No workflow commits or recursive workflow triggers are
needed: Chinese HTML is part of the same Pages artifact as English HTML.

## Font

All Chinese characters use Noto Serif SC, matching the homepage Chinese name.
The build downloads a pinned upstream version, subsets its glyphs, and serves
WOFF2 files locally. The homepage-name and language-link characters have a tiny
separate subset, so English visitors do not download the full Chinese text font.
Font license: `translations/NotoSerifSC-OFL.txt` (also copied to deployed assets).

## Local checks

```bash
python -m pip install -r scripts/requirements-i18n.txt
quarto render
python scripts/build_bilingual.py --extract
# Needed only if .cache/i18n/missing.json is not empty:
python -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r scripts/requirements-i18n-machine.txt
python scripts/build_bilingual.py --auto
python -m unittest discover -s scripts/i18n-tests -v
python scripts/check_bilingual.py
```

Serve `_site/` at a web root for browser checks. Direct file opening is not
supported because shared resources use root-relative paths.
