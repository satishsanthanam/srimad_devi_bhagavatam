#!/usr/bin/env python3
import os
import re
import sys
import difflib
import unicodedata
from collections import Counter
from rapidfuzz import fuzz

# ⚙️ GLOBAL MAPPINGS & CONFIGURATION DIRECTIVES
DEVA_DIGITS_MAP = {'०':'0','१':'1','२':'2','३':'3','४':'4','५':'5','६':'6','७':'7','८':'8','९':'9'}
DEVA_NUMS = "०१२३४५६७८९"

CLEANUP_RULES = {
    r"Book\s*[I\d]*\s*Chapter\s*[IVXLCDM\d]+\s+\d+": "", 
    r"<\_<": "sweeter",                         
    r"\s+i\b": " ॥",                            
    r"FATT\s+78": "॥ 78",
    r"\bJtis\b": "It is",
    
    # Trim inner spaces so capturing '\1' gets clean digits without extra spaces
    r'[\.।]\s*([०-९\d\-]+(?:\s+[०-९\d\-]+)*)\s*[\.।]\s*$': r'॥ \1 ॥',
}

COLOPHON_PATTERNS = [
    r"इति\s+श्रीमद्?देवी",
    r"द्वितीय\s*स्कन्धे",
    r"स्कन्धे",
    r"अध्यायः?",
    r"ध्यायः?",
    r"[शषस]्वरो?उ?ध्याः?",  # Matches corrupted OCR variants like 'श्वरोउध्याः'
    r"महापुराणे",
]

COLOPHON_CLEANUP_RULES = [
    # Fix corruptions like 'श्वरोउध्याः ॥ ६ ॥' -> 'षष्ठोऽध्यायः ॥ ६ ॥'
    (r"श्वरोउध्याः\s*॥\s*([०-९0-9]+)\s*॥", r"षष्ठोऽध्यायः ॥ \1 ॥"),
    (r"द्वितीयकन्धे", r"द्वितीयस्कन्धे"),
]

import os
import re

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

def clean_colophon_text(text: str) -> str:
    """Normalizes OCR-corrupted colophon phrases and chapter signatures."""
    for pattern, replacement in COLOPHON_CLEANUP_RULES:
        text = re.sub(pattern, replacement, text)
    return text

def is_colophon_line(line: str) -> bool:
    """Detects if a Devanagari line is an end-of-chapter colophon rather than a verse."""
    cleaned = line.strip()
    if not cleaned:
        return False
        
    for pattern in COLOPHON_PATTERNS:
        if re.search(pattern, cleaned):
            return True
            
    return False

def sanitize_sanskrit_text(text):
    """
    Strips out injected OCR headers, chapter markers, and page numbers
    from Sanskrit text blocks.
    """
    if not text:
        return ""

    junk_patterns = [
        r'^\s*Book\s+[I|V|X|L|C|D|M\d]+\s+Chapter\s+[I|V|X|L|C|D|M\d]+.*$',  # Book III Chapter XXV
        r'^\s*CHAPTER\s+[I|V|X|L|C|D|M\d]+.*$',                             # CHAPTER 25
        r'^\s*Book\s+[I|V|X|L|C|D|M\d]+.*$',                                 # Book III
        r'^\s*Page\s+\d+.*$',                                               # Page 123
        r'^\s*\d+\s*$',                                                     # Standalone line numbers/page numbers
        r'^\s*[SŠŚ]rimad\s*devi\s*bh[aā]gavatam.*$'                         # Running header titles
    ]

    combined_regex = re.compile('|'.join(junk_patterns), re.IGNORECASE)

    cleaned_lines = []
    for line in text.splitlines():
        if not combined_regex.match(line.strip()):
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()
 
def strip_diacritics(text):
    """Strips diacritics from strings to equalize text for raw token matching passes."""
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def deva_to_int(deva_str):
    """Converts Devanagari numerals to standard integers."""
    return int("".join(str(DEVA_NUMS.index(c)) for c in deva_str if c in DEVA_NUMS))

