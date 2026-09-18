Here is a tailored, professional **`README.md`** designed specifically for your **Śrīmad Devī Bhāgavatam** project repository.

---

# Śrīmad Devī Bhāgavatam (Verse-Mapped Digital Edition)

A high-performance, responsive static web publication and search platform for the complete **Śrīmad Devī Bhāgavatam Mahāpurāṇa** across all 12 Skandhas (318 Chapters). The platform provides side-by-side Sanskrit Devanagari text, English translations by Swami Vijñanananda (1921), dynamic chapter index navigation, and client-side static site search.

🔗 **Live Application**: [https://satishsanthanam.bitbucket.io/index.html](https://satishsanthanam.bitbucket.io/index.html?utm_source=gemini)

📂 **Bitbucket Pipeline & Source**: Hosted on Bitbucket Pages with automated CI/CD static site builds.

---

## Features

* **Complete 12 Skandhas Coverage**: Full digital edition encompassing all 318 Adhyāyas (Chapters) formatted into clean, verse-mapped HTML pages.


* **Dynamic Row-Wise Index**: Master Table of Contents displaying full chapter descriptions (`n.m -- <title> [READ]`) with collapsible Skandha cards.


* **Verse-Level Text Mapping**: Collapsible accordion view (`<details>`) per verse featuring Devanagari Sanskrit text alongside matching English translations.


* **Static Client-Side Search**: Embedded **Pagefind** search engine enabling instant full-text search across Sanskrit and English translations without a server backend.


* **Cache-Busted Automated Build**: Custom Python processing pipeline integrated with Bitbucket Pipelines for automated deployment.


* **Responsive & Accessible UI**: Optimized for mobile and desktop reading with custom CSS styling and smooth hashtag navigation (`#B01` through `#B12`).



---

## Repository & Project Structure

```text
.
├── process_for_web.py      # Master build pipeline controller
├── gen_html_md.py          # Master text converter (Parses source text into HTML/MD)
├── patch_titles.py         # Injects chapter descriptions into target HTML files
├── generate_index.py       # Scans HTML files & builds row-wise index.html + Pagefind
├── bitbucket-pipelines.yml # CI/CD deployment configuration
├── datafiles/              # Generated output directory (B01/C01/1.1.html ...)
│   ├── B01/
│   ├── ...
│   └── B12/
├── res/
│   └── style.css           # Global stylesheet
└── index.html              # Generated master entrypoint page

```

---

## Build Pipeline Architecture

The site build pipeline executes automatically via Bitbucket Pipelines on every push to `main`:

```
┌─────────────────────────┐
│ Source Text / Master MD │
└────────────┬────────────┘
             │
             ▼
   [1] gen_html_md.py          --> Converts master files to raw HTML/MD per book/chapter
             │
             ▼
   [2] patch_titles.py         --> Injects descriptive <div class="chapter-desc"> tags
             │
             ▼
   [3] generate_index.py       --> Scans datafiles, extracts titles, outputs row-wise index.html
             │
             ▼
   [4] Pagefind CLI            --> Generates static client search index inside ./pagefind
             │
             ▼
┌─────────────────────────┐
│ Bitbucket Pages Deploy  │   --> Pushed directly to 'site-build:pages' deployment branch
└─────────────────────────┘

```

---

## Local Setup & Development

### Prerequisites

* Python 3.10+
* `pip install "pagefind[bin]" markdown`


### Running the Build Locally

1. **Clone the Repository**:
```bash
git clone https://bitbucket.org/satishsanthanam/satishsanthanam.bitbucket.io.git
cd satishsanthanam.bitbucket.io

```


2. **Execute Full Build Pipeline**:
```bash
python process_for_web.py

```


This cleans previous build artifacts, generates all 12 Skandhas, patches chapter titles, builds `index.html`, and indexes search content via Pagefind.


3. **Preview Locally**:
```bash
python -m http.server 8000

```


Open `http://localhost:8000` in your browser.

---

## Primary Sources & Credits

* **English Translation**: *Śrīmad Devī Bhāgavatam* — Translated by Swami Vijñanananda (Hari Prasanna Chatterji), 1921.


* **Developer & Maintainer**: [Satish Santhanam](https://ventpipe.blog?utm_source=gemini) — Engineered dataset converter scripts, HTML patching pipeline, and Bitbucket CI/CD integration.


* **Publication Blog**: [ventpipe.blog](https://www.google.com/search?q=https://ventpipe.blog/2026/07/25/srimad-devi-bhagavatam-verse-mapped-version/&utm_source=gemini)

* **AI Collaborator**: Google Gemini AI — Code architecture, script optimization, and UI template engineering.

---

## License & Dedication

**🙏 Shri Krishnarpanam Asthu 🙏**

Maintained as part of an open-access digital Sanskrit scripture preservation initiative. Free for non-commercial, educational, and research utilization.