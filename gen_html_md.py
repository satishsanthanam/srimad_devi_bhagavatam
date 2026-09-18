#!/usr/bin/env python3
import os
import re
import html
import time

CSS_VERSION = f"v={int(time.time())}"

def parse_interleaved_text(text_content):
    """Parses interleaved verse blocks into structured dictionaries."""
    header_match = re.search(r'(=+\s*\n.*?\n=+)', text_content, re.DOTALL)
    header_title = header_match.group(1).replace('=', '').strip() if header_match else "Srimad Devi Bhagavatam"

    content_without_header = re.sub(r'=+\s*\n.*?\n=+', '', text_content, flags=re.DOTALL).strip()
    blocks = content_without_header.split('----------------------------------------')
    parsed_verses = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        header_m = re.search(r'\[(.*?)\]', block)
        verse_header = header_m.group(1).strip() if header_m else "Verse"

        if "English Translation:" in block:
            parts = block.split("English Translation:")
            sanskrit_part = re.sub(r'\[.*?\]', '', parts[0]).strip()
            english_part = parts[1].strip()
        else:
            sanskrit_part = re.sub(r'\[.*?\]', '', block).strip()
            english_part = ""

        colophon_m = re.search(r'(इति\s+श्रीमद्देवी.*)', sanskrit_part, re.DOTALL)
        colophon_text = ""
        if colophon_m:
            colophon_text = colophon_m.group(1).strip()
            sanskrit_part = sanskrit_part[:colophon_m.start()].strip()

        # --- Building the Card HTML ---
        colo_html = f'''
        <div class="section-label label-colophon">Sanskrit Colophon</div>
        <div class="colophon-card">{html.escape(colophon_text)}</div>
        ''' if colophon_text else ""

        parsed_verses.append({
            "header": verse_header,
            "sanskrit": sanskrit_part,
            "colophon": colophon_text,
            "english": english_part
        })

    return header_title, parsed_verses

def generate_markdown(title, verses):
    """Generates Collapsible Markdown."""
    clean_title = title.replace('=', '').strip()
    md_lines = [f"# {clean_title}\n"]
    
    for v in verses:
        md_lines.append(f"<details>")
        md_lines.append(f"  <summary><b>{v['header']}</b></summary>")
        md_lines.append(f"  <br>\n")
        
        if v['sanskrit']:
            san_formatted = v['sanskrit'].replace('\n', '\n> ')
            md_lines.append(f"> **Sanskrit:**\n> {san_formatted}\n>")
            
        if v['colophon']:
            colo_formatted = v['colophon'].replace('\n', '\n> ')
            md_lines.append(f"> *Colophon:*\n> {colo_formatted}\n>")
            
        if v['english']:
            md_lines.append(f"**English Translation:**\n\n{v['english']}\n")
            
        md_lines.append(f"</details>\n")

    return "\n".join(md_lines)

def generate_html(title, verses, css_rel_path="/res/style.css", index_rel_path="/index.html", prev_link=None, next_link=None):
    clean_title = title.replace('=', '').strip()
    
    # Parse Book and Chapter numbers
    book_match = re.search(r'BOOK\s*(\d+)', clean_title, re.IGNORECASE)
    chap_match = re.search(r'CHAPTER\s*(\d+)', clean_title, re.IGNORECASE)
    
    main_display_title = "Śrīmad Devī Bhāgavatam"

    if book_match and chap_match:
        book_num = book_match.group(1).zfill(2) # e.g., '01'
        chap_num = chap_match.group(1)
        
        # Make BOOK X clickable to return to that book's section on index.html
        book_link = f'<a href="{index_rel_path}#B{book_num}" class="breadcrumb-link">BOOK {int(book_num)}</a>'
        subtitle_html = f"{book_link} • CHAPTER {chap_num}"
    else:
        subtitle_html = html.escape(clean_title.upper())

    # Build Navigation Bar HTML
    prev_html = (
        f'<a href="{prev_link}" class="nav-btn prev-btn">← Previous Chapter</a>'
        if prev_link else '<span class="nav-btn disabled">← Previous Chapter</span>'
    )
    next_html = (
        f'<a href="{next_link}" class="nav-btn next-btn">Next Chapter →</a>'
        if next_link else '<span class="nav-btn disabled">Next Chapter →</span>'
    )

    nav_block = f"""
        <nav class="chapter-nav">
            {prev_html}
            <a href="{index_rel_path}" class="nav-btn index-btn">☰ Index</a>
            {next_html}
        </nav>
    """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{main_display_title} - {html.escape(clean_title)}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+Devanagari:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{css_rel_path}?{CSS_VERSION}">
</head>
<body>
    <div class="container">
        <div class="doc-header">
            <div class="breadcrumb">Scriptures</div>
            
            <!-- Linked Main Title -->
            <h1><a href="{index_rel_path}" class="header-title-link">{main_display_title}</a></h1>
            
            <!-- Subtitle with Clickable BOOK Link -->
            <div class="chapter-subtitle">{subtitle_html}</div>
            
            <div class="controls" style="margin-top: 1rem;">
                <button class="btn btn-primary" onclick="toggleAll(true)">Expand All</button>
                <button class="btn" onclick="toggleAll(false)">Collapse All</button>
            </div>

            <!-- TOP NAVIGATION -->
            {nav_block}
        </div>
