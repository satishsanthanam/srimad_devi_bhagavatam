# ==============================================================================
# APPLE SILICON CUDA, AUTOCAST, & BFLOAT16 DOWNCAST PATCH FOR BAIDU UNLIMITED-OCR
# (Must be at the absolute top of the script before loading the model)
# ==============================================================================
import sys
import torch

if torch.backends.mps.is_available():
    # 1. Trick all basic CUDA capability statements
    torch.cuda.is_available = lambda: True
    torch.cuda.device_count = lambda: 1
    torch.cuda.is_bf16_supported = lambda: False
    torch.cuda.get_device_properties = lambda dev: type('DeviceProps', (object,), {'total_memory': 24 * 1024**3})()
    
    # 2. Redirect global cache clearing
    torch.cuda.empty_cache = lambda: torch.mps.empty_cache()
    
    # 3. Intercept every single tensor instantiation pointing to "cuda"
    original_cuda_method = torch.Tensor.cuda
    def custom_cuda(self, *args, **kwargs):
        return self.to(device="mps", non_blocking=kwargs.get("non_blocking", False))
    torch.Tensor.cuda = custom_cuda

    # 4. Completely disable Autocast by mocking it as a No-Op context manager
    class DummyAutocast:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): return False

    torch.autocast = DummyAutocast
    if hasattr(torch, "amp"):
        torch.amp.autocast = DummyAutocast
    
    if not hasattr(torch, "cuda"):
        sys.modules['torch.cuda.amp'] = type('AMPContext', (object,), {'autocast': DummyAutocast})
    else:
        import torch.cuda.amp
        torch.cuda.amp.autocast = DummyAutocast

    # 5. CRITICAL FIX: Intercept torch.to calls to re-route "cuda" -> "mps" AND "bfloat16" -> "float16"
    original_to = torch.Tensor.to
    def custom_to(self, *args, **kwargs):
        # Convert device target
        if args and isinstance(args[0], str) and "cuda" in args[0]:
            args = ("mps",) + args[1:]
        if "device" in kwargs and isinstance(kwargs["device"], str) and "cuda" in kwargs["device"]:
            kwargs["device"] = "mps"
            
        # Convert dtype target (Catch bfloat16 explicitly requested via positional or keyword arg)
        if args and args[0] == torch.bfloat16:
            args = (torch.float16,) + args[1:]
        if "dtype" in kwargs and kwargs["dtype"] == torch.bfloat16:
            kwargs["dtype"] = torch.float16
            
        res = original_to(self, *args, **kwargs)
        
        # If the resulting tensor somehow sneaked through as bfloat16, force-downcast it here
        if res.dtype == torch.bfloat16:
            res = original_to(res, torch.float16)
        return res
    torch.Tensor.to = custom_to

    # 6. Intercept factory functions creating brand new tensors in bfloat16 natively
    original_tensor_creation = torch.tensor
    def custom_tensor(*args, **kwargs):
        if "dtype" in kwargs and kwargs["dtype"] == torch.bfloat16:
            kwargs["dtype"] = torch.float16
        res = original_tensor_creation(*args, **kwargs)
        if res.dtype == torch.bfloat16:
            res = res.to(torch.float16)
        return res
    torch.tensor = custom_tensor

    # 7. Intercept masked_scatter_ and masked_scatter to fix dtype & shape mismatch on MPS
    def patch_masked_scatter(original_func, is_inplace=False):
        def custom_scatter(self, mask, source):
            if source.dtype != self.dtype:
                source = source.to(self.dtype)
            if mask.shape != self.shape:
                mask = mask.expand_as(self).contiguous()
            mask = mask.to(self.device)
            source = source.to(self.device)
            return original_func(self, mask, source)
        return custom_scatter

    torch.Tensor.masked_scatter_ = patch_masked_scatter(torch.Tensor.masked_scatter_, is_inplace=True)
    torch.Tensor.masked_scatter = patch_masked_scatter(torch.Tensor.masked_scatter, is_inplace=False)

    print("[PATCH] Apple Silicon Emulation + Type Alignment (BFloat16 -> Float16) active.")
# ==============================================================================

import os
import re
import gc
import fitz  # PyMuPDF
from PIL import Image
from transformers import AutoModel, AutoTokenizer

# --- CONFIGURATION ---
PROJECT_ROOT = "/Users/satish/projects/bitbucket/scripturesv2/sridevibhagavatam"

