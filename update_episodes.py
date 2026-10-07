#!/usr/bin/env python3
"""Rewrites the episode list in index.html from the Buzzsprout RSS feed.
Usage: python3 update_episodes.py [index.html]   (standard library only)"""
import re, sys, html, urllib.request
import xml.etree.ElementTree as ET

FEED = "https://feeds.buzzsprout.com/2464832.rss"
FALLBACK_LINK = "https://www.buzzsprout.com/2464832"
COUNT = 6
path = sys.argv[1] if len(sys.argv) > 1 else "index.html"
src = sys.argv[2] if len(sys.argv) > 2 else FEED

def read(u):
    if u.startswith("http"):
        req = urllib.request.Request(u, headers={"User-Agent": "ocp-site-builder"})
        return urllib.request.urlopen(req, timeout=30).read()
    return open(u, "rb").read()

root = ET.fromstring(read(src))
ns = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}
rows = []
for item in root.findall("./channel/item")[:COUNT]:
    raw = item.findtext("title", "")
    title = re.sub(r"\s*\|\s*(the\s+)?off-court podcast.*$", "", raw, flags=re.I).strip()
    m = re.search(r"ep\.?\s*(\d+)", raw, re.I)
    num = m.group(1) if m else (item.findtext("itunes:episode", "", ns) or "")
    desc = re.sub(r"<[^>]+>", " ", html.unescape(item.findtext("description", "")))
    desc = re.sub(r"\s+", " ", html.unescape(desc)).strip()
    if len(desc) > 160:
        desc = desc[:157].rstrip() + "..."
    link = item.findtext("link", "") or FALLBACK_LINK
    e = lambda s: html.escape(s, quote=True)
    rows.append(
        f'<li><span class="ep">{e("ep."+num) if num else "new"}</span>'
        f'<div><h3>{e(title)}</h3>{"<p>"+e(desc)+"</p>" if desc else ""}</div>'
        f'<a class="btn ink" href="{e(link)}">play</a></li>')
if not rows:
    sys.exit("no episodes found; leaving index.html unchanged")

page = open(path, encoding="utf-8").read()
new = re.sub(r"<!--eps-->.*?<!--/eps-->", lambda _: "<!--eps-->\n" + "\n".join(rows) + "\n<!--/eps-->", page, flags=re.S)
if new != page:
    open(path, "w", encoding="utf-8").write(new)
    print(f"updated {len(rows)} episodes")
else:
    print("no changes")
