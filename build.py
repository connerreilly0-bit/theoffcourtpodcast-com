#!/usr/bin/env python3
"""Builds the whole site (home page, episode pages, episode index, sitemap) from the Buzzsprout RSS feed.
Usage: python3 build.py            (standard library only)"""
import re, sys, html, json, unicodedata, urllib.request, os
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

SITE = "https://theoffcourtpodcast.com"
FEED = sys.argv[1] if len(sys.argv) > 1 else "https://feeds.buzzsprout.com/2464832.rss"
SPOTIFY = "https://open.spotify.com/show/7K8ZXKIw15ZVin1MAzqve6"
APPLE = "https://podcasts.apple.com/podcast/id1804946867"
AMAZON = "https://music.amazon.com/podcasts/bb8f5b55-9da3-4487-9781-a4cc73624628"
ALLAPPS = "https://www.buzzsprout.com/2464832/follow"
YOUTUBE = "https://www.youtube.com/@TheOff-CourtPodcast"
INSTA = "https://www.instagram.com/theoffcourtpodcast/"
TIKTOK = "https://www.tiktok.com/@theoffcourtpodcast"
EMAIL = "theoffcourtpodcast@gmail.com"
NS = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd", "content": "http://purl.org/rss/1.0/modules/content/"}
E = lambda s: html.escape(s or "", quote=True)

def read(u):
    if u.startswith("http"):
        return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "ocp-site-builder"}), timeout=30).read()
    return open(u, "rb").read()

def trunc(s, n):
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= n: return s
    return s[:n].rsplit(" ", 1)[0].rstrip(" ,.;:-") + "..."

def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60].strip("-")