def determine_verse_header(chapter_num, current_extracted_num, last_processed_verse):
    """
    Infers range labels (e.g., '1-2') when OCR only prints the trailing 
    verse marker (e.g., '॥ 2 ॥') for multi-verse blocks.
    Returns string range label (e.g., '1-2' or '5').
    """
    if current_extracted_num is None:
        return str(last_processed_verse + 1)
        
    # Check if this is a range string already (e.g., "5-7")
    if "-" in str(current_extracted_num):
        return str(current_extracted_num)
        
    try:
        curr_num = int(current_extracted_num)
        expected_start = last_processed_verse + 1
        
        # IF there's a gap (e.g., last was 0, current marker is 2),
        # automatically form the range "1-2"
        if curr_num > expected_start:
            return f"{expected_start}-{curr_num}"
        else:
            return str(curr_num)
    except ValueError:
        return str(current_extracted_num)
    
def extract_verse_marker_number(sanskrit_text):
    """
    Extracts verse numbers strictly from trailing danda/period markers 
    (e.g., ॥ 41 ॥, । 41 ।, or . 41 .).
    """
    # Updated marker pattern to include periods (.) alongside danda characters [॥।|]
    marker_pattern = r'[॥।|\.]\s*([\d\u0966-\u096F\-\s]+)\s*[॥।|\.]'
    matches = list(re.finditer(marker_pattern, sanskrit_text))
    
    if matches:
        raw_str = matches[-1].group(1).strip()
        
        # Remove internal whitespace between digits (e.g., "4 1" -> "41", "४ ५" -> "४५")
        raw_str = re.sub(r'(?<=\d)\s+(?=\d)', '', raw_str)
        raw_str = re.sub(r'(?<=[०-९])\s+(?=[०-९])', '', raw_str)
        
        # Convert Devanagari numerals to ASCII
        norm_str = "".join(DEVA_DIGITS_MAP.get(c, c) for c in raw_str)
        
        found = re.findall(r'\d+\s*-\s*\d+|\d+', norm_str)
        if found:
            return found[0].replace(" ", "")

    # Fallback pattern for lines ending with digits
    fallback_pattern = r'([\d\u0966-\u096F\-\s]+)\s*[॥।|\.]?\s*$'
    fallback_match = re.search(fallback_pattern, sanskrit_text.strip())
    if fallback_match:
        raw_str = fallback_match.group(1).strip()
        
        raw_str = re.sub(r'(?<=\d)\s+(?=\d)', '', raw_str)
        raw_str = re.sub(r'(?<=[०-९])\s+(?=[०-९])', '', raw_str)
        
        norm_str = "".join(DEVA_DIGITS_MAP.get(c, c) for c in raw_str)
        found = re.findall(r'\d+\s*-\s*\d+|\d+', norm_str)
        if found:
            return found[0].replace(" ", "")

    return None

# ==============================================================================
# 🧩 STAGE 1: SANSKRIT PRISTINE DATABASE PARSER
# ==============================================================================
def load_clean_sanskrit(filepath):
    """Parses a clean Sanskrit file into a dictionary, supporting hybrid Devanagari/ASCII digits."""
    if not os.path.exists(filepath):
        print(f"⚠️ Warning: Pristine Sanskrit source file '{filepath}' not found.")
        return {}, "", ""
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    colophon_match = re.search(r'(इति\s+श्रीमद्देवीभागवते.*॥\s*[\d०१२३४५६७८९\.]+\s*॥)', content, re.DOTALL)
    colophon_text = colophon_match.group(1).strip() if colophon_match else ""
    if colophon_text:
        content = content.replace(colophon_match.group(1), "")
        
    verse_dict = {}
    pattern = re.compile(r'(.*?)(॥\s*([०१२३४५६७८९\d]+)\s*॥)', re.DOTALL)
    matches = list(pattern.finditer(content))
    
    chapter_title = ""
    for i, match in enumerate(matches):
        text_block = match.group(1).strip()
        raw_num = match.group(3)
        
        if any(c in DEVA_NUMS for c in raw_num):
            v_num = deva_to_int(raw_num)
        else:
            v_num = int(raw_num)
        
        if i == 0:
            title_match = re.match(r'^([\s\S]*?)(ॐ|शौनक|सूत|\n\n)', text_block)
            if title_match:
                chapter_title = title_match.group(1).strip()
                text_block = text_block[len(chapter_title):].strip()
                
        verse_dict[v_num] = text_block + f" ॥ {raw_num} ॥"
        
    return verse_dict, chapter_title, colophon_text

