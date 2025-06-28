import streamlit as st
from itertools import product
import csv
import os
import re

# ─── Read filter intent descriptions from CSV ───
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
                combos.add(''.join(sorted(d + ''.join(p))))
    else:
        pairs = set(''.join(sorted((seed_str[i], seed_str[j])))
                    for i in range(len(seed_str)) for j in range(i+1, len(seed_str)))
        for pair in pairs:
            for p in product(all_digits, repeat=3):
                combos.add(''.join(sorted(pair + ''.join(p))))
    return sorted(combos)

# ─── Single-filter helper ───
def apply_filter(desc, combo_digits, seed_digits):
    d = desc.lower().replace('-', ' ').replace(',', ' ')
    sum_combo = sum(combo_digits)
    sum_seed = sum(seed_digits)
    # digit-sum trap
    m = re.search(r"digit sum of the (?:combination|combo) equals (\d+)", d)
    if m and sum_combo == int(m.group(1)):
        return True
    # parity traps
    if ('seed contains' in d or 'seed includes digits' in d) and 'sum' in d:
        nums = list(map(int, re.findall(r"\d+", d)))
        if 'even sum' in d and set(nums).issubset(seed_digits) and sum_combo % 2 == 0:
            return True
        if 'odd sum' in d and set(nums).issubset(seed_digits) and sum_combo % 2 == 1:
            return True
    # end-digit traps
    m = re.search(r"seed sum end digit is (\d+) and combo sum end digit is (\d+)", d)
    if m and sum_seed % 10 == int(m.group(1)) and sum_combo % 10 == int(m.group(2)):
        return True
    # shared digits
    m = re.search(r"combo has ≥?(\d+) shared digits with seed and combo digit sum < (\d+)", d)
    if m:
        cnt, thr = int(m.group(1)), int(m.group(2))
        if len(set(combo_digits) & set(seed_digits)) >= cnt and sum_combo < thr:
            return True
    # mirror sum
    if 'mirror of the seed sum' in d and sum_combo == int(str(sum_seed)[::-1]):
        return True
    # root sum
    if 'same root sum as seed' in d:
        def root(n):
            while n >= 10:
                n = sum(map(int, str(n)))
            return n
        if root(sum_combo) == root(sum_seed):
            return True
    # mirror pair
    if 'digit and its mirror' in d:
        mirrors = {'0':'5','1':'6','2':'7','3':'8','4':'9'}
        for a,b in mirrors.items():
            if int(a) in combo_digits and int(b) in combo_digits:
                return True
    # unique >25 trap
    if '5 unique digits' in d and '>25' in d and '3 digits must match' in d:
        if len(set(combo_digits)) == 5 and sum_combo > 25 and len(set(combo_digits) & set(seed_digits)) < 3:
            return True
    # high/low
    if 'all 5 digits in combo are >/=5' in d and all(c>=5 for c in combo_digits):
        return True
    if 'all five digits in combo are <=4' in d and all(c<=4 for c in combo_digits):
        return True
    # odd/even
    if 'all 5 digits in combo are odd' in d and all(c%2==1 for c in combo_digits):
        return True
    if 'all 5 digits in combo are even' in d and all(c%2==0 for c in combo_digits):
        return True
    return False

# ─── Streamlit UI ───
st.sidebar.header("🔢 DC-5 Filter Tracker Full")

def input_seed(label):
    v = st.sidebar.text_input(label).strip()
    if not v:
        st.sidebar.error(f"Please enter {label.lower()}")
        st.stop()
    if len(v) != 5 or not v.isdigit():
        st.sidebar.error("Seed must be exactly 5 digits (0–9)")
        st.stop()
    return v

current_seed = input_seed("Current 5-digit seed (required):")
prev_seed    = input_seed("Previous 5-digit seed (required):")
method       = st.sidebar.selectbox("Generation Method:", ["1-digit","2-digit pair"])

# generate combos
combos = generate_combinations(prev_seed, method)
if not combos:
    st.sidebar.error("No combos generated. Check previous seed.")
    st.stop()
seed_digits = [int(d) for d in current_seed]

# ─── Compute elimination help counts ───
elim_counts = {desc: sum(apply_filter(desc, [int(c) for c in combo], seed_digits) for combo in combos) for desc in filters_list}

# ─── Filter selection & elimination ┎──
st.header("🔧 Active Filters & Combo Stats")
select_all = st.checkbox("Select/Deselect All Filters", value=False)
selected = []
for i, desc in enumerate(filters_list):
    label = f"{desc} — eliminated {elim_counts[desc]}"
    if st.checkbox(label, value=select_all, key=f"filter_{i}"):
        selected.append(desc)

# apply filters immediately
new_surv, new_elim = [], {}
for combo in combos:
    cd = [int(c) for c in combo]
    for desc in selected:
        if apply_filter(desc, cd, seed_digits):
            new_elim[combo] = desc
            break
    else:
        new_surv.append(combo)
survivors, eliminated_details = new_surv, new_elim
eliminated_counts = len(eliminated_details)
remaining_counts = len(survivors)

# ─── Display stats in a fixed area ───
col1, col2, col3 = st.columns(3)
col1.metric("Total Combos", len(combos))
col2.metric("Eliminated", eliminated_counts)
col3.metric("Remaining", remaining_counts)

# ─── Sidebar Lookup ┎──
st.sidebar.markdown('---')
query = st.sidebar.text_input("Check a combo (any order):")
if query:
    key = ''.join(sorted(query.strip()))
    if key in eliminated_details:
        st.sidebar.warning(f"Eliminated by: {eliminated_details[key]}")
    elif key in survivors:
        st.sidebar.success("It still survives!")
    else:
        st.sidebar.info("Not generated.")

# ─── Show survivors ┎──
with st.expander("Show remaining combinations"):
    for c in survivors:
        st.write(c)