def paras(raw):
    s = re.sub(r"<br\s*/?>", "\n", raw or "", flags=re.I)
    s = re.sub(r"</(p|div|ul|ol)>", "\n\n", s, flags=re.I)
    s = re.sub(r"<li[^>]*>", "\n- ", s, flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    out = [re.sub(r"[ \t]+", " ", p).strip() for p in re.split(r"\n\s*\n", s)]
    return [p for p in out if p]

def linkify(p):
    t = E(p).replace("\n", "<br>")
    return re.sub(r'(https?://[^\s<]+?)([.,;:!?)]*)(?=\s|<|$)', r'<a href="\1" rel="noopener">\1</a>\2', t)

def load():
    root = ET.fromstring(read(FEED))
    eps = []
    for it in root.findall("./channel/item"):
        raw = it.findtext("title", "")
        title = re.sub(r"\s*\|\s*(the\s+)?off-court podcast.*$", "", raw, flags=re.I).strip()
        num = it.findtext("itunes:episode", "", NS) or ((re.search(r"ep\.?\s*(\d+)", raw, re.I) or [None, ""])[1])
        body = it.findtext("content:encoded", "", NS) or it.findtext("description", "")
        enc = it.find("enclosure")
        try: dt = parsedate_to_datetime(it.findtext("pubDate", ""))
        except Exception: dt = None
        ps = paras(body)
        slug = (num + "-" if num else "") + slugify(title)
        eps.append(dict(title=title, num=num, paras=ps, dt=dt, audio=enc.get("url") if enc is not None else "", slug=slug.strip("-"),
                        blurb=trunc(ps[0] if ps else title, 160), meta=trunc(ps[0] if ps else title, 155)))
    if not eps: sys.exit("no episodes found; nothing changed")
    return eps

def date_s(e): return e["dt"].strftime("%-d %B %Y").lower() if e["dt"] else ""
def url(e): return f"/episodes/{e['slug']}/"
def label(e): return f"ep.{e['num']}" if e["num"] else "new"

CSS = """
:root{--blue:#0080ff;--navy:#0d193d;--paper:#fff;--ink:#0d193d;--soft:#eaf3ff;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0d193d;--ink:#fff;--soft:#122254}}
:root[data-theme="dark"]{--paper:#0d193d;--ink:#fff;--soft:#122254}
html{scroll-padding-top:env(safe-area-inset-top,0px);scroll-behavior:smooth}
*,*::before,*::after{box-sizing:inherit}
body{margin:0;overflow-x:clip;font-family:"Space Grotesk",system-ui,sans-serif;background:var(--paper);color:var(--ink);text-transform:lowercase;line-height:1.5;font-size:18px}
a{color:inherit}
:focus-visible{outline:3px solid #ffd84d;outline-offset:3px}
.wrap{max-width:1120px;margin:0 auto;padding:0 24px}
.blue{background:var(--blue);color:#fff}.navy{background:var(--navy);color:#fff}
header.over{position:absolute;inset:0 0 auto 0;z-index:2}
nav{display:flex;justify-content:space-between;align-items:center;padding:20px 0;font-weight:500}
nav a{text-decoration:none;margin-left:24px}nav a:hover{text-decoration:underline;text-underline-offset:5px}nav a.brand{margin:0;font-weight:700}
.hero{position:relative;overflow:hidden;padding:120px 0 72px;min-height:92vh;display:flex;align-items:center}
.hero .wrap{display:grid;grid-template-columns:1.6fr 1fr;gap:32px;align-items:center;width:100%}
h1{font-size:clamp(3.4rem,11vw,9rem);line-height:.88;letter-spacing:-.045em;margin:0 0 28px;font-weight:700}
h1 span{display:block}h1 .the{font-weight:300}
.sub{max-width:34ch;font-size:1.25rem;margin:0 0 32px}
.mascot{width:100%;max-width:340px;justify-self:center;transform-origin:50% 100%;animation:bob 1.1s cubic-bezier(.3,1.6,.5,1) .2s both}
@keyframes bob{from{transform:translateY(60px) rotate(-8deg);opacity:0}to{transform:none;opacity:1}}
.btns{display:flex;flex-wrap:wrap;gap:10px}
.btn{display:inline-block;padding:12px 22px;border:2px solid currentColor;border-radius:999px;text-decoration:none;font-weight:600;transition:background .15s,color .15s}
.btn:hover{background:#fff;color:var(--blue)}
.btn.solid{background:#fff;color:var(--blue);border-color:#fff}.btn.solid:hover{background:transparent;color:#fff}
.btn.ink:hover{background:var(--ink);color:var(--paper)}
section{padding:96px 0}
h2{font-size:clamp(2rem,5vw,3.4rem);letter-spacing:-.035em;line-height:1;margin:0 0 40px;font-weight:700}
.eps{list-style:none;margin:0;padding:0;border-top:2px solid var(--ink)}
.eps li{display:grid;grid-template-columns:90px 1fr auto;gap:20px;align-items:center;padding:26px 0;border-bottom:2px solid var(--ink)}
.eps .ep{font-size:2.2rem;font-weight:700;color:var(--blue);letter-spacing:-.04em}
.eps h3{margin:0 0 4px;font-size:1.3rem;line-height:1.2;font-weight:600}
.eps h3 a{text-decoration:none}.eps h3 a:hover{text-decoration:underline;text-underline-offset:4px}
.eps p{margin:0;opacity:.75;font-size:1rem;text-transform:none}
.more{margin-top:28px}
.hosts{display:grid;grid-template-columns:1fr 1.1fr;gap:56px;align-items:center}
.hosts img{width:100%;height:auto;border-radius:24px;display:block;border:3px solid #fff}
.hosts p{margin:0 0 18px;max-width:52ch}
.hosts .lead{font-size:1.5rem;line-height:1.3;font-weight:500}
.listen{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.listen a{display:flex;justify-content:space-between;padding:20px 22px;border:2px solid #fff;border-radius:18px;text-decoration:none;font-weight:600;font-size:1.15rem;transition:background .15s,color .15s}
.listen a:hover{background:#fff;color:var(--blue)}
.ep-page{padding-top:56px;padding-bottom:80px}
.crumb{display:inline-block;margin-bottom:28px;text-decoration:none;font-weight:600}
.meta{color:var(--blue);font-weight:700;font-size:1.1rem;margin:0 0 12px}
.ep-page h1{overflow-wrap:anywhere;font-size:clamp(2.2rem,6vw,4rem);line-height:1;letter-spacing:-.04em;margin:0 0 28px}
audio{width:100%;margin:0 0 28px}
.prose{overflow-wrap:anywhere;max-width:68ch;text-transform:none;font-size:1.1rem}.prose p{margin:0 0 1.1em}
.prose a{color:var(--blue)}
.ep-page .btns{margin:8px 0 48px}.ep-page .btn{color:var(--blue)}.ep-page .btn:hover{background:var(--blue);color:#fff}
.ep-page h2{font-size:1.8rem;margin:56px 0 20px}
footer{padding:48px 0 40px}
footer .wrap{display:flex;flex-wrap:wrap;gap:24px;justify-content:space-between;align-items:center}
footer img{height:64px;width:auto}
footer p a{margin:0}
@media (max-width:760px){
.hero{padding-top:100px}.hero .wrap,.hosts{grid-template-columns:1fr}.hosts{gap:32px}
.mascot{max-width:200px;grid-row:1;justify-self:start}
.eps li{grid-template-columns:1fr;gap:10px}
nav a:not(.brand){display:none}nav a.keep{display:inline}
section{padding:64px 0}}
@media (prefers-reduced-motion:reduce){.mascot{animation:none}html{scroll-behavior:auto}}
"""

NAV = '<nav><a class="brand" href="/">the off-court podcast</a><span><a href="/episodes/">episodes</a><a href="/#about">hosts</a><a href="/#partner">partner</a><a class="keep" href="/#listen">listen</a></span></nav>'
FOOT = f'''<footer class="navy"><div class="wrap"><img src="/mascot.png" alt="" width="40" height="64">
<p style="margin:0;display:flex;flex-wrap:wrap;gap:6px 20px"><a href="mailto:{EMAIL}">{EMAIL}</a><a href="{INSTA}">@theoffcourtpodcast</a></p>
<p style="margin:0;opacity:.7">&copy; 2026 the off-court podcast</p></div></footer>'''

def page(title, desc, path, body, ld, over=False, og_type="website"):
    canon = SITE + path
    ldh = "".join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False).replace("</", "<\\/") + "</script>" for x in ld)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canon}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="the off-court podcast">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{canon}">
