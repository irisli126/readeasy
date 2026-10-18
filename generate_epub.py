import json
import os
import re
import zipfile
import html
import uuid

def clean_paragraph(p, chapter_title=""):
    text = p.strip()
    if not text:
        return None
    # Skip standalone page numbers
    if text.isdigit() and len(text) <= 3:
        return None
    # Skip running headers
    if 'ÄNGLARNAS SVAR' in text.upper() and len(text) < 30:
        return None
    # Skip chapter title repetitions in header/footer margins
    if chapter_title and text.upper() == chapter_title.upper() and len(text) < 25:
        return None
    # Skip scan noise (e.g. random barcode or scan line symbols)
    if re.match(r'^[IO02bUY\-\(\)\s\.\,\'\"%]{4,15}$', text):
        return None
    return text

def build_epub():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    cover_path = os.path.join(data_dir, 'cover.jpg')
    processed_path = os.path.join(data_dir, 'book_processed.json')
    output_epub = os.path.join(base_dir, 'Änglarnas svar.epub')

    with open(processed_path, 'r', encoding='utf-8') as f:
        pages = json.load(f)

    # Define chapters with their starting pages and titles
    chapter_defs = [
        {'id': 'prolog', 'title': 'PROLOG', 'subtitle': '2011', 'start': 2, 'end': 5},
        {'id': 'marcus', 'title': 'MARCUS', 'subtitle': '1963', 'start': 6, 'end': 34},
        {'id': 'iris', 'title': 'IRIS', 'subtitle': '1968', 'start': 35, 'end': 60},
        {'id': 'hanna', 'title': 'HANNA', 'subtitle': '1954', 'start': 61, 'end': 92},
        {'id': 'madeleine', 'title': 'MADELEINE', 'subtitle': '1968', 'start': 93, 'end': 113},
        {'id': 'andreas', 'title': 'ANDREAS', 'subtitle': '1970', 'start': 114, 'end': 125},
        {'id': 'rachel', 'title': 'RACHEL', 'subtitle': '1968', 'start': 126, 'end': 140},
        {'id': 'vladek', 'title': 'VLADEK', 'subtitle': '1970', 'start': 141, 'end': 166},
        {'id': 'epilog', 'title': 'EPILOG', 'subtitle': '2011', 'start': 167, 'end': 171},
    ]

    # Collect chapter XHTML files
    chapter_files = []
    
    # 1. Info / Copyright Page (Page 1)
    p1 = pages[0]
    p1_paras = [html.escape(p) for p in p1.get('paragraphs', []) if clean_paragraph(p)]
    info_html = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="sv" lang="sv">
<head>
  <title>Bokinformation</title>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body class="info-body">
  <div class="book-info">
    <h1 class="book-main-title">Änglarnas svar</h1>
    <h2 class="book-author">Stefan Einhorn</h2>
    <hr class="title-divider"/>
    <div class="pub-details">
      {''.join(f'<p class="info-para">{p}</p>' for p in p1_paras)}
    </div>
  </div>
</body>
</html>'''
    chapter_files.append({
        'id': 'info',
        'href': 'info.xhtml',
        'title': 'Bokinformation',
        'content': info_html
    })

    # 2. Novel Chapters
    for ch in chapter_defs:
        ch_paras = []
        for p_idx in range(ch['start'] - 1, min(ch['end'], len(pages))):
            page_obj = pages[p_idx]
            for p_str in page_obj.get('paragraphs', []):
                cleaned = clean_paragraph(p_str, ch['title'])
                if cleaned:
                    # Skip if it is just the chapter title or subtitle at the top
                    if cleaned.upper() == ch['title'].upper() or cleaned == ch['subtitle']:
                        continue
                    ch_paras.append(html.escape(cleaned))

        paras_html = ''.join(f'<p>{p}</p>\n' for p in ch_paras)
        ch_html = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="sv" lang="sv">
<head>
  <title>{html.escape(ch['title'])}</title>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body>
  <div class="chapter-header">
    <h1 class="chapter-title">{html.escape(ch['title'])}</h1>
    <h2 class="chapter-subtitle">{html.escape(ch['subtitle'])}</h2>
  </div>
  <div class="chapter-content">
    {paras_html}
  </div>
</body>
</html>'''
        chapter_files.append({
            'id': ch['id'],
            'href': f"{ch['id']}.xhtml",
            'title': f"{ch['title']} ({ch['subtitle']})",
            'content': ch_html
        })

    # 3. Cover page (cover.xhtml)
    cover_xhtml = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="sv" lang="sv">
