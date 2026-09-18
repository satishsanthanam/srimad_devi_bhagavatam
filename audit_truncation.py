import os
import re
import glob

def audit_check_begin_mismatch(filepath):
    """
    Audits an interleaved master file specifically for HEAD / Beginning mismatches:
      1. Missing Speaker Attributions (when Sanskrit or OCR has speaker declarations).
      2. Invalid starting characters (lowercase, unexpected symbols).
    Prints findings directly to console.
    """
    if not os.path.exists(filepath):
        print(f"⚠️ File not found: {filepath}")
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.split('----------------------------------------')
    issues = []

    valid_start_chars = (
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
        '“', '"', "‘", "'", '(', '['
    )

    speaker_att_regex = re.compile(
        r'^(?:[A-Z\u0100-\u017F\u0180-\u024F\s\.\'\-]+\s+(?:said|spoke|asked|replied|cried|chanted|sing|sings|prayed|addressed)\s*(?::--|:|--|-)?)\s*',
        re.IGNORECASE
    )

    for idx, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue

        header_match = re.search(r'(\[Ch \d+ Verse [^\]]+\])', block)
        verse_id = header_match.group(1) if header_match else f"Block {idx + 1}"

        eng_match = re.search(r'English Translation:\n(.*)', block, re.DOTALL)
        if not eng_match:
            continue

        eng_text = eng_match.group(1).strip()
        if not eng_text:
            continue

        sanskrit_part = block.split("English Translation:")[0]

        # Check 1: Check if Sanskrit or verse header indicates a speaker
        # Matches Sanskrit speaker words OR common English speaker names in headers/verses
        sanskrit_has_speaker = bool(re.search(r'(?:उवाच|ऊचुः|उवाचः|said|spoke|asked)', sanskrit_part, re.IGNORECASE))
        english_has_speaker = bool(speaker_att_regex.match(eng_text))

        if sanskrit_has_speaker and not english_has_speaker:
            snippet = eng_text[:40].replace('\n', ' ')
            issues.append((verse_id, f"HEAD TRUNCATED (Missing Speaker Prefix) ──► \"{snippet}...\""))

        # Check 2: Invalid Start Character (Lowercase / Bad Prefix)
        elif not eng_text.startswith(valid_start_chars):
            snippet = eng_text[:40].replace('\n', ' ')
            issues.append((verse_id, f"HEAD TRUNCATED (Invalid Start Char) ──► \"{snippet}...\""))

    # Print output directly
    if issues:
        print(f"❌ {filepath} — Found {len(issues)} Head Mismatch issue(s):")
        for verse_id, issue_desc in issues:
            print(f"   └── {verse_id}: {issue_desc}")
    else:
        print(f"✅ {filepath} — No Head Mismatches found.")

    return issues

def audit_interleaved_file(filepath):
    """
    Scans a single interleaved file for potential English translation 
    truncation issues and reports any suspicious sentence ends.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into verse blocks delimited by '----------------------------------------'
    blocks = content.split('----------------------------------------')
    
    issues = []

    for idx, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue

        # Extract the verse header (e.g., [Ch 5 Verse 1])
        header_match = re.search(r'(\[Ch \d+ Verse [^\]]+\])', block)
        verse_id = header_match.group(1) if header_match else f"Block {idx + 1}"

        # Extract English Translation block
        eng_match = re.search(r'English Translation:\n(.*)', block, re.DOTALL)
        if not eng_match:
            continue

        eng_text = eng_match.group(1).strip()
        
        # Strictly final punctuation marks (including closing quotes/parentheses)
        valid_endings = (
            '.', '!', '?', '***',
            '”', '"', "’", "'", ')', ']'
        )

        if eng_text and not eng_text.endswith(valid_endings):
            # Capture the last ~40 characters for display
            tail = eng_text[-40:].replace('\n', ' ')
            issues.append((verse_id, tail))

    return issues


def run_book_audit(base_dir="datafiles/B02"):
    """
    Scans all chapters within Book 2 directory for truncation issues.
    """
    print("=" * 70)
    print("      INTERLEAVED FILE TRUNCATION AUDIT REPORT")
    print("=" * 70)

    # Search for all interleaved master files under base_dir (e.g., B02/C01/...interleaved_master.txt)
    pattern = os.path.join(base_dir, "C*", "*.interleaved_master.txt")
    files = sorted(glob.glob(pattern))

    if not files:
        # Fallback search if files are in current working directory structure
        pattern = os.path.join(".", "**", "*.interleaved_master.txt")
        files = sorted(glob.glob(pattern, recursive=True))

    if not files:
        print(f"⚠️  No interleaved files found matching pattern. Please check your path.")
        return

    total_issues = 0

    for filepath in files:
        filename = os.path.basename(filepath)
        issues = audit_interleaved_file(filepath)

        if issues:
            print(f"\n❌ {filename} — Found {len(issues)} issue(s):")
            for verse_id, snippet in issues:
                print(f"   └── {verse_id}: \"...{snippet}\"")
            total_issues += len(issues)
        else:
            print(f"✅ {filename} — All blocks cleanly terminated.")

        audit_check_begin_mismatch(filepath)

    print("\n" + "=" * 70)
    if total_issues == 0:
        print("🎉 SUCCESS: No truncations found across all audited chapters!")
    else:
        print(f"⚠️  TOTAL TRUNCATIONS DETECTED: {total_issues}")
    print("=" * 70)


if __name__ == "__main__":
    # Adjust directory path here if your folder structure is different
    run_book_audit(base_dir=".")
