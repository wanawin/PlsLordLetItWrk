import streamlit as st
from itertools import product
import csv
import os
import re
from collections import Counter

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
def apply_filter(desc, combo_digits, seed_digits,
                 prev_seed_digits, prev_prev_draw_digits,
                 seed_counts, new_seed_digits):
    d = desc.lower()
    sum_combo = sum(combo_digits)

        # custom filters are loaded dynamically from CSV
    # existing logic continues...
    return False

# ─── Streamlit UI ───
st.sidebar.header("🔢 DC-5 Filter Tracker Full")

def input_seed(label, required=True):
    v = st.sidebar.text_input(label).strip()
    if required and not v:
        st.sidebar.error(f"Please enter {label.lower()}")
        st.stop()
    if v and (len(v) != 5 or not v.isdigit()):
        st.sidebar.error("Seed must be exactly 5 digits (0–9)")
        st.stop()
    return v

# Inputs
today_seed = input_seed("Current 5-digit seed (required):")
prev_seed = input_seed("Previous 5-digit seed (optional):", required=False)
prev_prev_draw = input_seed("Draw before previous seed (optional):", required=False)

# Parse to digits
prev_seed_digits = [int(d) for d in prev_seed] if prev_seed else []
prev_prev_draw_digits = [int(d) for d in prev_prev_draw] if prev_prev_draw else []

# Optional contexts
hot_input = st.sidebar.text_input("Hot digits (optional, comma-separated):")
cold_input = st.sidebar.text_input("Cold digits (optional, comma-separated):")
due_input = st.sidebar.text_input("Due digits (optional, comma-separated):")
hot_digits = [int(d) for d in re.findall(r"\d+", hot_input)] if hot_input else []
cold_digits = [int(d) for d in re.findall(r"\d+", cold_input)] if cold_input else []
due_digits = [int(d) for d in re.findall(r"\d+", due_input)] if due_input else []
method = st.sidebar.selectbox("Generation Method:", ["1-digit","2-digit pair"])

# Generate combos and helper vars
combos = generate_combinations(today_seed, method)
if not combos:
    st.sidebar.error("No combos generated. Check current seed.")
    st.stop()
seed_digits = [int(d) for d in today_seed]
seed_counts = Counter(seed_digits)
new_seed_digits = set(seed_digits) - set(prev_seed_digits)

# Elimination
new_surv, new_elim = [], {}
for combo in combos:
    cd = [int(c) for c in combo]
    for i, desc in enumerate(filters_list):
        if st.session_state.get(f"filter_{i}", False):
            if apply_filter(desc, cd, seed_digits,
                            prev_seed_digits, prev_prev_draw_digits,
                            seed_counts, new_seed_digits):
                new_elim[combo] = desc
                break
    else:
        new_surv.append(combo)
survivors, eliminated_details = new_surv, new_elim

# Metrics
eliminated_counts = len(eliminated_details)
remaining_counts = len(survivors)
st.sidebar.markdown(f"**Total combos:** {len(combos)}  
**Eliminated:** {eliminated_counts}  
**Remaining:** {remaining_counts}")

# Combo lookup
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

# Filter UI
st.header("🔧 Active Filters")
select_all = st.checkbox("Select/Deselect All Filters")
for i, desc in enumerate(filters_list):
    label = f"{desc} — eliminated {sum(apply_filter(desc, [int(c) for c in combo], seed_digits, prev_seed_digits, prev_prev_draw_digits, seed_counts, new_seed_digits) for combo in combos)}"
    st.checkbox(label, value=select_all, key=f"filter_{i}")

# Survivors
with st.expander("Show remaining combinations"):
    for c in survivors:
        st.write(c)
