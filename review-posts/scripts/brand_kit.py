#!/usr/bin/env python3
"""Setup helper: read a business website and pull a starter brand kit.

  python3 brand_kit.py https://example.com --folder "<business folder>"
  python3 brand_kit.py --get-font "Playfair Display" --folder "<business folder>"
      -> downloads one Google Font into <business folder>/fonts/ (use when the site loads fonts with
         JavaScript and the scan found none: read the real font in the browser, then fetch it here)

Writes <business folder>/brand-kit/:
  logo-*.png          logo candidates (look at them and pick one)
  photo-*.jpg         large photos found on the site (look at them and keep the good ones)
  fonts/              the site's Google Fonts, if any (free, open license)
  brand-kit.json      colors, fonts, phone, review links and social links found, plus a suggested palette

Needs Python 3 + Pillow and internet access. If the site blocks it, look at the site in the
browser instead, or ask the person for their logo and colors. Nothing here is final: the skill
shows the person what it found and they confirm.
"""
from __future__ import annotations

import argparse
import colorsys
import io
import json
import re
import ssl
import sys
import urllib.parse
import urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is missing. Run: pip install pillow")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
GENERIC_FONTS = {"inherit", "initial", "sans-serif", "serif", "monospace", "cursive", "system-ui", "arial", "helvetica",
                 "helvetica neue", "-apple-system", "blinkmacsystemfont", "segoe ui", "roboto", "times new roman", "times",
                 "georgia", "verdana", "tahoma", "ui-sans-serif", "ui-serif", "apple color emoji", "segoe ui emoji",
                 "segoe ui symbol", "noto color emoji", "dashicons", "fontawesome", "font awesome 5 free",
                 "font awesome 6 free", "font awesome 5 brands", "eicons", "star", "icomoon", "var", "courier new"}
REVIEW_HOSTS = {"google": ("g.page", "maps.google", "google.com/maps", "goo.gl/maps", "maps.app.goo.gl", "search.google.com/local"),
                "yelp": ("yelp.com",), "bbb": ("bbb.org",), "facebook": ("facebook.com",), "trustpilot": ("trustpilot.com",),
                "houzz": ("houzz.com",), "angi": ("angi.com", "angieslist.com"), "nextdoor": ("nextdoor.com",),
                "homeadvisor": ("homeadvisor.com",), "thumbtack": ("thumbtack.com",), "tripadvisor": ("tripadvisor.",),
                "instagram": ("instagram.com",)}
CTX = ssl.create_default_context()


def fetch(url: str, limit: int = 15_000_000) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=25, context=CTX) as r:
        return r.read(limit)


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.imgs, self.links, self.metas, self.anchors, self.styles, self.inline = [], [], {}, [], [], []
        self.title, self._in_style, self._in_title, self._svg_depth, self.svgs, self._svg = "", False, False, 0, [], []

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if self._svg_depth:
            self._svg.append(self.get_starttag_text() or "")
            self._svg_depth += 1
            return
        if tag == "svg":
            ctx = (a.get("class", "") + a.get("id", "") + a.get("aria-label", "")).lower()
            self._svg_depth, self._svg = 1, [self.get_starttag_text() or ""]
            self._svg_ctx = ctx
            return
        if a.get("style"):
            self.inline.append(a["style"])
        if tag == "img":
            self.imgs.append(a)
        elif tag == "link":
            self.links.append(a)
        elif tag == "meta":
            k = (a.get("property") or a.get("name") or "").lower()
            if k:
                self.metas[k] = a.get("content", "")
        elif tag == "a":
            self.anchors.append(a)
        elif tag == "style":
            self._in_style = True
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if self._svg_depth:
            self._svg.append(f"</{tag}>")
            self._svg_depth -= 1
            if not self._svg_depth:
                self.svgs.append((self._svg_ctx, "".join(self._svg)))
            return
        if tag == "style":
            self._in_style = False
        if tag == "title":
            self._in_title = False

    def handle_startendtag(self, tag, attrs):
        if self._svg_depth:
            self._svg.append(self.get_starttag_text() or "")
            return
        self.handle_starttag(tag, attrs)
        if tag == "svg":  # self-closing svg
            self.handle_endtag("svg")

    def handle_data(self, data):
        if self._in_style:
            self.styles.append(data)
        if self._in_title:
            self.title += data