# ==============================================================================
# 🧩 STAGE 2: CONFIGURATION RANGE & PARSING UTILITIES
# ==============================================================================
def parse_chapters_range(config_str):
    """Parses ranges from book.cfg (e.g., '1-20' or '11')."""
    config_str = config_str.strip()
    if not config_str:
        return []
    if '-' in config_str:
        match = re.match(r'^(\d+)-(\d+)$', config_str)
        if match:
            return list(range(int(match.group(1)), int(match.group(2)) + 1))
    if config_str.isdigit():
        return [int(config_str)]
    return []

def parse_range_label(label_str, max_verse):
    """Converts verse label identifiers (e.g. '5-7') into discrete integer keys."""
    digits = [int(d) for d in re.findall(r'\d+', label_str)]
    if not digits:
        return []
    if len(digits) == 1:
        return [digits[0]] if digits[0] <= max_verse else []
    
    start, end = digits[0], digits[1]
    if end < start:  
        return [start] if start <= max_verse else []
    return list(range(start, min(end + 1, max_verse + 1)))

def extract_linguistic_blocks(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    compiled_blocks, active_chunk = [], []
    active_type = None

    # Pre-compile header/footer junk patterns
    junk_line_regex = re.compile(
        r'^\s*('
        r'Book\s+[I|V|X|L|C|D|M\d]+\s+Chapter\s+[I|V|X|L|C|D|M\d]+|'
        r'CHAPTER\s+[I|V|X|L|C|D|M\d]+|'
        r'Book\s+[I|V|X|L|C|D|M\d]+|'
        r'Page\s+\d+|'
        r'[\d\s]+|'
        # Matches running title variants (Šrimaddevibhāgavatam, Srimaddevibhagavatam, etc.)
        r'[SŠŚ]rimad\s*devi\s*bh[aā]gavatam'
        r')\s*$',
        re.IGNORECASE
    )
    
    for line in lines:
        cleaned_line = line.strip()
        for pattern, replacement in CLEANUP_RULES.items():
            cleaned_line = re.sub(pattern, replacement, cleaned_line)
        cleaned_line = cleaned_line.strip()
        
        # 1. Skip empty lines and layout noise early
        if not cleaned_line or cleaned_line in ("~~", ">~", "~ te"):
            continue

        # 2. Skip injected OCR running headers/footers BEFORE block classification
        if junk_line_regex.match(cleaned_line):
            continue

        if re.match(r'^CHAPTER\s+[IVXLCDM]+$', cleaned_line, re.IGNORECASE):
            continue
            
        if "ध्याय" in cleaned_line or re.match(r'^इति\s+(?:श्री|द्रव्य|शुभ|अध्याय)', cleaned_line):
            continue
            
        deva_count = len(re.findall(r'[\u0900-\u097F]', cleaned_line))
        line_type = "SANSKRIT" if deva_count > 2 else "ENGLISH"
        
        if active_type is None:
            active_type = line_type
        if line_type != active_type:
            raw_block = "\n".join(active_chunk)
            if active_type == "SANSKRIT":
                raw_block = sanitize_sanskrit_text(raw_block)
            compiled_blocks.append((active_type, raw_block))
            active_chunk = [cleaned_line]
            active_type = line_type
        else:
            active_chunk.append(cleaned_line)
            
    if active_chunk:
        raw_block = "\n".join(active_chunk)
        if active_type == "SANSKRIT":
            raw_block = sanitize_sanskrit_text(raw_block)
        compiled_blocks.append((active_type, raw_block))

    return compiled_blocks

# ==============================================================================
# 🧩 STAGE 3: INPUT SANITIZATION & SEQUENCE ALIGNMENT ENGINE
# ==============================================================================
def sanitize_layout_pollution(ocr_text):
    """Purges cross-column line bounces using a local 20-word historical window."""
    words = ocr_text.split()
    sanitized_words = []
    seen_phrases = {}
    
    i = 0
    while i < len(words):
        if i + 2 < len(words):
            phrase_key = " ".join([w.lower().strip(".,!\"';:-?«»()[]") for w in words[i:i+3]])
            if phrase_key in seen_phrases and (len(sanitized_words) - seen_phrases[phrase_key]) < 20:
                i += 3  
                continue
            seen_phrases[phrase_key] = len(sanitized_words)
        sanitized_words.append(words[i])
        i += 1
        
    return " ".join(sanitized_words)

def align_ocr_to_wisdom(ocr_text, wisdom_text):
    ocr_matches = list(re.finditer(r'\b\w+\b', ocr_text))
    if not ocr_matches:
        return re.sub(r'\s+', ' ', ocr_text)
    ocr_words_norm = [strip_diacritics(m.group().lower()) for m in ocr_matches]
    
    wisdom_words = []
    for match in re.finditer(r'\b\w+\b', wisdom_text):
        wisdom_words.append({
            'norm': strip_diacritics(match.group().lower()),
            'start': match.start(),
            'end': match.end()
        })
        
    if not wisdom_words:
        return re.sub(r'\s+', ' ', ocr_text)
        
    M = len(ocr_words_norm)
    N = len(wisdom_words)
    
    ocr_counter = Counter(ocr_words_norm)
    best_overlap = -1
    rough_center = 0
    
    for i in range(max(0, N - M + 1)):
        win_words = [wisdom_words[k]['norm'] for k in range(i, min(N, i + M))]
        win_counter = Counter(win_words)
        overlap = sum((ocr_counter & win_counter).values())
        if overlap > best_overlap:
            best_overlap = overlap
            rough_center = i
            
    search_start = max(0, rough_center - 80)
    search_end = min(N, rough_center + M + 150)
    local_wisdom = wisdom_words[search_start:search_end]
    L = len(local_wisdom)
    
    best_ratio = -1
    best_start_idx = search_start
    best_end_idx = min(N, search_start + M)
    
    min_size = max(1, M - 40)
    max_size = min(N, M + 100)
    
    for w_size in range(min_size, min(L, max_size) + 1):
        for i in range(L - w_size + 1):
            window_tokens = [local_wisdom[k]['norm'] for k in range(i, i + w_size)]
            #ratio = difflib.SequenceMatcher(None, window_tokens, ocr_words_norm).ratio()
            ratio = fuzz.ratio(" ".join(window_tokens), " ".join(ocr_words_norm)) / 100.0
            if ratio > best_ratio:
                best_ratio = ratio
                best_start_idx = search_start + i
                best_end_idx = search_start + i + w_size
                
    best_char_ratio = -1
    final_start_char = wisdom_words[best_start_idx]['start'] if best_start_idx < N else 0
    final_end_char = wisdom_words[min(N - 1, best_end_idx - 1)]['end'] if best_end_idx > 0 else len(wisdom_text)
    
    for idx_s in range(max(0, best_start_idx - 3), best_start_idx + 1):
        for idx_e in range(best_end_idx, min(N + 1, best_end_idx + 4)):
            s_char = wisdom_words[idx_s]['start']
            e_char = wisdom_words[idx_e - 1]['end']
            
            while s_char > 0 and wisdom_text[s_char - 1] in (' ', '“', '"', '\n', '(', '[', '«', '-', '—', ':'):
                s_char -= 1
            while e_char < len(wisdom_text) and wisdom_text[e_char] in (' ', '”', '"', '.', '!', '?', ',', ';', '\n', ')', ']', '»', '-', '—', ':'):
                e_char += 1
                
            sub_str = wisdom_text[s_char:e_char].strip()
            char_ratio = difflib.SequenceMatcher(None, sub_str.lower(), ocr_text.lower()).ratio()
            
            if char_ratio > best_char_ratio:
                best_char_ratio = char_ratio
                final_start_char = s_char
                final_end_char = e_char
                
    raw_match = wisdom_text[final_start_char:final_end_char].strip()
    return re.sub(r'\s+', ' ', raw_match)

# ==============================================================================
# 🧩 STAGE 4: PRE-FLIGHT INTEGRITY & STRUCTURAL VALIDATOR
# ==============================================================================
def validate_input_integrity(filepath):
    """Detects alignment and script errors before execution."""
    
    if not os.path.exists(filepath):
        return True
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    last_verse = 0
    errors_found = False

    for line_idx, line in enumerate(lines, start=1):
        cleaned = line.strip()
        
        # 1. Clean OCR corruptions in colophons first
        cleaned_colophon = clean_colophon_text(cleaned)

        if is_colophon_line(line):
            continue

        if not cleaned or "अध्याय" in cleaned or "ध्याय" in cleaned or "CHAPTER" in cleaned.upper() or cleaned.startswith("इति"):
            continue
            
        #if re.search(r'[\u0900-\u097F]', cleaned) and re.search(r'\b\d+\b', cleaned):
            #print(f"💡 Input Note (Line {line_idx}): Found Western ASCII digits within a Sanskrit block: '{cleaned}'.")

        words = re.findall(r'\S+', cleaned)
        for word in words:
            if any(c in '0123456789' for c in word) and any(c in '०१२३४५६७८९' for c in word):
                print(f"❌ Input Incorrect: Mixed script numerals check at line {line_idx}: '{cleaned}'")
                errors_found = True

        if re.search(r'[\u0900-\u097F]', cleaned):
            v_marker = extract_verse_marker_number(cleaned)
            if v_marker:
                digits = re.findall(r'\d+', v_marker)
                if digits:
                    current_verse = int(digits[-1])
                    if current_verse < last_verse and not (last_verse == 68 and current_verse == 61):
                        print(f"❌ Input Incorrect: Sequence broken at line {line_idx}: '{cleaned}' (Dropped from {last_verse} to {current_verse})")
                        errors_found = True
                    else:
                        last_verse = current_verse
                        
    if errors_found:
        print(f"\n🛑 Pipeline Aborted: Fix the structural anomalies listed above in '{filepath}' before execution.")
        return False
    return True

# ==============================================================================
# 🚀 STAGE 5: BATCH PROCESSOR ORCHESTRATION LAYER
# ==============================================================================
def process_single_chapter(book_id, ch_num, book_num=2):
    ch_padded = str(ch_num).zfill(2)
    dir_path = f"datafiles/{book_id}/C{ch_padded}"
    
    file_clean_san  = f"{dir_path}/{book_num}.{ch_num}.clean_san.txt"
    file_eng_san    = f"{dir_path}/{book_num}.{ch_num}.eng_san.txt"  
    file_wisdom_ref = f"{dir_path}/{book_num}.{ch_num}.wisdom.txt"
    
    if not os.path.exists(file_eng_san) or not os.path.exists(file_wisdom_ref):
        print(f"⏭️  Skipping Path: {dir_path}/ (Data paths missing for {book_num}.{ch_num})")
        return

    print(f"🏁 Processing {book_id} Chapter {ch_num} inside {dir_path}...")

    if not validate_input_integrity(file_eng_san):
        sys.exit(1)
    
    clean_san_db, chapter_title, colophon_text = load_clean_sanskrit(file_clean_san)
    max_verse_key = max(clean_san_db.keys()) if clean_san_db else 0
    
    linguistic_blocks = extract_linguistic_blocks(file_eng_san)
    
    with open(file_wisdom_ref, 'r', encoding='utf-8') as f:
        wisdom_text_full = f.read()
        
    wisdom_text_full = re.sub(r'(?i)Chapter\s+\d+\s*-\s*On\s+[^.\n]+', '', wisdom_text_full)
    wisdom_text_full = re.sub(r'(?i)< Previous|parent:\s*Book\s+\d+|Next\s*>', '', wisdom_text_full)
    
    last_consumed_idx = 0
    last_processed_verse = 0  # Track verse sequence state across blocks
    
    master_interleaved = []
    sanskrit_log = []
    english_log = []
    
    master_interleaved.append("="*80 + f"\nSRIMAD DEVI BHAGAVATAM — BOOK {book_num}, CHAPTER {ch_num}\n" + "="*80 + "\n")
    
    idx = 0
    while idx < len(linguistic_blocks) - 1:
        type_current, text_current = linguistic_blocks[idx]
        type_next, text_next = linguistic_blocks[idx + 1]
        
        if type_current == "SANSKRIT" and type_next == "ENGLISH":
            text_san = text_current
            text_mix = text_next
            
            raw_extracted_num = extract_verse_marker_number(text_san)
            
            # Determine range header (e.g., '1-2' if last was 0 and extracted marker is 2)
            range_label = determine_verse_header(ch_num, raw_extracted_num, last_processed_verse)
            
            if range_label == "68-61":
                range_label = "69"
                
            payload_text = re.sub(r'\s+', ' ', text_mix).replace('|', '').strip()
            
            cleaned_ocr_eng = sanitize_layout_pollution(payload_text)
            best_sliding_match = align_ocr_to_wisdom(cleaned_ocr_eng, wisdom_text_full[last_consumed_idx:])
            
            if not best_sliding_match.strip():
                best_sliding_match = cleaned_ocr_eng
            
            match_pos = wisdom_text_full.find(best_sliding_match, last_consumed_idx)
            if match_pos != -1:
                last_consumed_idx = match_pos + len(best_sliding_match)
            
            target_verses = parse_range_label(range_label, max_verse_key)
            clean_verses_list = [clean_san_db[v] for v in target_verses if v in clean_san_db]
            
            if clean_verses_list:
                pristine_san_output = "\n\n".join(clean_verses_list)
            else:
                sanitized_raw_san = sanitize_sanskrit_text(text_san)
                pristine_san_output = re.sub(r'\s+', ' ', sanitized_raw_san).strip()
            
            flat_ocr_san = re.sub(r'\s+', ' ', text_san).strip()
            flat_cln_san = re.sub(r'\s+', ' ', pristine_san_output).strip()
            
            if 1 in target_verses and chapter_title:
                pristine_san_output = f"{chapter_title}\n\n\n{pristine_san_output}"
                
            if max_verse_key in target_verses and colophon_text:
                pristine_san_output = f"{pristine_san_output}\n\n{colophon_text}"
            
            prefix = f"Ch {ch_num} Verse {range_label}"
            
            master_interleaved.append(f"[{prefix}]\n{pristine_san_output}\nEnglish Translation:\n{best_sliding_match}\n{'-'*40}\n")
            sanskrit_log.append(f"[{prefix}]\nOLD OCR SAN ──► {flat_ocr_san}\nNEW CLN SAN ──► {flat_cln_san}\n\n")
            english_log.append(f"[{prefix}]\nOLD OCR ENG ──► {payload_text}\nNEW CORR ENG ──► {best_sliding_match}\n\n")
            
            # Update sequence state for the next iteration
            if target_verses:
                last_processed_verse = max(target_verses)
            else:
                last_processed_verse += 1
            
            idx += 2  
        else:
            idx += 1

    out_master = f"{dir_path}/{book_num}.{ch_num}.interleaved_master.txt"
    out_san    = f"{dir_path}/{book_num}.{ch_num}.comparison_sanskrit.txt"
    out_eng    = f"{dir_path}/{book_num}.{ch_num}.comparison_english.txt"

    with open(out_master, 'w', encoding='utf-8') as f: f.write("\n".join(master_interleaved))
    with open(out_san, 'w', encoding='utf-8') as f: f.write("".join(sanskrit_log).strip() + "\n")
    with open(out_eng, 'w', encoding='utf-8') as f: f.write("".join(english_log).strip() + "\n")

    audit_check_begin_mismatch(out_master)
    
    issues = audit_interleaved_file(out_master)

    if issues:
        print(f"\n❌ {out_master} — Found {len(issues)} issue(s):")
        for verse_id, snippet in issues:
            print(f"   └── {verse_id}: \"...{snippet}\"")
    else:
        print(f"✅ {out_master} — All blocks cleanly terminated.")   
    
    print(f"🎯 Complete! Written logs to directory: {dir_path}\n")

if __name__ == "__main__":
    print("🏁 Deploying Production Text Interleaving Engine...")
    
    book_num = 6
    chapters_to_run = list(range(1, 31))
    config_source = "Default Fallback Directive"
    
    cfg_path = "book.cfg"
    if os.path.exists(cfg_path):
        with open(cfg_path, 'r', encoding='utf-8') as cfg_file:
            for line in cfg_file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("BOOK="):
                    val = line.split("=", 1)[1].strip()
                    if val.isdigit():
                        book_num = int(val)
                elif line.startswith("CHAPTERS="):
                    val = line.split("=", 1)[1].strip()
                    parsed = parse_chapters_range(val)
                    if parsed:
                        chapters_to_run = parsed
                        config_source = f"book.cfg [BOOK={book_num}, CHAPTERS={val}]"

    book_id = f"B{book_num:02d}"
    print(f"📂 Scanning Route: ./datafiles/{book_id}/C*/ via {config_source}")
    print(f"🔢 Targeted Book: {book_num} | Chapters: {chapters_to_run}")
    print("─" * 80)
    
    for chapter in chapters_to_run:
        process_single_chapter(book_id=book_id, ch_num=chapter, book_num=book_num)
        
    print("─" * 80)
    print("🎯 Process Matrix Sweep Complete!")