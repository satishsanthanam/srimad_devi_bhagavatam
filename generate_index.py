#!/usr/bin/env python3
import os
import re
import time
import subprocess

# Version identifier for cache-busting
CSS_VERSION = f"v={int(time.time())}"

def extract_chapter_title(html_path):
    """Extracts chapter title from <div class="chapter-desc"> in the target HTML file."""
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Look for <div class="chapter-desc"...>Title Here</div>
        match = re.search(r'<div\s+class="chapter-desc"[^>]*>(.*?)</div>', content, re.DOTALL | re.IGNORECASE)
        if match:
            # Strip inner HTML tags if any exist
            title = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            return title
    except Exception as e:
        print(f"  ⚠️ Warning reading {html_path}: {e}")
    
    return ""

def build_index_page(root_dir="."):
    print(f"🔍 Generating row-wise index.html by scanning: {root_dir}")
    
    books_data = {}

    for folderpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".html") and filename != "index.html":
                full_path = os.path.join(folderpath, filename)
                rel_path = os.path.relpath(full_path, root_dir).replace("\\", "/")
                
                # Display name e.g., "1.1"
                display_name = filename.replace(".html", "").replace(".interleaved_master", "")
                
                parts = display_name.split(".")
                book_num = parts[0] if len(parts) > 1 else "1"
                
                book_key = f"Book {book_num}"
                if book_key not in books_data:
                    books_data[book_key] = []
                
                # Extract chapter title from the file
                title = extract_chapter_title(full_path)
                    
                books_data[book_key].append((display_name, title, rel_path))

    sorted_book_keys = sorted(books_data.keys(), key=lambda x: int(re.search(r'\d+', x).group()))

    books_sections_html = ""
    for idx, b_key in enumerate(sorted_book_keys):
        chapters = books_data[b_key]
        # Sort chapters numerically (1.1, 1.2 ... 1.20)
        chapters.sort(key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x[0])])
        
        # Extract numerical book integer for constructing IDs like 'B01', 'B09'
        b_num_match = re.search(r'\d+', b_key)
        b_num_int = int(b_num_match.group()) if b_num_match else (idx + 1)
        book_anchor_id = f"B{b_num_int:02d}"  # Creates B01, B02 ... B09
        
        rows_html = ""
        for ch_num, ch_title, rel_path in chapters:
            title_display = f" — {ch_title}" if ch_title else ""
            rows_html += f"""
            <div class="chapter-row">
                <span class="chapter-num">{ch_num}</span>
                <span class="chapter-title-text">{ch_title if ch_title else 'Chapter ' + ch_num}</span>
                <a href="{rel_path}" class="btn-read">READ</a>
            </div>"""

        open_attr = "open" if idx == 0 else "" 

        books_sections_html += f"""
        <details class="book-card" id="{book_anchor_id}" {open_attr}>
            <summary class="book-summary">
                <span class="book-title">{b_key}</span>
                <span class="badge badge-count">{len(chapters)} Chapters</span>
            </summary>
            <div class="chapter-list">
                {rows_html}
            </div>
        </details>"""

    index_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Śrīmad Devī Bhāgavatam — Master Index</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Cache-Busted Stylesheets -->
    <link rel="stylesheet" href="res/style.css?{CSS_VERSION}">
    
    <!-- Pagefind Static Search Assets -->
    <link href="pagefind/pagefind-ui.css?{CSS_VERSION}" rel="stylesheet">
    
    <style>
        html {{
            scroll-behavior: smooth;
        }}
        .book-card {{
            background: var(--card-bg, #ffffff);
            border: 1px solid var(--border-color, #e2e8f0);
            border-radius: 10px;
            margin-bottom: 16px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
            overflow: hidden;
            transition: border-color 0.15s ease;
            scroll-margin-top: 2rem;
        }}
        .search-container {{
            background: var(--card-bg, #ffffff);
            border: 1px solid var(--border-color, #e2e8f0);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .book-card[open] {{
            border-color: var(--border-hover, #cbd5e1);
        }}
        .book-summary {{
            padding: 16px 20px;
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--san-label, #15803d);
            cursor: pointer;
            user-select: none;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background-color: var(--card-bg, #ffffff);
            transition: background-color 0.15s ease;
        }}
        .book-summary:hover {{
            background-color: #f8fafc;
        }}
        .book-summary::-webkit-details-marker {{
            display: none;
        }}
        .badge-count {{
            background-color: var(--eng-bg, #f8fafc);
            color: var(--text-muted, #64748b);
            border-color: var(--border-color, #e2e8f0);
        }}

        /* Row-wise Chapter Index Styling */
        .chapter-list {{
            padding: 12px 16px;
            border-top: 1px solid var(--border-color, #e2e8f0);
            display: flex;
            flex-direction: column;
            gap: 8px;
            background-color: #ffffff;
        }}
        .chapter-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 14px;
            background-color: var(--san-bg, #f0fdf4);
            border: 1px solid var(--san-border, #bbf7d0);
            border-radius: 6px;
            transition: all 0.15s ease;
        }}
        .chapter-row:hover {{
            background-color: #dcfce7;
            border-color: var(--accent-primary, #15803d);
        }}
        .chapter-num {{
            font-weight: 700;
            color: var(--san-label, #166534);
            min-width: 55px;
            font-size: 0.9rem;
        }}
        .chapter-title-text {{
            flex-grow: 1;
            padding: 0 12px;
            color: var(--text-primary, #0f172a);
            font-size: 0.925rem;
            font-weight: 500;
        }}
        .btn-read {{
            padding: 5px 14px;
            border: 1px solid var(--san-border, #bbf7d0);
            border-radius: 5px;
            background-color: #ffffff;
            color: var(--san-label, #15803d);
            font-size: 0.8rem;
            font-weight: 700;
            text-decoration: none;
            letter-spacing: 0.05em;
            transition: all 0.15s ease;
            white-space: nowrap;
        }}
        .btn-read:hover {{
            background-color: var(--san-label, #15803d);
            color: #ffffff;
        }}

        @media (max-width: 640px) {{
            .book-summary {{
                padding: 14px 16px;
                font-size: 1rem;
            }}
            .chapter-row {{
                flex-wrap: wrap;
                gap: 6px;
                padding: 10px;
            }}
            .chapter-title-text {{
                width: 100%;
                padding: 2px 0;
            }}
            .btn-read {{
                margin-left: auto;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="doc-header">
            <div class="breadcrumb">Scriptures</div>
            <h1>Śrīmad Devī Bhāgavatam</h1>
            <p style="color: var(--text-muted, #64748b); margin-bottom: 8px; font-size: 0.95rem;">
                English translation by <strong>Swami Vijñanananda (1921)</strong> 
            </p>
            <p style="color: var(--text-muted, #64748b); margin-bottom: 16px; font-size: 0.9rem;">
                Select a chapter or search across Sanskrit text and English translations below.
            </p>
            <div class="controls">
                <button class="btn btn-primary" onclick="toggleBooks(true)">Expand All Books</button>
                <button class="btn" onclick="toggleBooks(false)">Collapse All</button>
            </div>
        </div>

        <!-- Embedded Search UI Container -->
        <div class="search-container">
            <div id="search"></div>
        </div>

        {books_sections_html if books_sections_html else '<p>No chapter HTML files found yet.</p>'}

        <!-- Site Footer -->
        <footer class="doc-footer" style="margin-top: 3rem; padding: 1.5rem 0; border-top: 1px solid #e2e8f0; text-align: center; color: #64748b; font-size: 0.9rem;">
            <p><strong>🙏 Shri Krishnarpanam Asthu 🙏</strong> | Maintained &amp; published via <a href="https://ventpipe.blog" target="_blank" rel="noopener noreferrer" style="color: #0284c7; text-decoration: none; font-weight: 500;">ventpipe.blog</a></p>
        </footer>
    </div>

    <!-- Pagefind JS Script Initialization -->
    <script src="pagefind/pagefind-ui.js"></script>
    <script>
        window.addEventListener('DOMContentLoaded', (event) => {{
            new PagefindUI({{ 
                element: "#search", 
                showSubResults: true,
                showImages: false
            }});

            // Auto-expand and scroll to target book if hashtag is present (e.g., #B09)
            if (window.location.hash) {{
                const targetEl = document.querySelector(window.location.hash);
                if (targetEl && targetEl.tagName === 'DETAILS') {{
                    targetEl.open = true;
                    setTimeout(() => {{
                        targetEl.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    }}, 100);
                }}
            }}
        }});

        function toggleBooks(open) {{
            document.querySelectorAll('.book-card').forEach(el => {{
                el.open = open;
            }});
        }}
    </script>
</body>
</html>"""

    index_path = os.path.join(root_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)

    print(f"✅ Created row-wise master index: {index_path}")

def run_pagefind(root_dir="."):
    """Invokes the Pagefind CLI via python module pagefind_bin."""
    print("🔎 Building Pagefind search index...")
    try:
        result = subprocess.run(
            ["python3", "-m", "pagefind_bin", "--site", root_dir],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print("✅ Search index built successfully in ./pagefind directory!")
    except subprocess.CalledProcessError as e:
        print("❌ Failed to build search index:")
        print(e.stderr)

if __name__ == "__main__":
    build_index_page(".")
    run_pagefind(".")