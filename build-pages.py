#!/usr/bin/env python3
"""Generate the bilingual site from src/site.html.

Every page exists in both languages, each as its own file with its own URL:

    /ar/index.html  /ar/about.html  /ar/terms.html  ...
    /en/index.html  /en/about.html  /en/terms.html  ...
    /index.html     -> sends visitors to the right tree

src/site.html is the single source. It carries every page's markup and the
shared logic, and picks which page and which language to render from the two
meta tags this script writes into each generated file. Each page also gets
its own title, description, canonical URL and hreflang alternates, so both
language versions can be linked, shared and indexed independently.

Run after any change to src/site.html:

    python3 build-pages.py

Keep PAGES below in sync with the PAGES list inside src/site.html.
"""

import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "src" / "site.html"
SITE = "https://www.velorci.com"
LANGS = ("ar", "en")

# key -> output file, then per-language <title> and meta description
PAGES = [
    ("home", "index.html", {
        "ar": ("velorci — منصة تشغيل الأعمال المتكاملة",
               "منصة تشغيل أعمال متكاملة تدير الطلبات والتوصيل والمتجر والمحاسبة وواتساب والإعلانات ونقطة البيع — من لوحة واحدة."),
        "en": ("velorci — the all-in-one business operating platform",
               "One platform running orders, delivery, your online store, accounting, WhatsApp, ads and POS — from a single dashboard."),
    }),
    ("about", "about.html", {
        "ar": ("من نحن — velorci",
               "من نحن ولمن نبني: منصة تشغيل أعمال واحدة تغني عن ربط أدوات متفرقة، للمنشآت في الخليج والعالم العربي."),
        "en": ("About us — velorci",
               "Who we are and who we build for: one business operating platform that replaces a stack of disconnected tools."),
    }),
    ("services", "services.html", {
        "ar": ("الخدمات والباقات — velorci",
               "موديولات المنصة وباقات الاشتراك السنوي: إدارة الطلبات، المتجر الإلكتروني، المحاسبة، نقطة البيع، واتساب الأعمال والإعلانات."),
        "en": ("Services & plans — velorci",
               "Platform modules and annual subscription plans: orders, online store, accounting, POS, WhatsApp Business and ads."),
    }),
    ("team", "team.html", {
        "ar": ("فريق العمل على المنصة — velorci",
               "تطبيق مستقل بصلاحيات محددة لكل دور في عملك — من مدير الشركة حتى الكاشير والسائق."),
        "en": ("Your team on the platform — velorci",
               "A dedicated app with clear permissions for every role in your business — from the manager to the cashier and driver."),
    }),
    ("subscribe", "subscribe.html", {
        "ar": ("إتمام الاشتراك — velorci",
               "اختر باقتك السنوية وأرسل طلب الاشتراك، ونرسل لك فاتورة رسمية ورابط دفع آمن لإتمام العملية."),
        "en": ("Complete your subscription — velorci",
               "Choose your annual plan and submit your request. We'll send a formal invoice and a secure payment link."),
    }),
    ("contact", "contact.html", {
        "ar": ("تواصل معنا — velorci",
               "راسلنا لحجز عرض تجريبي أو لأي استفسار عن المنصة. بيانات التواصل والعنوان المسجّل لشركة Velorci LLC."),
        "en": ("Contact us — velorci",
               "Reach out to book a demo or ask about the platform. Contact details and the registered address of Velorci LLC."),
    }),
    ("terms", "terms.html", {
        "ar": ("شروط الاستخدام — velorci",
               "شروط استخدام منصة فيلورسي: وصف الخدمة، الاشتراك السنوي والدفع، التجديد والإلغاء، حدود المسؤولية والقانون الحاكم."),
        "en": ("Terms of Service — velorci",
               "Terms for using the Velorci platform: the service, annual subscription and payment, renewal and cancellation, liability and governing law."),
    }),
    ("privacy", "privacy.html", {
        "ar": ("سياسة الخصوصية — velorci",
               "كيف نجمع بياناتك الشخصية ونستخدمها ونحميها، ومع من نشاركها، وما حقوقك في الوصول إليها وتصحيحها وحذفها."),
        "en": ("Privacy Policy — velorci",
               "What personal data we collect, why we process it, who we share it with, how we protect it, and your rights over it."),
    }),
    ("refund", "refund.html", {
        "ar": ("سياسة الاسترجاع والإلغاء — velorci",
               "استرداد كامل خلال 14 يوماً من بدء الاشتراك، شروط إلغاء التجديد التلقائي، ومدة وطريقة رد المبلغ."),
        "en": ("Refund & Cancellation Policy — velorci",
               "Full refund within 14 days of the subscription start, how to cancel auto-renewal, and how refunds are returned."),
    }),
]

DIR = {"ar": "rtl", "en": "ltr"}

