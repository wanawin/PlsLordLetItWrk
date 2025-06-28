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

# ─── Ensure Mirror filter is in the list ───
mirror_desc = "If a combo contains both a digit and its mirror (0/5, 1/6, 2/7, 3/8, 4/9), eliminate combo"
if mirror_desc not in filters_list:
    filters_list.append(mirror_desc)

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
    # normalize and match description
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
    if d.lower().startswith("v-trac"):
        groups = [get_v_trac_group(digit) for digit in combo_digits]
        return len(set(groups)) == 1

    # Mirror filter: eliminate if combo contains both a digit and its mirror
    if "mirror" in d.lower():
        return any(get_mirror(digit) in combo_digits for digit in combo_digits)

    return False

# ─── Streamlit UI ───
st.sidebar.header("🔢 DC-5 Filter Tracker Full")

# ... rest of your Streamlit app code continues unchanged ...