<head>
  <title>Omslag</title>
  <style type="text/css">
    @page { margin: 0; }
    body { margin: 0; padding: 0; text-align: center; background-color: #000; }
    img { max-width: 100%; max-height: 100vh; height: auto; margin: auto; }
  </style>
</head>
<body>
  <div>
    <img src="cover.jpg" alt="Änglarnas svar av Stefan Einhorn"/>
  </div>
</body>
</html>'''

    # 4. Stylesheet (stylesheet.css)
    stylesheet_css = '''
@charset "utf-8";

body {
  margin: 5%;
  font-family: "Georgia", "Merriweather", "Times New Roman", serif;
  font-size: 1.05em;
  line-height: 1.65;
  text-align: justify;
  text-justify: inter-word;
  color: #1a1a1a;
}

h1.chapter-title {
  text-align: center;
  font-size: 1.9em;
  font-weight: bold;
  letter-spacing: 0.08em;
  margin-top: 2.2em;
  margin-bottom: 0.2em;
  text-transform: uppercase;
}

h2.chapter-subtitle {
  text-align: center;
  font-size: 1.15em;
  font-weight: normal;
  letter-spacing: 0.1em;
  color: #555555;
  margin-top: 0;
  margin-bottom: 2.5em;
}

p {
  text-indent: 1.7em;
  margin-top: 0;
  margin-bottom: 0.35em;
}

div.chapter-content > p:first-child {
  text-indent: 0;
}

/* Book info page */
div.book-info {
  text-align: center;
  margin-top: 20%;
}

h1.book-main-title {
  font-size: 2.2em;
  margin-bottom: 0.3em;
  letter-spacing: 0.05em;
}

h2.book-author {
  font-size: 1.3em;
  font-weight: normal;
  color: #444;
  margin-bottom: 1.5em;
}

hr.title-divider {
  width: 40%;
  border: none;
  border-top: 1px solid #aaa;
  margin: 2em auto;
}

div.pub-details {
  font-size: 0.85em;
  color: #666;
  line-height: 1.6;
}

p.info-para {
  text-indent: 0;
  margin-bottom: 0.8em;
}
'''

    # 5. Table of contents (nav.xhtml - EPUB3 Navigation)
    nav_items = ''.join(f'<li><a href="{ch["href"]}">{html.escape(ch["title"])}</a></li>\n' for ch in chapter_files)
    nav_xhtml = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="sv" lang="sv">
<head>
  <title>Innehållsförteckning</title>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Innehållsförteckning</h1>
    <ol>
      {nav_items}
    </ol>
  </nav>
</body>
</html>'''

    # 6. NCX table of contents (toc.ncx - EPUB2 / Kindle legacy compatibility)
    ncx_points = []
    play_order = 1
    for ch in chapter_files:
        ncx_points.append(f'''
    <navPoint id="navPoint-{play_order}" playOrder="{play_order}">
      <navLabel><text>{html.escape(ch['title'])}</text></navLabel>
      <content src="{ch['href']}"/>
    </navPoint>''')
        play_order += 1

    toc_ncx = f'''<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:isbn:9789137136721"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>Änglarnas svar</text></docTitle>
  <docAuthor><text>Stefan Einhorn</text></docAuthor>
  <navMap>
    {''.join(ncx_points)}
  </navMap>
</ncx>'''

    # 7. Package Document (content.opf)
    manifest_items = [
        '<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>',
        '<item id="cover-image" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/>',
        '<item id="style" href="stylesheet.css" media-type="text/css"/>',
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
    ]
    for ch in chapter_files:
        manifest_items.append(f'<item id="{ch["id"]}" href="{ch["href"]}" media-type="application/xhtml+xml"/>')

    spine_items = [
        '<itemref idref="cover" linear="no"/>'
    ]
    for ch in chapter_files:
        spine_items.append(f'<itemref idref="{ch["id"]}"/>')

    content_opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="3.0" xml:lang="sv">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title id="title">Änglarnas svar</dc:title>
    <dc:creator id="creator">Stefan Einhorn</dc:creator>
    <dc:identifier id="BookId">urn:isbn:9789137136721</dc:identifier>
    <dc:language>sv</dc:language>
    <dc:publisher>Bokförlaget Forum</dc:publisher>
    <dc:date>2011-09-01</dc:date>
    <dc:description>Roman av Stefan Einhorn.</dc:description>
    <meta property="dcterms:modified">2026-10-18T18:45:00Z</meta>
    <meta name="cover" content="cover-image"/>
  </metadata>
  <manifest>
    {chr(10).join(manifest_items)}
  </manifest>
  <spine toc="ncx">
    {chr(10).join(spine_items)}
  </spine>
  <guide>
    <reference type="cover" title="Cover" href="cover.xhtml"/>
    <reference type="toc" title="Innehåll" href="nav.xhtml"/>
    <reference type="text" title="Start" href="info.xhtml"/>
  </guide>
</package>'''

    # 8. Create ZIP archive (EPUB format)
    print(f"Creating EPUB file: {output_epub}...")
    with zipfile.ZipFile(output_epub, 'w') as zf:
        # First file: 'mimetype' MUST be stored uncompressed
        zf.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)

        # Container XML
        container_xml = '''<?xml version="1.0" encoding="utf-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
        zf.writestr('META-INF/container.xml', container_xml, compress_type=zipfile.ZIP_DEFLATED)

        # OEBPS content
        zf.writestr('OEBPS/content.opf', content_opf, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr('OEBPS/toc.ncx', toc_ncx, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr('OEBPS/nav.xhtml', nav_xhtml, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr('OEBPS/stylesheet.css', stylesheet_css, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr('OEBPS/cover.xhtml', cover_xhtml, compress_type=zipfile.ZIP_DEFLATED)

        # Cover image
        if os.path.exists(cover_path):
            with open(cover_path, 'rb') as img_f:
                zf.writestr('OEBPS/cover.jpg', img_f.read(), compress_type=zipfile.ZIP_DEFLATED)

        # Chapters
        for ch in chapter_files:
            zf.writestr(f"OEBPS/{ch['href']}", ch['content'], compress_type=zipfile.ZIP_DEFLATED)

    epub_size = os.path.getsize(output_epub)
    print(f"EPUB successfully generated: {output_epub} ({epub_size / (1024*1024):.2f} MB)")

if __name__ == '__main__':
    build_epub()
