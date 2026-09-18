#!/usr/bin/env python3
import os
import shutil
import gen_html_md as converter
import generate_index as indexer
import patch_titles as patcher


def clean_previous_builds(
    root_dir=".", data_dir="datafiles", pagefind_dir="pagefind"
):
    """Deletes existing generated HTML/MD files and the pagefind directory for a clean build."""
    print("🧹 --- CLEANING PREVIOUS BUILD ARTIFACTS ---")

    # 1. Clean HTML and MD files in datafiles/
    deleted_files = 0
    if os.path.exists(data_dir):
        for folderpath, _, filenames in os.walk(data_dir):
            for filename in filenames:
                if filename.endswith(".html") or filename.endswith(".md"):
                    file_path = os.path.join(folderpath, filename)
                    try:
                        os.remove(file_path)
                        deleted_files += 1
                    except Exception as e:
                        print(f"  ⚠️ Could not remove {file_path}: {e}")
        print(
            f"  ✅ Removed {deleted_files} generated .html and .md files from {data_dir}/"
        )

    # 2. Clean root index.html
    root_index = os.path.join(root_dir, "index.html")
    if os.path.exists(root_index):
        try:
            os.remove(root_index)
            print("  ✅ Removed root index.html")
        except Exception as e:
            print(f"  ⚠️ Could not remove {root_index}: {e}")

    # 3. Clean pagefind index directory
    pagefind_path = os.path.join(root_dir, pagefind_dir)
    if os.path.exists(pagefind_path):
        try:
            shutil.rmtree(pagefind_path)
            print(f"  ✅ Removed existing {pagefind_dir}/ directory")
        except Exception as e:
            print(f"  ⚠️ Could not remove {pagefind_path}: {e}")

    print("✨ Cleanup complete!\n")


def main():
    print("🚀 --- EXECUTING COMPLETE BUILD PIPELINE --- 🚀\n")

    # Step 0: Clean previous build artifacts
    clean_previous_builds()

    # Step 1: Parse and output HTML/Markdown for all 12 books
    print("Step 1: Converting master text files...")
    converter.process_books(list(range(1, 13)))
    print()

    # Step 1.5: Inject descriptive chapter titles into generated HTML
    print("Step 1.5: Patching chapter descriptive titles...")
    patcher.patch_html_files("datafiles")
    print()

    # Step 2: Build main index.html
    print("Step 2: Rebuilding index.html with search container...")
    indexer.build_index_page(".")
    print()

    # Step 3: Run Pagefind static indexing
    print("Step 3: Indexing site content for fast client search...")
    indexer.run_pagefind(".")
    print()

    print("🎉 --- BUILD COMPLETE! READY TO TEST ON ORACLE --- 🎉")


if __name__ == "__main__":
    main()