def biggest_src(img: dict, base: str) -> str:
    best, best_w = img.get("data-orig-src") or img.get("data-src") or img.get("data-lazy-src") or img.get("src", ""), 0
    for attr in ("srcset", "data-srcset", "data-lazy-srcset"):
        for part in img.get(attr, "").split(","):
            bits = part.strip().split()
            if len(bits) == 2 and bits[1].endswith("w") and bits[1][:-1].isdigit() and int(bits[1][:-1]) > best_w:
                best, best_w = bits[0], int(bits[1][:-1])
    return urllib.parse.urljoin(base, best) if best and not best.startswith("data:") else ""


def hexes(css: str) -> list[str]:
    out = []
    for m in re.finditer(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", css):
        h = m.group(1).lower()
        out.append("#" + ("".join(c * 2 for c in h) if len(h) == 3 else h))
    for m in re.finditer(r"rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)", css):
        out.append("#%02x%02x%02x" % tuple(min(255, int(v)) for v in m.groups()))
    return out


def hls(h: str):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hls(r, g, b)


def is_brandy(h: str) -> bool:
    l, s = hls(h)[1], hls(h)[2]
    return s > 0.18 and 0.08 < l < 0.92


def lum(h: str) -> float:
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def shade(h: str, light: float) -> str:
    hh, _, s = hls(h)
    r, g, b = colorsys.hls_to_rgb(hh, light, min(1, s))
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def suggest_palette(ranked: list[str]) -> dict:
    """dark = background behind white text; accent = stars, highlights, lines."""
    brandy = [h for h in ranked if is_brandy(h)]
    if not brandy:
        return {"dark": "#1d2733", "darker": "#10161d", "accent": "#d4a843", "accent_light": "#e6c36a",
                "note": "No brand colors found; neutral navy and gold used. Ask the person for their colors."}
    darks = [h for h in brandy if lum(h) < 0.08]
    dark = darks[0] if darks else shade(brandy[0], 0.2)
    dh = hls(dark)[0]
    accent = next((h for h in brandy if h != dark and lum(h) > 0.12 and min(abs(hls(h)[0] - dh), 1 - abs(hls(h)[0] - dh)) > 0.08), None)
    if not accent:
        accent = shade(brandy[0], 0.6) if lum(brandy[0]) < 0.12 else brandy[0]
    return {"dark": dark, "darker": shade(dark, max(0.06, hls(dark)[1] * 0.6)), "accent": accent,
            "accent_light": shade(accent, min(0.75, hls(accent)[1] + 0.1))}


def css_rules(css: str):
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        yield m.group(1).strip().lower(), m.group(2)


CSS_VARS: dict = {}


def resolve_vars(v: str, depth: int = 0) -> str:
    """var(--x, fallback) -> its value (themes like WordPress/Elementor/Avada keep fonts in variables)."""
    if depth > 5 or "var(" not in v:
        return v
    def sub(m):
        name, fb = m.group(1), (m.group(2) or "").strip()
        return CSS_VARS.get(name, fb)
    return resolve_vars(re.sub(r"var\(\s*--([\w-]+)\s*(?:,\s*([^()]*))?\)", sub, v), depth + 1)


def first_family(decl: str) -> str:
    m = re.search(r"font-family\s*:\s*([^;}{]+)", decl)
    if not m:
        return ""
    for fam in resolve_vars(m.group(1).replace("&quot;", '"')).split(","):
        fam = fam.strip().strip("'\"").strip()
        if fam.lower() not in GENERIC_FONTS and not fam.lower().startswith("var("):
            return fam
    return ""


def google_font_files(family: str, dest: Path) -> list[str]:
    """Download a Google Font family from the official google/fonts GitHub repo (open licenses)."""
    slug = re.sub(r"[^a-z0-9]", "", family.lower())
    for lic in ("ofl", "apache", "ufl"):
        try:
            listing = json.loads(fetch(f"https://api.github.com/repos/google/fonts/contents/{lic}/{slug}"))
        except Exception:
            continue
        ttfs = [f for f in listing if f["name"].lower().endswith(".ttf")]
        want = []
        for test in (lambda n: "italic" not in n and "[" in n, lambda n: n.endswith("-regular.ttf"),
                     lambda n: "italic" in n and "[" in n, lambda n: n.endswith("-italic.ttf"),
                     lambda n: n.endswith("-semibold.ttf") or n.endswith("-bold.ttf"), lambda n: n.endswith("-light.ttf")):
            want += [f for f in ttfs if test(f["name"].lower()) and f not in want][:1]
        lic_file = next((f for f in listing if f["name"].upper().startswith(("OFL", "LICENSE"))), None)
        dest.mkdir(parents=True, exist_ok=True)
        got = []
        for f in want + ([lic_file] if lic_file else []):
            try:
                (dest / f["name"]).write_bytes(fetch(f["download_url"]))
                got.append(f["name"])
            except Exception:
                pass
        return got
    return []


def save_image(data: bytes, path: Path, as_png: bool) -> tuple[int, int, bool] | None:
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception:
        return None
    transparent = im.mode in ("RGBA", "LA", "P") and "A" in im.convert("RGBA").getbands() and im.convert("RGBA").getchannel("A").getextrema()[0] < 250
    if as_png:
        im.convert("RGBA").save(path.with_suffix(".png"))
    else:
        if im.width > 2400:
            im = im.resize((2400, round(im.height * 2400 / im.width)), Image.LANCZOS)
        im.convert("RGB").save(path.with_suffix(".jpg"), quality=92)
    return im.width, im.height, transparent


def svg_to_png(svg: bytes, path: Path) -> bool:
    for mod in ("cairosvg",):
        try:
            import cairosvg  # type: ignore
            cairosvg.svg2png(bytestring=svg, write_to=str(path), output_width=1200)
            return True
        except Exception:
            pass
    import shutil
    import subprocess
    import tempfile
    for tool in (["rsvg-convert", "-w", "1200", "-o", str(path)], ["magick", "-background", "none", "-density", "300", "svg:-", str(path)]):
        if shutil.which(tool[0]):
            try:
                if tool[0] == "rsvg-convert":
                    with tempfile.NamedTemporaryFile(suffix=".svg") as t:
                        t.write(svg)
                        t.flush()
                        subprocess.run(tool + [t.name], check=True, capture_output=True, timeout=30)
                else:
                    subprocess.run(tool, input=svg, check=True, capture_output=True, timeout=30)
                return path.exists()
            except Exception:
                pass
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("website", nargs="?")
    ap.add_argument("--folder", required=True)
    ap.add_argument("--max-photos", type=int, default=30)
    ap.add_argument("--get-font", help="download this Google Font family into <folder>/fonts/")
    a = ap.parse_args()
    if a.get_font:
        got = google_font_files(a.get_font, Path(a.folder).expanduser() / "fonts")
        print("\n".join(got) if got else f"'{a.get_font}' is not on Google Fonts. Ask the person for the .ttf file, or pick a bundled look-alike.")
        return
    if not a.website:
        sys.exit("Give the website, or --get-font.")
    site = a.website if a.website.startswith("http") else "https://" + a.website
    kit = Path(a.folder).expanduser() / "brand-kit"
    kit.mkdir(parents=True, exist_ok=True)
    report: dict = {"website": site, "notes": []}

    try:
        html = fetch(site).decode("utf-8", "replace")
    except Exception as e:
        sys.exit(f"COULD NOT OPEN {site} ({e}). Use the browser to look at the site, or ask for the logo and colors.")
    home = Page()
    home.feed(html)
    pages = [(site, home)]
    # a few inner pages likely to have job photos
    host = urllib.parse.urlparse(site).netloc
    extra = []
    for an in home.anchors:
        href = urllib.parse.urljoin(site, an.get("href", ""))
        if urllib.parse.urlparse(href).netloc == host and re.search(r"gallery|project|portfolio|our-work|work|before-after|photos", href, re.I):
            if href.split("#")[0] not in extra and href.split("#")[0].rstrip("/") != site.rstrip("/"):
                extra.append(href.split("#")[0])
    for href in extra[:3]:
        try:
            pg = Page()
            pg.feed(fetch(href).decode("utf-8", "replace"))
            pages.append((href, pg))
        except Exception:
            pass

    report["business_name_guess"] = (home.metas.get("og:site_name") or re.split(r"\s[|\-–—]\s", home.title.strip())[-1]).strip()

    # ---- CSS: linked stylesheets + inline
    css_parts = list(home.styles) + home.inline
    for ln in home.links:
        if "stylesheet" in ln.get("rel", "").lower() and ln.get("href"):
            href = urllib.parse.urljoin(site, ln["href"])
            if "fonts.googleapis.com" in href:
                continue
            try:
                css_parts.append(fetch(href, 3_000_000).decode("utf-8", "replace"))
            except Exception:
                pass
            if len(css_parts) > 40:
                break
    css = "\n".join(css_parts)

    for m in re.finditer(r"--([\w-]+)\s*:\s*([^;}{]+)", css):
        CSS_VARS.setdefault(m.group(1), m.group(2).strip())
    # ---- colors
    counts = Counter(hexes(css))
    vars_ = {}
    for m in re.finditer(r"--([\w-]*(?:primary|secondary|accent|brand|main|theme|highlight)[\w-]*)\s*:\s*([^;}{]+)", css, re.I):
        hx = hexes(m.group(2))
        if hx:
            vars_[m.group(1)] = hx[0]
    theme = home.metas.get("theme-color", "")
    ranked = [h for h, _ in counts.most_common(40)]
    priority = list(vars_.values()) + hexes(theme)
    ranked = list(dict.fromkeys([h for h in priority if is_brandy(h)] + [h for h in ranked if is_brandy(h)]))
    report["colors"] = {"brand_colors_ranked": ranked[:12], "css_brand_variables": vars_, "theme_color": theme}

    # ---- fonts
    gfams = []
    for ln in home.links:
        href = ln.get("href", "")
        if "fonts.googleapis.com" in href:
            for fam in re.findall(r"family=([^&:]+)", urllib.parse.unquote(href)):
                gfams.append(fam.replace("+", " ").strip())
    for m in re.finditer(r"fonts\.googleapis\.com/css2?\?([^'\")\s]+)", css + html):
        for fam in re.findall(r"family=([^&:]+)", urllib.parse.unquote(m.group(1))):
            gfams.append(fam.replace("+", " ").strip())
    head_c, body_c = Counter(), Counter()
    for sel, decl in css_rules(css):
        fam = first_family(decl)
        if not fam:
            continue
        if re.search(r"(^|[\s,>])h[1-3]\b|heading|title|hero", sel):
            head_c[fam] += 1
        elif re.search(r"(^|[\s,])(body|html|p)\b", sel):
            body_c[fam] += 3
        else:
            body_c[fam] += 1
    head = (head_c.most_common(1) or [("", 0)])[0][0]
    body = (body_c.most_common(1) or [("", 0)])[0][0]
    if not (head or body):
        report["notes"].append("No fonts found in the page source (the site probably loads them with JavaScript). In the browser run: "
                               "[...['h1','h2','p']].map(t => t + ': ' + getComputedStyle(document.querySelector(t) || document.body).fontFamily), "
                               "then use --get-font.")
    fonts = {"heading_font": head or body, "body_font": body or head, "google_fonts_linked": list(dict.fromkeys(gfams)), "downloaded": {}}
    for fam in dict.fromkeys(f for f in (fonts["heading_font"], fonts["body_font"]) if f):
        got = google_font_files(fam, kit / "fonts")
        if got:
            fonts["downloaded"][fam] = got
        else:
            report["notes"].append(f"Font '{fam}' is not a free Google Font (or couldn't be downloaded); a bundled look-alike will be used unless the person sends the font file.")
    report["fonts"] = fonts

    # ---- logo candidates
    cands = []
    for base, pg in pages[:1]:
        for im in pg.imgs:
            ctx = " ".join(im.get(k, "") for k in ("src", "alt", "class", "id", "data-src")).lower()
            if "logo" in ctx:
                src = biggest_src(im, base)
                if src:
                    cands.append(("img", src))
        for ln in pg.links:
            rel = ln.get("rel", "").lower()
            if "apple-touch-icon" in rel or ("icon" in rel and ln.get("sizes", "") not in ("16x16", "32x32")):
                cands.append(("icon", urllib.parse.urljoin(base, ln.get("href", ""))))
        if pg.metas.get("og:image"):
            cands.append(("og:image", urllib.parse.urljoin(base, pg.metas["og:image"])))
    logos = []
    for i, (kind, url) in enumerate(dict.fromkeys(cands)):
        if len(logos) >= 6:
            break
        try:
            data = fetch(url)
        except Exception:
            continue
        path = kit / f"logo-{len(logos) + 1}.png"
        if url.lower().split("?")[0].endswith(".svg") or data.lstrip()[:5] in (b"<svg ", b"<?xml"):
            if not svg_to_png(data, path):
                (kit / f"logo-{len(logos) + 1}.svg").write_bytes(data)
                logos.append({"file": path.with_suffix(".svg").name, "from": kind, "url": url, "note": "SVG: couldn't convert here. Ask the person for a PNG, or screenshot it in the browser."})
                continue
            info = Image.open(path).size + (True,)
        else:
            info = save_image(data, path, as_png=True)
            if not info:
                continue
        logos.append({"file": path.name, "from": kind, "url": url, "size": f"{info[0]}x{info[1]}", "transparent": info[2]})
    for ctx, svg in home.svgs:  # inline <svg> logos
        if "logo" in ctx and len(logos) < 8:
            path = kit / f"logo-{len(logos) + 1}.png"
            if svg_to_png(svg.encode(), path):
                logos.append({"file": path.name, "from": "inline svg", "size": "%dx%d" % Image.open(path).size, "transparent": True})
    report["logos"] = logos
    # logo colors help when the CSS is noisy
    for lg in logos:
        if lg["file"].endswith(".png"):
            im = Image.open(kit / lg["file"]).convert("RGBA")
            im.thumbnail((200, 200))
            px = [p[:3] for p in im.getdata() if p[3] > 200]
            common = Counter("#%02x%02x%02x" % tuple(v // 8 * 8 for v in p) for p in px).most_common(8)
            lg["colors"] = [h for h, _ in common if is_brandy(h)][:4]
    logo_colors = [c for lg in logos for c in lg.get("colors", [])]
    report["colors"]["logo_colors"] = list(dict.fromkeys(logo_colors))[:6]
    report["colors"]["suggested"] = suggest_palette(list(dict.fromkeys(report["colors"]["logo_colors"][:2] + ranked)))

    # ---- photos
    urls = []
    for base, pg in pages:
        for im in pg.imgs:
            ctx = " ".join(im.get(k, "") for k in ("src", "alt", "class")).lower()
            if any(w in ctx for w in ("logo", "icon", "badge", "award", "avatar", "seal", "certif", "accredit", "association",
                                      "bbb", "google", "facebook", "yelp", "warrant", "clipart", "partner", "member")):
                continue
            u = biggest_src(im, base)
            if u and not u.lower().split("?")[0].endswith(".svg"):
                urls.append(u)
        if pg.metas.get("og:image"):
            urls.append(urllib.parse.urljoin(base, pg.metas["og:image"]))
        for st in pg.inline + pg.styles:
            for m in re.finditer(r"url\(['\"]?([^'\")]+\.(?:jpe?g|png|webp)[^'\")]*)", st, re.I):
                urls.append(urllib.parse.urljoin(base, m.group(1)))
    photos = []
    for u in dict.fromkeys(urls):
        if len(photos) >= a.max_photos:
            break
        try:
            data = fetch(u)
        except Exception:
            continue
        path = kit / f"photo-{len(photos) + 1:02d}.jpg"
        info = save_image(data, path, as_png=False)
        if not info:
            continue
        if max(info[:2]) < 1000:  # too small for a 1080x1350 post
            path.with_suffix(".jpg").unlink(missing_ok=True)
            continue
        photos.append({"file": path.name, "size": f"{info[0]}x{info[1]}", "url": u})
    report["photos"] = photos
    if len(photos) < 4:
        report["notes"].append("Few big photos on the site. Ask the person for job photos, or use free stock aerials of their area (see reference/photos.md).")

    # ---- phone, review and social links
    phones, links = [], {}
    for base, pg in pages:
        for an in pg.anchors:
            href = an.get("href", "")
            if href.startswith("tel:"):
                phones.append(href[4:].strip())
            for k, hosts in REVIEW_HOSTS.items():
                if any(hh in href for hh in hosts):
                    links.setdefault(k, [])
                    if href not in links[k]:
                        links[k].append(href)
    report["phone"] = (Counter(phones).most_common(1) or [("", 0)])[0][0]
    report["review_and_social_links"] = links

    (kit / "brand-kit.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ("business_name_guess", "colors", "fonts", "phone", "review_and_social_links")}, indent=1))
    print(f"\n{len(logos)} logo candidate(s), {len(photos)} photo(s) -> {kit}")
    for n in report["notes"]:
        print("NOTE:", n)


if __name__ == "__main__":
    main()
