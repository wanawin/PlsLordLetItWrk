import streamlit as st
from itertools import product

# ─── Begin Filter Intent TXT Parsing ───
import csv
import os

# Read filter intent descriptions from plain text file
txt_path = 'filter_intent_summary_corrected_only.csv'
filters_list = []
if os.path.exists(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            desc = line.strip().strip('"')
            if desc:
                filters_list.append(desc)
else:
    st.sidebar.error(f"Filter intent file not found: {txt_path}")
# At this point, filters_list contains each description as a string
# ─── End TXT Parsing ───

# ─── Begin inlined dc5_final_all_filters_embedded.py ───
# Entire original module inlined below

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
# ─── Begin dynamic filter logic using filters_list ───
import re

def should_eliminate(combo_digits, seed_digits):
    """Apply filters dynamically based on plain-English descriptions in filters_list."""
    sum_combo = sum(combo_digits)
    sum_seed  = sum(seed_digits)

    for desc in filters_list:
        d = desc.lower().replace('-', ' ').replace(',', ' ')

        # 1. digit sum equals N
        m = re.search(r"digit sum of the (?:combination|combo) equals (\\d+)", d)
        if m and sum_combo == int(m.group(1)):
            return True

        # 2. seed parity traps (even/odd sums)
        if ('seed contains' in d or 'seed includes digits' in d) and 'sum' in d:
            nums = list(map(int, re.findall(r"\\d+", d)))
            if 'even sum' in d and set(nums).issubset(seed_digits) and sum_combo % 2 == 0:
                return True
            if 'odd sum' in d and set(nums).issubset(seed_digits) and sum_combo % 2 == 1:
                return True

        # 3. seed sum end digit traps
        m = re.search(r"seed sum end digit is (\\d+) and combo sum end digit is (\\d+)", d)
        if m and sum_seed % 10 == int(m.group(1)) and sum_combo % 10 == int(m.group(2)):
            return True

        # 4. shared digits traps
        m = re.search(r"combo has ≥?(\\d+) shared digits with seed and combo digit sum < (\\d+)", d)
        if m:
            count, thresh = int(m.group(1)), int(m.group(2))
            if len(set(combo_digits) & set(seed_digits)) >= count and sum_combo < thresh:
                return True

        # 5. mirror sum trap
        if 'mirror of the seed sum' in d:
            mirror = int(str(sum_seed)[::-1])
            if sum_combo == mirror:
                return True

        # 6. same root sum as seed
        if 'same root sum as seed' in d:
            def root(n):
                while n >= 10:
                    n = sum(map(int, str(n)))
                return n
            if root(sum_combo) == root(sum_seed):
                return True

        # 7. digit-mirror pair trap
        if 'digit and its mirror' in d:
            mirrors = {'0':'5','1':'6','2':'7','3':'8','4':'9'}
            for a,b in mirrors.items():
                if int(a) in combo_digits and int(b) in combo_digits:
                    return True

        # 8. unique digits >25 trap
        if '5 unique digits' in d and '>25' in d and '3 digits must match' in d:
            if len(set(combo_digits)) == 5 and sum_combo > 25 and len(set(combo_digits) & set(seed_digits)) < 3:
                return True

        # 9. all high/low digits
        if 'all 5 digits in combo are >/=5' in d and all(c >= 5 for c in combo_digits):
            return True
        if 'all five digits in combo are< /=4' in d and all(c <= 4 for c in combo_digits):
            return True

        # 10. all odd or all even
        if 'all 5 digits in combo are odd' in d and all(c % 2 == 1 for c in combo_digits):
            return True
        if 'all 5 digits in combo are even' in d and all(c % 2 == 0 for c in combo_digits):
            return True

    return False
# ─── End dynamic filter logic ───

# ─── Begin dynamic filter logic using filters_list ───
def should_eliminate(combo_digits, seed_digits):
    """Apply filters dynamically based on plain-English descriptions in filters_list."""
    import re

    sum_combo = sum(combo_digits)
    sum_seed = sum(seed_digits)

    for desc in filters_list:
        d = desc.lower().replace('-', ' ').replace(',', ' ')

        # 1. digit sum equals N
        m = re.search(r"digit sum of the (?:combination|combo) equals (\\d+)", d)
        if m:
            if sum_combo == int(m.group(1)):
                return True
            continue

        # 2. seed parity traps (even/odd sums)
        if ('seed contains' in d or 'seed includes digits' in d) and 'sum' in d:
            nums = list(map(int, re.findall(r"\\d+", d)))
            if 'even sum' in d:
                if set(nums).issubset(seed_digits) and sum_combo % 2 == 0:
                    return True
                continue
            if 'odd sum' in d:
                if set(nums).issubset(seed_digits) and sum_combo % 2 == 1:
                    return True
                continue

        # 3. seed sum end digit traps
        m = re.search(r"seed sum end digit is (\\d+) and combo sum end digit is (\\d+)", d)
        if m:
            if sum_seed % 10 == int(m.group(1)) and sum_combo % 10 == int(m.group(2)):
                return True
            continue

        # 4. shared digits traps
        m = re.search(r"combo has ≥?(\\d+) shared digits with seed and combo digit sum < (\\d+)", d)
        if m:
            count, thresh = int(m.group(1)), int(m.group(2))
            if len(set(combo_digits) & set(seed_digits)) >= count and sum_combo < thresh:
                return True
            continue

        # 5. mirror sum trap
        if 'mirror of the seed sum' in d:
            mirror = int(str(sum_seed)[::-1])
            if sum_combo == mirror:
                return True
            continue

        # 6. same root sum as seed
        if 'same root sum as seed' in d:
            def root(n):
                while n >= 10:
                    n = sum(map(int, str(n)))
                return n
            if root(sum_combo) == root(sum_seed):
                return True
            continue

        # 7. digit-mirror pair trap
        if 'digit and its mirror' in d:
            mirrors = {'0':'5','1':'6','2':'7','3':'8','4':'9'}
            for a,b in mirrors.items():
                if int(a) in combo_digits and int(b) in combo_digits:
                    return True
            continue

        # 8. unique digits cold trap
        if '5 unique digits' in d and '>25' in d and '3 digits must match' in d:
            if len(set(combo_digits)) == 5 and sum_combo > 25 and len(set(combo_digits) & set(seed_digits)) < 3:
                return True
            continue

        # 9. all high/low digits
        if 'all 5 digits in combo are >/=5' in d:
            if all(c >= 5 for c in combo_digits):
                return True
            continue
        if 'all five digits in combo are< /=4' in d:
            if all(c <= 4 for c in combo_digits):
                return True
            continue

        # 10. all odd or all even
        if 'all 5 digits in combo are odd' in d:
            if all(c % 2 == 1 for c in combo_digits):
                return True
            continue
        if 'all 5 digits in combo are even' in d:
            if all(c % 2 == 0 for c in combo_digits):
                return True
            continue

    return False
# ─── End dynamic filter logic ───


# ─── Streamlit UI Setup ───
st.sidebar.header("🔢 DC-5 Filter Tracker Full")


def input_seed(label):
    value = st.sidebar.text_input(label).strip()
    if not value:
        st.sidebar.error(f"Please enter {label.lower()}")
        st.stop()
    if len(value) != 5 or not value.isdigit():
        st.sidebar.error("Seed must be exactly 5 digits (0–9)")
        st.stop()
    return value

current_seed = input_seed("Current 5-digit seed (required):")
prev_seed    = input_seed("Previous 5-digit seed (required):")

hot_digits   = [d for d in st.sidebar.text_input("Hot digits (comma-separated):").replace(' ', '').split(',') if d]
cold_digits  = [d for d in st.sidebar.text_input("Cold digits (comma-separated):").replace(' ', '').split(',') if d]
due_digits   = [d for d in st.sidebar.text_input("Due digits (comma-separated):").replace(' ', '').split(',') if d]
method       = st.sidebar.selectbox("Generation Method:", ["1-digit", "2-digit pair"])

# Generate combos
combos = generate_combinations(prev_seed, method)
if not combos:
    st.sidebar.error("No combinations generated. Check previous seed.")
    st.stop()
# ─── Begin dynamic filter logic using filters_list ───
import re

def should_eliminate(combo_digits, seed_digits):
    """Apply filters dynamically based on plain-English descriptions in filters_list."""
    sum_combo = sum(combo_digits)
    sum_seed  = sum(seed_digits)

    for desc in filters_list:
        d = desc.lower().replace('-', ' ').replace(',', ' ')

        # 1. digit sum equals N
        m = re.search(r"digit sum of the (?:combination|combo) equals (\d+)", d)
        if m and sum_combo == int(m.group(1)):
            return True

        # 2. seed parity traps (even/odd sums)
        if ('seed contains' in d or 'seed includes digits' in d) and 'sum' in d:
            nums = list(map(int, re.findall(r"\d+", d)))
            if 'even sum' in d and set(nums).issubset(seed_digits) and sum_combo % 2 == 0:
                return True
            if 'odd sum' in d and set(nums).issubset(seed_digits) and sum_combo % 2 == 1:
                return True

        # 3. seed sum end digit traps
        m = re.search(r"seed sum end digit is (\d+) and combo sum end digit is (\d+)", d)
        if m and sum_seed % 10 == int(m.group(1)) and sum_combo % 10 == int(m.group(2)):
            return True

        # 4. shared digits traps
        m = re.search(r"combo has ≥?(\d+) shared digits with seed and combo digit sum < (\d+)", d)
        if m:
            count, thresh = int(m.group(1)), int(m.group(2))
            if len(set(combo_digits) & set(seed_digits)) >= count and sum_combo < thresh:
                return True

        # 5. mirror sum trap
        if 'mirror of the seed sum' in d:
            mirror = int(str(sum_seed)[::-1])
            if sum_combo == mirror:
                return True

        # 6. same root sum as seed
        if 'same root sum as seed' in d:
            def root(n):
                while n >= 10:
                    n = sum(map(int, str(n)))
                return n
            if root(sum_combo) == root(sum_seed):
                return True

        # 7. digit-mirror pair trap
        if 'digit and its mirror' in d:
            mirrors = {'0':'5','1':'6','2':'7','3':'8','4':'9'}
            for a,b in mirrors.items():
                if int(a) in combo_digits and int(b) in combo_digits:
                    return True

        # 8. unique digits >25 trap
        if '5 unique digits' in d and '>25' in d and '3 digits must match' in d:
            if len(set(combo_digits)) == 5 and sum_combo > 25 and len(set(combo_digits) & set(seed_digits)) < 3:
                return True

        # 9. all high/low digits
        if 'all 5 digits in combo are >/=5' in d and all(c >= 5 for c in combo_digits):
            return True
        if 'all five digits in combo are< /=4' in d and all(c <= 4 for c in combo_digits):
            return True

        # 10. all odd or all even
        if 'all 5 digits in combo are odd' in d and all(c % 2 == 1 for c in combo_digits):
            return True
        if 'all 5 digits in combo are even' in d and all(c % 2 == 0 for c in combo_digits):
            return True

    return False
# ─── End dynamic filter logic ───

# Apply filters
seed_digits = [int(d) for d in current_seed]
eliminated_counts = 0
survivors = []
for combo_str in combos:
    combo_digits = [int(c) for c in combo_str]
    if should_eliminate(combo_digits, seed_digits):
        eliminated_counts += 1
    else:
        survivors.append(combo_str)

# Sidebar summary
st.sidebar.markdown(f"**Total combos generated:** {len(combos)}")
st.sidebar.markdown(f"**Total eliminated:** {eliminated_counts}")
st.sidebar.markdown(f"**Remaining combos:** {len(survivors)}")

# Main content
st.write(f"Remaining combos after all filters: **{len(survivors)}**")
with st.expander("Show remaining combinations"):
    for c in survivors:
        st.write(c)
