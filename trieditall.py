import streamlit as st
from itertools import product
import csv
import os
import re

# ─── Read filter intent descriptions from CSV ───
# CSV should live alongside this script in the repo root
txt_path = 'filter_intent_summary_corrected_only.csv'
filters_list = []
if os.path.exists(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            desc = row[0].strip().strip('"')
            if desc:
                filters_list.append(desc)
else:
    st.sidebar.error(f"Filter intent file not found: {txt_path}")

# ─── Combination Generator ───
def generate_combinations(seed, method="2-digit pair"):
    all_digits = '0123456789'
    combos = set()
    seed_str = str(seed)
    if len(seed_str) < 2:
        return []
    if method == "1-digit":
        for d in seed_str:
            for p in product(all_digits, repeat=4):
                combo = ''.join(sorted(d + ''.join(p)))
                combos.add(combo)
    else:
        pairs = set(''.join(sorted((seed_str[i], seed_str[j])))
                    for i in range(len(seed_str)) for j in range(i+1, len(seed_str)))
        for pair in pairs:
            for p in product(all_digits, repeat=3):
                combo = ''.join(sorted(pair + ''.join(p)))
                combos.add(combo)
    return sorted(combos)

# ─── Single-filter helper ───
def apply_filter(desc, combo_digits, seed_digits, sum_combo=None, sum_seed=None):
    d = desc.lower().replace('-', ' ').replace(',', ' ')
    sum_combo = sum_combo if sum_combo is not None else sum(combo_digits)
    sum_seed  = sum_seed  if sum_seed  is not None else sum(seed_digits)
    # 1. digit sum equals N
    m = re.search(r"digit sum of the (?:combination|combo) equals (\d+)", d)
    if m and sum_combo == int(m.group(1)):
        return True
    # 2. seed parity traps
    if ('seed contains' in d or 'seed includes digits' in d) and 'sum' in d:
        nums = list(map(int, re.findall(r"\d+", d)))
        if 'even sum' in d and set(nums).issubset(seed_digits) and sum_combo % 2 == 0:
            return True
        if 'odd sum' in d and set(nums).issubset(seed_digits) and sum_combo % 2 == 1:
            return True
    # 3. end-digit traps
    m = re.search(r"seed sum end digit is (\d+) and combo sum end digit is (\d+)", d)
    if m and sum_seed % 10 == int(m.group(1)) and sum_combo % 10 == int(m.group(2)):
        return True
    # 4. shared-digits traps
    m = re.search(r"combo has ≥?(\d+) shared digits with seed and combo digit sum < (\d+)", d)
    if m:
        cnt, thr = int(m.group(1)), int(m.group(2))
        if len(set(combo_digits) & set(seed_digits)) >= cnt and sum_combo < thr:
            return True
    # 5. mirror-sum trap
    if 'mirror of the seed sum' in d:
        if sum_combo == int(str(sum_seed)[::-1]):
            return True
    # 6. root-sum trap
    if 'same root sum as seed' in d:
        def root(n):
            while n >= 10:
                n = sum(map(int, str(n)))
            return n
        if root(sum_combo) == root(sum_seed):
            return True
    # 7. mirror pair
    if 'digit and its mirror' in d:
        mirrors = {'0':'5','1':'6','2':'7','3':'8','4':'9'}
        for a,b in mirrors.items():
            if int(a) in combo_digits and int(b) in combo_digits:
                return True
    # 8. unique >25 trap
    if '5 unique digits' in d and '>25' in d and '3 digits must match' in d:
        if len(set(combo_digits)) == 5 and sum_combo > 25 and len(set(combo_digits)&set(seed_digits)) < 3:
            return True
    # 9. high/low digits
    if 'all 5 digits in combo are >/=5' in d and all(c >=5 for c in combo_digits): return True
    if 'all five digits in combo are <=4' in d and all(c <=4 for c in combo_digits): return True
    # 10. odd/even digits
    if 'all 5 digits in combo are odd' in d and all(c%2==1 for c in combo_digits): return True
    if 'all 5 digits in combo are even' in d and all(c%2==0 for c in combo_digits): return True
    return False

# ─── Streamlit UI Setup ───
st.sidebar.header("🔢 DC-5 Filter Tracker Full")

def input_seed(label):
    val = st.sidebar.text_input(label)
    val = val.strip()
    if not val:
        st.sidebar.error(f"Please enter {label.lower()}")
        st.stop()
    if len(val) != 5 or not val.isdigit():
        st.sidebar.error("Seed must be exactly 5 digits (0–9)")
        st.stop()
    return val

current_seed = input_seed("Current 5-digit seed (required):")
prev_seed    = input_seed("Previous 5-digit seed (required):")

hot_digits  = [int(d) for d in st.sidebar.text_input("Hot digits (comma-separated):").replace(' ','').split(',') if d]
cold_digits = [int(d) for d in st.sidebar.text_input("Cold digits (comma-separated):").replace(' ','').split(',') if d]
due_digits  = [int(d) for d in st.sidebar.text_input("Due digits (comma-separated):").replace(' ','').split(',') if d]
method       = st.sidebar.selectbox("Generation Method:", ["1-digit","2-digit pair"])

# ─── Compute combos and initial elimination ───
combos = generate_combinations(prev_seed, method)
if not combos:
    st.sidebar.error("No combos generated. Check previous seed.")
    st.stop()

seed_digits = [int(d) for d in current_seed]
eliminated_details = {}
survivors = []
for combo in combos:
    combo_digits = [int(c) for c in combo]
    for desc in filters_list:
        if apply_filter(desc, combo_digits, seed_digits):
            eliminated_details[combo] = desc
            break
    else:
        survivors.append(combo)
eliminated_counts = len(eliminated_details)

# ─── Interactive Filter UI & Combo Lookup ───
# Sidebar initial counts (with no filters applied)
st.sidebar.markdown(
    f"**Total combos:** {len(combos)}  
"
    f"**Eliminated:** 0  
"
    f"**Remaining:** {len(combos)}"
)

# Combo lookup widget
st.sidebar.markdown("---")
query = st.sidebar.text_input("Check a combo (any order):")
if query:
    key = "".join(sorted(query.strip()))
    if key in eliminated_details:
        st.sidebar.warning(f"Eliminated by: {eliminated_details[key]}")
    elif key in survivors:
        st.sidebar.success("It still survives!")
    else:
        st.sidebar.info("Not generated.")

# Expander showing remaining survivors
with st.expander("Show remaining combinations"):
    for c in survivors:
        st.write(c)
