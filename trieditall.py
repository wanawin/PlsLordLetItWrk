import streamlit as st
from itertools import product
import csv
import os
import re
from collections import Counter

# ─── V-Trac group definitions ───
# Map each digit (0–9) to its V-Trac group (1–5)
V_TRAC_GROUPS = {
    0: 1, 5: 1,
    1: 2, 6: 2,
    2: 3, 7: 3,
    3: 4, 8: 4,
    4: 5, 9: 5,
}

def get_v_trac_group(digit: int) -> int:
    """Return the V-Trac group number (1–5) for a given digit."""
    return V_TRAC_GROUPS.get(digit)

# ─── Mirror digit definitions ───
# Map each digit (0–9) to its mirror digit
MIRROR_PAIRS = {
    0: 5, 5: 0,
    1: 6, 6: 1,
    2: 7, 7: 2,
    3: 8, 8: 3,
    4: 9, 9: 4,
}

def get_mirror(digit: int) -> int:
    """Return the mirror digit for a given digit (0–9)."""
    return MIRROR_PAIRS.get(digit)

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
    # normalize and match description exactly
    d = desc.strip().replace('≥', '>=').replace('≤', '<=')
    sum_combo = sum(combo_digits)
    common_to_both = set(prev_prev_draw_digits).intersection(prev_seed_digits)
    last2 = set(prev_prev_draw_digits) | set(prev_seed_digits)

    # 1. FullHouse on seed (3 of one digit + 2 of another) AND combo sum is even
    if d == "if set(seed_counts.values()) == {2, 3} and sum(combo) % 2 == 0: eliminate(combo)":
        return set(seed_counts.values()) == {2, 3} and sum_combo % 2 == 0

    # 2. Any new seed digit (not in prev_seed) must appear in combo
    if d == "if new_seed_digits and not new_seed_digits.intersection(combo): eliminate(combo)":
        return bool(new_seed_digits) and not new_seed_digits.intersection(combo_digits)

    # 3. ≥2 digits common to both prev_seed AND prev_prev_draw
    if d == "if sum(d in common_to_both for d in combo) >= 2: eliminate(combo)":
        return sum(d in common_to_both for d in combo_digits) >= 2

    # 4. fewer than 2 of last-2-draw digits → eliminate
    if d == "if len(last2.intersection(combo)) < 2: eliminate(combo)":
        return len(last2.intersection(combo_digits)) < 2

    # 5. eliminate if ≥2 of last-2-draw digits
    if d == "if len(last2.intersection(combo)) >= 2: eliminate(combo)":
        return len(last2.intersection(combo_digits)) >= 2

    # 6. eliminate if all combo digits come from last-2 draws
    if d == "if set(combo).issubset(last2): eliminate(combo)":
        return set(combo_digits).issubset(last2)

    # V-Trac example: eliminate if all digits share same group
    if d == "V-TRAC: all digits same group":
        groups = [get_v_trac_group(d) for d in combo_digits]
        return len(set(groups)) == 1

    # Mirror example: eliminate if combo contains a digit and its mirror
    if d == "MIRROR: eliminate if contains mirror pairs":
        return any(get_mirror(d) in combo_digits for d in combo_digits)

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

# Generate combos
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

survivors = new_surv
eliminated_details = new_elim

# Metrics
eliminated_counts = len(eliminated_details)
remaining_counts = len(survivors)
st.sidebar.markdown(
    f"**Total combos:** {len(combos)}  \
**Eliminated:** {eliminated_counts}  \
**Remaining:** {remaining_counts}"
)

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
    count_elim = sum(
        apply_filter(desc,
                     [int(c) for c in combo],
                     seed_digits,
                     prev_seed_digits,
                     prev_prev_draw_digits,
                     seed_counts,
                     new_seed_digits)
        for combo in combos
    )
    label = f"{desc} — eliminated {count_elim}"
    st.checkbox(label, value=select_all, key=f"filter_{i}")

# Survivors listing
with st.expander("Show remaining combinations"):
    for c in survivors:
        st.write(c)
