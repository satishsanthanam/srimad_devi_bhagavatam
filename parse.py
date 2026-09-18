import os
import re

def clean_and_merge_chapter(directory=".", output_filename="chapter_1_clean.txt"):
    # Find all page_*.txt files and sort them numerically (page_1, page_2, etc.)
    page_files = [f for f in os.listdir(directory) if f.startswith("page_") and f.endswith(".txt")]
    page_files.sort(key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    
    if not page_files:
        print("Error: No page_*.txt files found in the current directory.")
        return

    full_text_lines = []

    for filename in page_files:
        filepath = os.path.join(directory, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                raw_line = line.strip()
                if not raw_line:
                    continue
                
                # 1. Remove the <|det|>... Box tag prefix completely
                cleaned = re.sub(r'<\|det\|>.*?<\|/det\|>', '', raw_line).strip()
                
                # 2. Skip structural headers, decorative page dividers, or standalone page numbers
                if not cleaned or cleaned in ["-*", "Śrimaddevibhāgavatam"]:
                    continue
                if re.match(r'^\d+$', cleaned) or "Book II Chapter" in cleaned:
                    continue
                
                full_text_lines.append(cleaned)

    # Write out the concatenated, completely stripped text document
    with open(output_filename, 'w', encoding='utf-8') as out_f:
        out_f.write("\n\n".join(full_text_lines))
        
    print(f"🎉 Chapter aggregated successfully in sequential order!")
    print(f"📁 Output file saved to: {output_filename}")

if __name__ == "__main__":
    clean_and_merge_chapter()