"""

    for v in verses:
        san_html = f'''
        <div class="section-label label-sanskrit">Sanskrit Text</div>
        <div class="sanskrit-card">{html.escape(v["sanskrit"])}</div>
        ''' if v["sanskrit"] else ""

        colo_html = f'''
        <div class="section-label label-colophon">Sanskrit Colophon</div>
        <div class="colophon-card">{html.escape(v["colophon"])}</div>
        ''' if v["colophon"] else ""

        eng_html = f'''
        <div class="section-label label-english">English Translation</div>
        <div class="english-card">{html.escape(v["english"])}</div>
        ''' if v["english"] else ""

        html_content += f"""
        <details class="verse-details">
            <summary>
                <span>{html.escape(v["header"])}</span>
                <span class="badge">Verse</span>
            </summary>
            <div class="content">
                {san_html}
                {colo_html}
                {eng_html}
            </div>
        </details>"""

    # --- BOTTOM NAVIGATION & CITATION FOOTER ---
    html_content += f"""
        <!-- BOTTOM NAVIGATION -->
        {nav_block}

<!-- Site Footer -->
        <footer class="doc-footer" style="margin-top: 3rem; padding: 1.5rem 0; border-top: 1px solid #e2e8f0; text-align: center; color: #64748b; font-size: 0.9rem;">
            <p><strong>🙏 Shri Krishnarpanam Asthu 🙏</strong> | Maintained &amp; published via <a href="https://ventpipe.blog/2026/07/25/srimad-devi-bhagavatam-verse-mapped-version/" target="_blank" rel="noopener noreferrer" style="color: #0284c7; text-decoration: none; font-weight: 500;">ventpipe.blog</a></p>
        </footer>

        <!-- footer class="doc-footer" style="margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border-color, #e2e8f0); text-align: center; color: var(--text-muted, #64748b); font-size: 0.85rem;">
            <p>
                <strong>Source Text Citation:</strong><br>
                <em>Śrīmad Devī Bhāgavatam</em> — Translated by Swami Vijñanananda (1921)<br>
            </p>
        </footer-->
    </div>
    <script>
        function toggleAll(open) {{
            document.querySelectorAll('.verse-details').forEach(el => {{
                el.open = open;
            }});
        }}
    </script>
</body>
</html>"""
    return html_content

def extract_sort_key(filepath):
    """Extracts numerical book and chapter for accurate sequential sorting."""
    match = re.search(r'B(\d+).*?C(\d+)', filepath, re.IGNORECASE)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return (0, 0)

def process_file(input_filepath, prev_link=None, next_link=None):
    if not os.path.exists(input_filepath):
        print(f"File not found: {input_filepath}")
        return

    with open(input_filepath, 'r', encoding='utf-8') as f:
        text_content = f.read()

    title, verses = parse_interleaved_text(text_content)

    base_name = re.sub(r'\.interleaved_master(\.txt)?$', '', input_filepath)
    if base_name == input_filepath:
        base_name = os.path.splitext(input_filepath)[0]

    md_out = f"{base_name}.md"
    html_out = f"{base_name}.html"

    # Clean legacy output files
    for legacy in [f"{base_name}.interleaved_master.html", f"{base_name}.interleaved_master.md"]:
        if os.path.exists(legacy):
            os.remove(legacy)

    # Use root-relative paths for clean serving across subfolders
    css_rel_path = "/res/style.css"
    index_rel_path = "/index.html"

    with open(md_out, 'w', encoding='utf-8') as f:
        f.write(generate_markdown(title, verses))

    with open(html_out, 'w', encoding='utf-8') as f:
        f.write(generate_html(
            title, 
            verses, 
            css_rel_path=css_rel_path, 
            index_rel_path=index_rel_path,
            prev_link=prev_link,
            next_link=next_link
        ))

    print(f"✅ Generated Markdown: {md_out}")
    print(f"✅ Generated HTML:     {html_out}")

def process_books(book_numbers=list(range(1, 13))):
    print(f"🚀 Starting conversion run for Books: {book_numbers}\n" + "─" * 60)
    
    # 1. Discover all files across requested books
    all_files = []
    for b_num in book_numbers:
        book_dir = f"datafiles/B{b_num:02d}"
        if not os.path.exists(book_dir):
            book_dir = f"datafiles/B{b_num}"
            
        if not os.path.exists(book_dir):
            print(f"⚠️ Directory not found: {book_dir}. Skipping...")
            continue

        for root, _, files in os.walk(book_dir):
            for file in files:
                if file.endswith(".interleaved_master.txt"):
                    all_files.append(os.path.join(root, file))

    # 2. Sort files sequentially across books
    all_files.sort(key=extract_sort_key)
    total_files = len(all_files)

    # 3. Process each file with Next/Prev context
    for idx, full_path in enumerate(all_files):
        print(f"  🎯 Converting: {full_path}")
        
        # Compute html target path relative to web root
        prev_link = None
        next_link = None

        if idx > 0:
            prev_base = re.sub(r'\.interleaved_master(\.txt)?$', '', all_files[idx - 1])
            prev_link = f"/{prev_base}.html"

        if idx < total_files - 1:
            next_base = re.sub(r'\.interleaved_master(\.txt)?$', '', all_files[idx + 1])
            next_link = f"/{next_base}.html"

        process_file(full_path, prev_link=prev_link, next_link=next_link)

    print("─" * 60)
    print(f"✨ Converted {total_files} chapter file(s) with Next/Prev links for Books {book_numbers}.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        process_file(sys.argv[1])
    else:
        process_books(list(range(1, 13)))
