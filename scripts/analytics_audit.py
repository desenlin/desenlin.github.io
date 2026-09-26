"""Check source coverage and discover published HTML pages; no GA credentials needed."""
import argparse, fnmatch, json, os, re, sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit, unquote
from urllib.request import Request, urlopen

ALLOWED_HOSTS={'desenlin.com','linguistics-teaching-labs.github.io'}
SKIP_DIRS={'.git','node_modules','__pycache__','_site','dist','build','vendor'}

class Page(HTMLParser):
    def __init__(self,text):
        super().__init__();self.scripts=[];self.links=[];self.title='';self.in_title=False;self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='script':self.scripts.append(a)
        if tag=='a' and a.get('href'):self.links.append(a['href'])
        if tag=='title':self.in_title=True
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
    def handle_data(self,data):
        if self.in_title:self.title+=data

def issues(text,mid,require_tracker=True):
    text=re.sub(r'\{\{\s*[\"\']([^\"\']+)[\"\']\s*\|\s*relative_url\s*\}\}',r'\1',text)
    errors=[];p=Page(text)
    trackers=[s for s in p.scripts if s.get('src','').split('?')[0].endswith('/analytics.js') or s.get('src')=='analytics.js']
    trackers=[s for s in trackers if 'google-analytics.com' not in s.get('src','')]
    google=[s for s in p.scripts if 'googletagmanager.com/gtag/js' in s.get('src','')]
    if re.search(r'google-analytics\.com/analytics\.js|\bga\(\s*[\"\']create',text):errors.append('Legacy Universal Analytics code is incompatible with GA4.')
    if require_tracker and len(trackers)!=1:errors.append(f'Expected one shared analytics script; found {len(trackers)}.')
    for s in trackers:
        if s.get('data-ga-id')!=mid:errors.append('Shared tracker has the wrong or missing measurement ID.')
        if not s.get('data-project'):errors.append('Shared tracker is missing data-project.')
        if 'defer' not in s:errors.append('Shared tracker must use defer so it can detect existing GA4 initialization.')
    if len(google)>1:errors.append('Multiple Google tag loaders can duplicate measurement.')
    ids=set(re.findall(r'G-[A-Z0-9]{6,}',text))
    if ids and ids!={mid}:errors.append('Unexpected measurement ID: '+', '.join(sorted(ids)))
    # Existing inline GA4 is supported; the shared script configures only when gtag does not exist.
    configs=re.findall(r'gtag\(\s*[\"\']config[\"\']\s*,\s*[\"\']'+re.escape(mid),text)
    if len(configs)>1:errors.append('Multiple inline GA4 config calls can duplicate page views.')
    return errors

def config_at(root):
    cfg=json.loads((root/'.analytics.json').read_text())
    u=urlsplit(cfg['site_url'])
    if u.scheme!='https' or u.hostname not in ALLOWED_HOSTS or u.query or u.fragment:raise ValueError('site_url must be an approved public HTTPS site without parameters.')
    if not re.fullmatch(r'G-[A-Z0-9]+',cfg['measurement_id']):raise ValueError('Invalid measurement_id.')
    if not cfg['site_url'].endswith('/'):raise ValueError('site_url must end with /.')
    for pattern,reason in cfg.get('exclude',{}).items():
        if not str(reason).strip():raise ValueError('Every exclusion needs a documented reason: '+pattern)
    return cfg

def excluded(path,cfg):return any(fnmatch.fnmatch(path,p) for p in cfg.get('exclude',{}))
def clean(url):
    u=urlsplit(url);return urlunsplit((u.scheme,u.netloc,u.path or '/', '', ''))

