#!/usr/bin/env python3
"""Generate one HTML file per page from index.html.

index.html is the single source: it carries every page's markup and the
shared logic, and decides which one to show from the <meta name="velorci-page">
tag this script writes into each generated file. Each page also gets its own
<title>, description and canonical URL so it can be linked, shared and
indexed on its own.

Run after any change to index.html:

    python3 build-pages.py

Keep PAGES below in sync with the PAGES list inside index.html.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "index.html"
SITE = "https://www.velorci.com"

# key, output file, <title>, meta description
PAGES = [
    ("home", "index.html",
     "velorci — منصة تشغيل الأعمال المتكاملة",
     "منصة تشغيل أعمال متكاملة تدير الطلبات والتوصيل والمتجر والمحاسبة وواتساب والإعلانات ونقطة البيع — من لوحة واحدة."),
    ("about", "about.html",
     "من نحن — velorci",
     "من نحن ولمن نبني: منصة تشغيل أعمال واحدة تغني عن ربط أدوات متفرقة، للمنشآت في الخليج والعالم العربي."),
    ("services", "services.html",
     "الخدمات والباقات — velorci",
     "موديولات المنصة وباقات الاشتراك السنوي: إدارة الطلبات، المتجر الإلكتروني، المحاسبة، نقطة البيع، واتساب الأعمال والإعلانات."),
    ("team", "team.html",
     "فريق العمل على المنصة — velorci",
     "تطبيق مستقل بصلاحيات محددة لكل دور في عملك — من مدير الشركة حتى الكاشير والسائق."),
    ("subscribe", "subscribe.html",
     "إتمام الاشتراك — velorci",
     "اختر باقتك السنوية وأرسل طلب الاشتراك، ونرسل لك فاتورة رسمية ورابط دفع آمن لإتمام العملية."),
    ("contact", "contact.html",
     "تواصل معنا — velorci",
     "راسلنا لحجز عرض تجريبي أو لأي استفسار عن المنصة. بيانات التواصل والعنوان المسجّل لشركة Velorci LLC."),
    ("terms", "terms.html",
     "شروط الاستخدام — velorci",
     "شروط استخدام منصة فيلورسي: وصف الخدمة، الاشتراك السنوي والدفع، التجديد والإلغاء، حدود المسؤولية والقانون الحاكم."),
    ("privacy", "privacy.html",
     "سياسة الخصوصية — velorci",
     "كيف نجمع بياناتك الشخصية ونستخدمها ونحميها، ومع من نشاركها، وما حقوقك في الوصول إليها وتصحيحها وحذفها."),
    ("refund", "refund.html",
     "سياسة الاسترجاع والإلغاء — velorci",
     "استرداد كامل خلال 14 يوماً من بدء الاشتراك، شروط إلغاء التجديد التلقائي، ومدة وطريقة رد المبلغ."),
]

TITLE_RE = re.compile(r"<title>.*?</title>", re.S)
DESC_RE = re.compile(r'<meta name="description" content="[^"]*">')
OG_TITLE_RE = re.compile(r'<meta property="og:title" content="[^"]*">')
OG_DESC_RE = re.compile(r'<meta property="og:description" content="[^"]*">')
OG_URL_RE = re.compile(r'<meta property="og:url" content="[^"]*">')
CANONICAL_RE = re.compile(r'<link rel="canonical" href="[^"]*">')
PAGE_META_RE = re.compile(r'<meta name="velorci-page" content="[^"]*">\n?')


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def render(base: str, key: str, title: str, desc: str, out_name: str) -> str:
    html = PAGE_META_RE.sub("", base)

    url = f"{SITE}/" if out_name == "index.html" else f"{SITE}/{out_name}"
    head_extra = f'<meta name="velorci-page" content="{key}">\n<link rel="canonical" href="{url}">'

    html = TITLE_RE.sub(lambda _: f"<title>{esc(title)}</title>", html, count=1)
    for pattern, replacement in (
        (DESC_RE, f'<meta name="description" content="{esc(desc)}">'),
        (OG_TITLE_RE, f'<meta property="og:title" content="{esc(title)}">'),
        (OG_DESC_RE, f'<meta property="og:description" content="{esc(desc)}">'),
        (OG_URL_RE, f'<meta property="og:url" content="{url}">'),
    ):
        html = pattern.sub(lambda _, r=replacement: r, html, count=1)

    html = CANONICAL_RE.sub("", html, count=1)
    html = html.replace("</head>", head_extra + "\n</head>", 1)
    return html


def main() -> int:
    base = SRC.read_text(encoding="utf-8")

    keys_in_app = set(re.findall(r'\{ key:"(\w+)",\s+file:"([\w.]+)"', base))
    declared = {(k, f) for k, f, _, _ in PAGES}
    if keys_in_app and keys_in_app != declared:
        print("error: PAGES here does not match the PAGES list in index.html", file=sys.stderr)
        print(f"  index.html: {sorted(keys_in_app)}", file=sys.stderr)
        print(f"  this file : {sorted(declared)}", file=sys.stderr)
        return 1

    for key, out_name, title, desc in PAGES:
        (ROOT / out_name).write_text(render(base, key, title, desc, out_name), encoding="utf-8")
        print(f"  {out_name:<16} {key}")

    print(f"wrote {len(PAGES)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