<meta property="og:image" content="{SITE}/og-image.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="/favicon.png"><link rel="apple-touch-icon" href="/favicon.png">
<link rel="alternate" type="application/rss+xml" title="the off-court podcast" href="https://feeds.buzzsprout.com/2464832.rss">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300..700&display=swap">
<style>{CSS}</style>{ldh}</head><body>
<header class="blue{' over' if over else ''}"{' style="background:none"' if over else ''}><div class="wrap">{NAV}</div></header>
{body}
{FOOT}
</body></html>'''

SERIES = {"@type": "PodcastSeries", "name": "The Off-Court Podcast", "url": SITE + "/"}

def ep_li(e):
    p = f"<p>{E(e['blurb'])}</p>" if e["blurb"] else ""
    return f'<li><span class="ep">{E(label(e))}</span><div><h3><a href="{url(e)}">{E(e["title"])}</a></h3>{p}</div><a class="btn ink" href="{url(e)}">listen</a></li>'

def build_home(eps):
    lis = "\n".join(ep_li(e) for e in eps[:6])
    body = f'''<main id="top">
<div class="hero blue"><div class="wrap"><div>
<h1><span class="the">the</span><span>off-court</span><span>podcast</span></h1>
<p class="sub">the padel podcast covering all your padel needs. hosted by conner reilly &amp; hug hernandez.</p>
<div class="btns"><a class="btn solid" href="{SPOTIFY}">listen on spotify</a><a class="btn" href="{APPLE}">apple podcasts</a><a class="btn" href="{YOUTUBE}">watch on youtube</a></div></div>
<img class="mascot" src="/mascot.png" width="435" height="700" alt="the off-court podcast mascot: a smiling padel racket wearing an ocp cap"></div></div>
<section id="episodes"><div class="wrap"><h2>latest padel podcast episodes</h2><ul class="eps">
{lis}
</ul><p class="more"><a class="btn ink" href="/episodes/">all episodes</a></p></div></section>
<section id="about" class="blue"><div class="wrap"><h2>the english-speaking padel podcast</h2><div class="hosts">
<img src="/hosts.jpg" width="900" height="900" alt="conner reilly and hug hernandez, hosts of the off-court podcast, at the studio table with microphones" loading="lazy">
<div><p class="lead">we're conner and hug: two padel lovers bringing weekly, engaging padel content to the english-speaking padel community.</p>
<p>padel is a mostly spanish-speaking sport, so a lot gets missed. we're here to bridge that gap with tournament reviews, news on pairings and players, game analysis and conversations with the people who make the sport.</p>
<p>we started after becoming obsessed with a sport that seemed impossible to stop talking about, and we exist to cover padel in a way that feels authentic to the people who play it, follow it and care about where it's heading.</p></div></div></div></section>
<section id="partner" class="navy"><div class="wrap"><h2>partner with us</h2>
<p class="sub" style="max-width:48ch">brands, events and padel businesses: we reach a growing, engaged padel audience across the podcast, instagram and tiktok. get in touch to work together.</p>
<a class="btn" href="mailto:{EMAIL}">partner with us</a></div></section>
<section id="listen" class="blue"><div class="wrap"><h2>listen to the padel podcast</h2><div class="listen">
<a href="{SPOTIFY}">spotify <span aria-hidden="true">&nearr;</span></a><a href="{APPLE}">apple podcasts <span aria-hidden="true">&nearr;</span></a>
<a href="{AMAZON}">amazon music <span aria-hidden="true">&nearr;</span></a><a href="{ALLAPPS}">other podcast apps <span aria-hidden="true">&nearr;</span></a>
<a href="{YOUTUBE}">youtube <span aria-hidden="true">&nearr;</span></a><a href="{INSTA}">instagram <span aria-hidden="true">&nearr;</span></a>
<a href="{TIKTOK}">tiktok <span aria-hidden="true">&nearr;</span></a></div></div></section></main>'''
    ld = [{"@context": "https://schema.org", **SERIES, "description": "A padel podcast hosted by Conner Reilly and Hug Hernandez covering players, rivalries, tournaments and personalities in padel.",
           "inLanguage": "en", "genre": "Sports", "about": "Padel", "image": SITE + "/og-image.jpg", "webFeed": "https://feeds.buzzsprout.com/2464832.rss",
           "author": [{"@type": "Person", "name": "Conner Reilly"}, {"@type": "Person", "name": "Hug Hernandez"}],
           "sameAs": [SPOTIFY, APPLE, AMAZON, YOUTUBE, INSTA, TIKTOK]}]
    return page("the off-court podcast | the padel podcast for english-speaking fans",
                "the off-court podcast is a padel podcast hosted by conner reilly and hug hernandez. weekly padel news, player interviews, tournament recaps and rivalries. listen on spotify, apple podcasts and youtube.",
                "/", body, ld, over=True)

def build_ep(eps, i):
    e = eps[i]
    nb = [x for x in eps[max(0, i - 2): i + 3] if x is not e][:4]
    prose = "".join(f"<p>{linkify(p)}</p>" for p in e["paras"])
    audio = f'<audio controls preload="none" src="{E(e["audio"])}"></audio>' if e["audio"] else ""
    body = f'''<main><article class="wrap ep-page"><a class="crumb" href="/episodes/">&larr; all episodes</a>