SUBS = (
    (re.compile(r"<title>.*?</title>", re.S), "<title>{title}</title>"),
    (re.compile(r'<meta name="description" content="[^"]*">'), '<meta name="description" content="{desc}">'),
    (re.compile(r'<meta property="og:title" content="[^"]*">'), '<meta property="og:title" content="{title}">'),
    (re.compile(r'<meta property="og:description" content="[^"]*">'), '<meta property="og:description" content="{desc}">'),
    (re.compile(r'<meta property="og:url" content="[^"]*">'), '<meta property="og:url" content="{url}">'),
    (re.compile(r'<meta property="og:locale" content="[^"]*">\n?'), ""),
    (re.compile(r'<meta name="velorci-(?:page|lang)" content="[^"]*">\n?'), ""),
    (re.compile(r'<link rel="canonical" href="[^"]*">\n?'), ""),
    (re.compile(r'<link rel="alternate"[^>]*>\n?'), ""),
    (re.compile(r'<html[^>]*>'), '<html lang="{lang}" dir="{dir}">'),
)

ROOT_REDIRECT = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>velorci</title>
<meta name="robots" content="noindex">
<link rel="alternate" hreflang="ar" href="{site}/ar/index.html">
<link rel="alternate" hreflang="en" href="{site}/en/index.html">
<link rel="alternate" hreflang="x-default" href="{site}/ar/index.html">
<meta http-equiv="refresh" content="0; url=ar/index.html">
<style>
  body{{margin:0;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;
       background:#041316;color:#E8FFFE;font-family:system-ui,sans-serif;text-align:center;padding:24px;}}
  a{{padding:12px 28px;border-radius:22px;border:1px solid rgba(101,212,210,.45);color:#65D4D2;
     text-decoration:none;font-weight:700;font-size:15px;}}
  a:hover{{background:rgba(101,212,210,.12);}}
  .row{{display:flex;gap:12px;flex-wrap:wrap;justify-content:center;}}
</style>
</head>
<body>
<div style="font-size:22px;font-weight:800;letter-spacing:-.02em;">velorci</div>
<div class="row">
  <a href="ar/index.html">العربية</a>
  <a href="en/index.html">English</a>
</div>
<script>
  // Send visitors straight to their language; the meta refresh above is the
  // fallback, and the links stay visible either way.
  try {{
    var en = (navigator.languages || [navigator.language || ""]).some(function (l) {{
      return String(l).toLowerCase().indexOf("ar") !== 0;
    }}) && !(navigator.language || "").toLowerCase().startsWith("ar");
    location.replace(en ? "en/index.html" : "ar/index.html");
  }} catch (e) {{}}
</script>
</body>
</html>
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def render(base: str, key: str, out_name: str, lang: str, title: str, desc: str) -> str:
    url = f"{SITE}/{lang}/{out_name}"
    fields = {"title": esc(title), "desc": esc(desc), "url": url,
              "lang": lang, "dir": DIR[lang]}

    html = base
    for pattern, template in SUBS:
        replacement = template.format(**fields) if template else ""
        html = pattern.sub(lambda _, r=replacement: r, html, count=1)

    alternates = "\n".join(
        f'<link rel="alternate" hreflang="{other}" href="{SITE}/{other}/{out_name}">'
        for other in LANGS
    )
    head_extra = (
        f'<meta name="velorci-page" content="{key}">\n'
        f'<meta name="velorci-lang" content="{lang}">\n'
        f'<meta property="og:locale" content="{"ar_KW" if lang == "ar" else "en_US"}">\n'
        f'<link rel="canonical" href="{url}">\n'
        f'{alternates}\n'
        f'<link rel="alternate" hreflang="x-default" href="{SITE}/ar/{out_name}">'
    )
    html = html.replace("</head>", head_extra + "\n</head>", 1)

    # The generated pages sit one level down, so root-relative siblings move up.
    html = html.replace('src="./support.js"', 'src="../support.js"')
    html = html.replace('"assets/', '"../assets/').replace("(assets/", "(../assets/")
    return html


def main() -> int:
    if not SRC.exists():
        print(f"error: {SRC} not found", file=sys.stderr)
        return 1
    base = SRC.read_text(encoding="utf-8")

    in_app = set(re.findall(r'\{ key:"(\w+)",\s+file:"([\w.]+)"', base))
    declared = {(k, f) for k, f, _ in PAGES}
    if in_app and in_app != declared:
        print("error: PAGES here does not match the PAGES list in src/site.html", file=sys.stderr)
        print(f"  src/site.html: {sorted(in_app)}", file=sys.stderr)
        print(f"  this file    : {sorted(declared)}", file=sys.stderr)
        return 1

    count = 0
    for lang in LANGS:
        out_dir = ROOT / lang
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir()
        for key, out_name, meta in PAGES:
            title, desc = meta[lang]
            (out_dir / out_name).write_text(
                render(base, key, out_name, lang, title, desc), encoding="utf-8")
            count += 1
        print(f"  {lang}/ — {len(PAGES)} pages")

    (ROOT / "index.html").write_text(ROOT_REDIRECT.format(site=SITE), encoding="utf-8")
    print(f"  index.html — language redirect")
    print(f"wrote {count + 1} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
