import glob
import re
from openpyxl import load_workbook
import csv

# Patterns to detect header/labels describing service combinations
HEADER_PATTERNS = [
    r"tres servicios",
    r"3 servicios",
    r"dos servicios",
    r"un servicio",
    r"ninguno",
    r"combinac",
    r"combinación",
    r"combinaciones",
    r"telefon",
    r"televis",
    r"tv",
    r"internet",
]

header_re = re.compile("|".join(HEADER_PATTERNS), re.IGNORECASE)
number_re = re.compile(r"([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]+)?|[0-9]+(?:[.,][0-9]+)?)\s*%?")

files = sorted(glob.glob(r"datos\\B.1\\*.xlsx"))

out_rows = []

for f in files:
    try:
        wb = load_workbook(f, read_only=True, data_only=True)
    except Exception as e:
        print(f"ERROR opening {f}: {e}")
        continue
    for sheet in wb.sheetnames:
        ws = wb[sheet]
        rows = list(ws.iter_rows(values_only=True))
        for i, row in enumerate(rows):
            # join and lowercase
            try:
                line = " | ".join([str(c).strip() for c in row if c is not None])
            except Exception:
                continue
            if header_re.search(line):
                # capture context rows following this row (up to 15)
                context = []
                for j in range(i, min(i+15, len(rows))):
                    r = rows[j]
                    s = " | ".join([str(c).strip() for c in r if c is not None])
                    if s:
                        # find numeric tokens
                        nums = number_re.findall(s)
                        # normalize numbers: remove thousand separators and change comma to dot
                        parsed = []
                        for n in nums:
                            n_clean = n.replace(',', '').replace(' ', '')
                            n_clean = n_clean.replace('\u00A0', '')
                            parsed.append(n_clean)
                        context.append((j+1, s, parsed))
                # decide whether context contains percentage-like values
                has_pct = any('%' in c[1] or any((float(p.replace(',', '.'))<=100 and '.' in p) or ('%' in c[1]) for p in c[2]) for c in context if c[2])
                # store context for manual inspection
                out_rows.append({
                    'file': f,
                    'sheet': sheet,
                    'header_row': i+1,
                    'header_text': line,
                    'context': context,
                    'has_pct': has_pct,
                })
    wb.close()

# write CSV summary with provenance and a short context snippet
with open('scripts/extracted_service_combinations_summary.csv', 'w', newline='', encoding='utf-8') as csvf:
    writer = csv.writer(csvf)
    writer.writerow(['file','sheet','header_row','header_text','has_pct','context_snippet'])
    for r in out_rows:
        snippet = " -- ".join([f"R{ln}:{txt[:120]}" for ln,txt,nums in r['context'][:6]])
        writer.writerow([r['file'], r['sheet'], r['header_row'], r['header_text'][:200], r['has_pct'], snippet])

print(f"Scanned {len(files)} files, found {len(out_rows)} candidate headers.")
print("Summary written to scripts/extracted_service_combinations_summary.csv")

# also write a detailed JSON-like file for inspection
with open('scripts/extracted_service_combinations_details.txt','w',encoding='utf-8') as detf:
    for r in out_rows:
        detf.write(f"File: {r['file']} | Sheet: {r['sheet']} | Header row: {r['header_row']}\n")
        detf.write(r['header_text'] + "\n")
        for ln, txt, nums in r['context']:
            detf.write(f"  Row {ln}: {txt}\n")
            if nums:
                detf.write(f"    Numbers: {nums}\n")
        detf.write("="*80 + "\n")

print('Done')