<p class="meta">{E(label(e))}{' &middot; ' + E(date_s(e)) if date_s(e) else ''}</p><h1>{E(e["title"])}</h1>{audio}
<div class="btns"><a class="btn" href="{SPOTIFY}">spotify</a><a class="btn" href="{APPLE}">apple podcasts</a><a class="btn" href="{AMAZON}">amazon music</a><a class="btn" href="{YOUTUBE}">youtube</a><a class="btn" href="{ALLAPPS}">other apps</a></div>
<div class="prose">{prose}</div>
<h2>more padel podcast episodes</h2><ul class="eps">{"".join(ep_li(x) for x in nb)}</ul></article></main>'''
    ld = {"@context": "https://schema.org", "@type": "PodcastEpisode", "name": e["title"], "url": SITE + url(e), "description": e["meta"],
          "partOfSeries": SERIES, "inLanguage": "en"}
    if e["dt"]: ld["datePublished"] = e["dt"].date().isoformat()
    if e["num"].isdigit(): ld["episodeNumber"] = int(e["num"])
    if e["audio"]: ld["associatedMedia"] = {"@type": "AudioObject", "contentUrl": e["audio"]}
    return page(f'{e["title"]} | the off-court podcast', e["meta"], url(e), body, [ld], og_type="article")

def build_index(eps):
    body = f'''<main><div class="wrap ep-page"><h1>all padel podcast episodes</h1>
<p class="prose">every episode of the off-court podcast: tournament reviews, player interviews and padel news from conner and hug.</p>
<ul class="eps" style="margin-top:32px">{"".join(ep_li(e) for e in eps)}</ul></div></main>'''
    return page("all padel podcast episodes | the off-court podcast", "every episode of the off-court podcast: padel tournament reviews, player interviews and news from conner reilly and hug hernandez.", "/episodes/", body, [])

def write(path, s):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old != s: open(path, "w", encoding="utf-8").write(s)

eps = load()
write("index.html", build_home(eps))
write("episodes/index.html", build_index(eps))
for i, e in enumerate(eps): write(f"episodes/{e['slug']}/index.html", build_ep(eps, i))
urls = [f"  <url><loc>{SITE}/</loc></url>", f"  <url><loc>{SITE}/episodes/</loc></url>"] + \
       [f"  <url><loc>{SITE}{url(e)}</loc>" + (f"<lastmod>{e['dt'].date().isoformat()}</lastmod>" if e["dt"] else "") + "</url>" for e in eps]
write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n")
print(f"built home, episode index and {len(eps)} episode pages")