def source(root,cfg):
    failures=[];paths=set();count=0
    def check(label,text):
        nonlocal count
        count+=1;failures.extend(f'{label}: {e}' for e in issues(text,cfg['measurement_id']))
    tracker=(root/cfg['tracker']).resolve()
    if not tracker.is_relative_to(root.resolve()) or not tracker.is_file():failures.append('Missing repository-owned shared tracker: '+cfg['tracker'])
    else:
        content=tracker.read_text()
        for marker in ['window.top !== window.self','activity_start','lab_launch','event.isTrusted',"typeof window.gtag !== 'function'"]:
            if marker not in content:failures.append('Shared tracker is missing safeguard/event: '+marker)
    for f in root.rglob('*.html'):
        relative=f.relative_to(root)
        if any(p in SKIP_DIRS for p in relative.parts) or excluded(relative.as_posix(),cfg):continue
        text=f.read_text(encoding='utf-8')
        check(relative.as_posix(),text)
        name=relative.as_posix()
        if cfg['mode']=='react' and name.startswith('public/'):name=name[7:]
        paths.add(name)
    mode=cfg['mode']
    if mode=='jekyll':
        layout=(root/'_layouts/default.html').read_text()
        if 'include head-custom.html' not in layout:failures.append('Jekyll default layout does not include head-custom.html.')
        check('_includes/head-custom.html',(root/'_includes/head-custom.html').read_text())
        paths.add('')
    elif mode=='quarto':
        quarto=(root/'_quarto.yml').read_text()
        if not re.search(r'google-analytics:\s*[\"\']?'+re.escape(cfg['measurement_id']),quarto):failures.append('Quarto global GA4 ID is missing or incorrect.')
        if 'include-after-body: includes/analytics-events.html' not in quarto:failures.append('Quarto analytics include is missing.')
        check('includes/analytics-events.html',(root/'includes/analytics-events.html').read_text())
        for f in root.rglob('*.qmd'):
            rel=f.relative_to(root).as_posix()
            if excluded(rel,cfg) or any(p in SKIP_DIRS for p in f.relative_to(root).parts):continue
            text=f.read_text()
            if re.search(r'google-analytics\s*:|include-after-body\s*:',text):failures.append(rel+': page-level analytics override needs review.')
            paths.add(rel[:-4]+'.html')
    elif mode=='react':
        layout=(root/'app/layout.tsx').read_text()
        if cfg['measurement_id'] not in layout or 'data-ga-id={GOOGLE_ANALYTICS_ID}' not in layout or '/analytics.js' not in layout:failures.append('React root layout is missing the expected tracker or measurement ID.')
        paths.add('')
    if not paths:failures.append('No public HTML pages were discovered.')
    for item in cfg.get('smoke',[]):paths.add(item['path'])
    return {'source_checks':count,'urls':sorted({clean(urljoin(cfg['site_url'],p)) for p in paths}),'failures':failures}

def get_html(url):
    request=Request(url,headers={'User-Agent':'TeachingLabs-AnalyticsAudit/1.0 (GitHub Actions)'})
    with urlopen(request,timeout=25) as r:
        if urlsplit(r.url).hostname not in ALLOWED_HOSTS:raise ValueError('Unexpected redirect destination: '+r.url)
        if 'text/html' not in r.headers.get('Content-Type',''):raise ValueError('Expected an HTML page.')
        return r.read().decode('utf-8'),clean(r.url)

def live(cfg,manifest):
    pending=list(manifest['urls']);seen=set();pages=[];failures=[]
    base=urlsplit(cfg['site_url']);limit=200
    while pending:
        url=pending.pop(0)
        if url in seen:continue
        seen.add(url)
        if len(seen)>limit:failures.append('Discovery exceeded 200 pages; increase the reviewed limit instead of silently skipping pages.');break
        try:
            html,final=get_html(url)
            errors=issues(html,cfg['measurement_id'])
            pages.append({'url':final,'title':Page(html).title,'errors':errors})
            failures.extend(f'{final}: {e}' for e in errors)
            for href in Page(html).links:
                candidate=clean(urljoin(final,href));u=urlsplit(candidate)
                if u.scheme!='https' or u.hostname!=base.hostname:continue
                # The academic-site audit follows new same-domain tools automatically.
                if not u.path.startswith(base.path):continue
                if any(part.startswith('.') for part in unquote(u.path).split('/')):continue
                if not (u.path.endswith('/') or u.path.endswith('.html')):continue
                if candidate not in seen and candidate not in pending:pending.append(candidate)
        except Exception as e:failures.append(f'{url}: {e}')
    return {'pages':pages,'urls':sorted({p['url'] for p in pages}),'failures':failures}

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['source','live']);p.add_argument('--root',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);a=p.parse_args()
    cfg=config_at(a.root)
    report=source(a.root,cfg) if a.mode=='source' else live(cfg,json.loads(a.manifest.read_text()))
    a.manifest.write_text(json.dumps(report,indent=2)+'\n')
    summary=f"### Analytics {a.mode} audit\n\nProject: `{cfg['project']}` · Measurement ID: `{cfg['measurement_id']}`\n\nDiscovered {len(report['urls'])} pages; {len(report['failures'])} failures.\n"
    if report['failures']:summary+='\n'+'\n'.join('- '+x for x in report['failures'])+'\n'
    print(summary)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write(summary)
    for error in report['failures']:print('::error::'+error.replace('\n',' '))
    return bool(report['failures'])
if __name__=='__main__':sys.exit(main())
