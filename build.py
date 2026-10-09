#!/usr/bin/env python3
"""Reads portfolio.txt and writes index.html. Usage: python build.py [portfolio.txt] [index.html]"""
import sys, re, json, html
import os

src = sys.argv[1] if len(sys.argv) > 1 else "portfolio.txt"
out = sys.argv[2] if len(sys.argv) > 2 else "index.html"

# Format: "# Section" headings, "## Project title" headings, "Key: value" lines, "//" comments.
sections, cur, proj = {}, None, None
for raw in open(src, encoding="utf-8-sig").read().splitlines():
    t = raw.strip()
    if not t or t.startswith("//"): continue
    if t.startswith("##"):
        if cur == "projects":
            proj = {"title": t.lstrip("#").strip()}; sections[cur]["projects"].append(proj)
    elif t.startswith("#"):
        cur = t.lstrip("#").strip().lower(); sections[cur] = {"lines": [], "projects": []}; proj = None
    elif ":" in t and cur:
        k, v = [x.strip() for x in t.split(":", 1)]
        if not v: continue
        if proj is not None: proj[k.lower()] = v
        else: sections[cur]["lines"].append((k.lower(), v, k))

def kv(sec): return {k: v for k, v, _ in sections.get(sec, {}).get("lines", [])}
settings, profile = kv("settings"), kv("profile")

def url(v):
    if "@" in v and "://" not in v and not v.startswith("mailto:"): return "mailto:" + v
    if "://" not in v and not v.startswith(("mailto:", "#")): return "https://" + v
    return v

links = [{"label": k, "url": url(v)} for _, v, k in sections.get("links", {}).get("lines", [])]
projects = []
for p in sections.get("projects", {}).get("projects", []):
    projects.append({
        "title": p["title"], "year": p.get("year", ""), "summary": p.get("summary", ""),
        "stack": [s.strip() for s in p.get("stack", "").split(",") if s.strip()],
        "live": url(p["live"]) if p.get("live") else "", "code": url(p["source"]) if p.get("source") else "",
        "problem": p.get("problem", ""), "built": p.get("what i built", p.get("built", "")),
        "result": p.get("result", ""), "resultLabel": p.get("result label", "")})
site = {"name": profile.get("name", "Your Name"), "tagline": profile.get("tagline", ""), "links": links, "projects": projects}

# Settings -> CSS (values are validated so a typo can't break the page)
color = lambda v: v if re.fullmatch(r"#[0-9a-fA-F]{3,8}|[a-zA-Z]{3,20}", v or "") else None
mapping = {"accent colour": "--accent", "background colour": "--bg", "text colour": "--ink", "card colour": "--surface"}
css = [f"{var}:{color(settings[k])}" for k, var in mapping.items() if color(settings.get(k))]
head = []
font = settings.get("font", "")
if re.fullmatch(r"[A-Za-z0-9 ]{2,40}", font):
    head.append(f'<link href="https://fonts.googleapis.com/css2?family={font.replace(" ", "+")}:wght@400;600;800&display=swap" rel="stylesheet">')
    css.append(f'--font:"{font}",system-ui,sans-serif')
if css: head.append("<style>html:root:root:root{" + ";".join(css) + "}</style>")
if settings.get("show layout switcher", "yes").lower() not in ("yes", "y", "true"):
    head.append("<style>.bar{display:none}</style>")

scheme = settings.get("colour scheme", "auto").lower()
layout = settings.get("layout", "cards").lower()
layout = layout if layout in ("cards", "index", "cases") else "cards"

page = open("template.html", encoding="utf-8").read()
page = page.replace("/*__SITE__*/{}", json.dumps(site, ensure_ascii=False).replace("</", "<\\/"))
page = page.replace("/*__LAYOUT__*/'cards'", json.dumps(layout))
page = page.replace("<!--__HEAD__-->", "\n".join(head))
page = page.replace("__TITLE__", html.escape(settings.get("page title", site["name"])))
if scheme in ("light", "dark"): page = page.replace('<html lang="en">', f'<html lang="en" data-theme="{scheme}">')
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
open(out, "w", encoding="utf-8").write(page)
print(f"Built {out}: {len(projects)} projects, layout '{layout}', scheme '{scheme}'")