# Absolute paths mapped to your repository structure
INPUT_PDF = f"{PROJECT_ROOT}/datafiles/B07/B07.pdf"
OUTPUT_DIR = f"{PROJECT_ROOT}/datafiles/B07/C00/"
FINAL_CHAPTER_FILE = os.path.join(OUTPUT_DIR, "B07_ocred.txt")
START_PAGE = 0  # 0-indexed (Page 1)

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- DUAL STREAM FOR CAPTURING STDOUT ---
class DualStream:
    def __init__(self, file_path):
        self.terminal = sys.stdout
        self.log = open(file_path, "a", encoding="utf-8")
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    def flush(self):
        self.terminal.flush()
        self.log.flush()
    def close(self):
        self.log.close()

# --- INITIALIZE MODEL ON MPS ---
model_id = "baidu/Unlimited-OCR"
print("Loading model and tokenizer onto Apple Silicon...")

if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("[INFO] Metal Performance Shaders (MPS) active.")
else:
    device = torch.device("cpu")
    print("[WARNING] MPS not found. Falling back to CPU.")

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

model = AutoModel.from_pretrained(
    model_id, 
    trust_remote_code=True, 
    dtype=torch.float16 
).to(device) 

model.eval()
print(f"Model successfully anchored to: {device}")

# --- PROCESSING LOOP ---
doc = fitz.open(INPUT_PDF)
total_pages = len(doc)
current_page = START_PAGE

print(f"Starting OCR pipeline. Total pages to process: {total_pages}")

while current_page < total_pages:
    print(f"\n--- Processing Page {current_page + 1} / {total_pages} ---")
    
    txt_output_path = os.path.join(OUTPUT_DIR, f"page_{current_page + 1}.txt")
    if os.path.exists(txt_output_path):
        os.remove(txt_output_path)
        
    stream = DualStream(txt_output_path)
    sys.stdout = stream
    
    page = doc.load_page(current_page)
    pix = page.get_pixmap(dpi=150)
    temp_img_path = os.path.join(OUTPUT_DIR, f"temp_page_{current_page}.png")
    pix.save(temp_img_path)
    
    try:
        model.infer(
            tokenizer=tokenizer,
            prompt='<image>document parsing.',
            image_file=temp_img_path,
            output_path=OUTPUT_DIR,
            base_size=1024, 
            image_size=1024,
            crop_mode=False,
            max_length=4096,
            no_repeat_ngram_size=35, 
            ngram_window=128
        )
        
        sys.stdout = stream.terminal
        stream.close()
        
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)
            
        current_page += 1
        
    except Exception as e:
        sys.stdout = stream.terminal
        stream.close()
        print(f"\n[ERROR] Inference failed on Page {current_page + 1}: {e}")
        
        if os.path.exists(txt_output_path):
            os.remove(txt_output_path)
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)
            
        print("Flushing memory and retrying this page...")
        
    finally:
        gc.collect()
        torch.mps.empty_cache()

print("\n🎉 OCR Pipeline completed successfully!")

# ==============================================================================
# INTEGRATED STAGE: PARSE, CLEAN, AND AGGREGATE INDIVIDUAL PAGES
# ==============================================================================
print("\n--- Starting Post-Processing Phase ---")

# Find all page_*.txt files in the output directory and sort them numerically
page_files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith("page_") and f.endswith(".txt")]
page_files.sort(key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])

if not page_files:
    print(f"Error: No page_*.txt files found in target directory: {OUTPUT_DIR}")
else:
    full_text_lines = []

    for filename in page_files:
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                raw_line = line.strip()
                if not raw_line:
                    continue
                
                # 1. Strip structural detection coordinate blocks (<|det|>...<|/det|>)
                cleaned = re.sub(r'<\|det\|>.*?<\|/det\|>', '', raw_line).strip()
                
                # 2. Skip running page layouts and decoration anchors
                if not cleaned or cleaned in ["-*", "Śrimaddevibhāgavatam"]:
                    continue
                if re.match(r'^\d+$', cleaned) or "Book II Chapter" in cleaned:
                    continue
                
                full_text_lines.append(cleaned)

    # Export out the sanitized aggregate master document
    with open(FINAL_CHAPTER_FILE, 'w', encoding='utf-8') as out_f:
        out_f.write("\n\n".join(full_text_lines))
        
    print(f"🎉 Chapter aggregated successfully in sequential order!")
    print(f"📁 Master file saved to: {FINAL_CHAPTER_FILE}")