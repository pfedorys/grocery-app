import streamlit as st
import pandas as pd
import urllib.parse
import json

st.set_page_config(page_title="Smart Grocery Planner", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('cleaned_food_list.csv')
    df.columns = df.columns.str.strip()
    store_cols = ['King Kullen', 'Aldi', 'Stop & Shop', 'Whole Foods', 'Target', 'Costco']
    for col in store_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
    if 'Best Price' in df.columns:
        df['Best Price'] = pd.to_numeric(df['Best Price'].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
    df = df.dropna(subset=['Item'])
    return df, store_cols

df, STORES = load_data()

# --- NEW: SESSION STATE FOR SAVED LISTS ---
if "saved_lists" not in st.session_state:
    st.session_state.saved_lists = {} # Dictionary: {name: [indices]}

# Handle URL Parameters (Auto-loading a shared list)
params = st.query_params
if "items" in params and not st.session_state.get('loaded_from_url'):
    try:
        item_indices = [int(i) for i in params["items"].split(",")]
        for idx in item_indices:
            st.session_state[f"check_{idx}"] = True
        st.session_state.loaded_from_url = True
    except:
        pass

def reset_list():
    for key in list(st.session_state.keys()):
        if key.startswith("check_"):
            st.session_state[key] = False

st.title("🛒 Smart Grocery List Builder")

col_search, col_reset = st.columns([3, 1])
with col_search:
    search_query = st.text_input("🔍 Search for items", "")
with col_reset:
    st.write(" ")
    if st.button("🔄 Clear Selections"):
        reset_list()
        st.query_params.clear()
        st.rerun()

# 1. Selection Interface
st.sidebar.header("Filter")
categories = df['Category'].unique()
category_filter = st.sidebar.multiselect("Select Categories", categories, default=categories)

filtered_df = df[
    (df['Category'].isin(category_filter)) & 
    (df['Item'].str.contains(search_query, case=False, na=False))
]

st.subheader("Select Items to Buy")
selected_items = []
with st.expander("Show Checklist", expanded=True):
    for index, row in filtered_df.iterrows():
        item_label = f"{row['Item']} (${row['Best Price']:.2f} at {row['Best Store']})"
        # Use session state to allow URL loading
        is_checked = st.checkbox(item_label, key=f"check_{index}")
        if is_checked:
            selected_items.append(row)

# 2. Optimized List & Comparisons
if selected_items:
    st.divider()
    shopping_df = pd.DataFrame(selected_items)
    best_grand_total = shopping_df['Best Price'].sum()
    
    st.header("📋 Optimized Shopping List")
    for store in shopping_df['Best Store'].unique():
        items_at_store = shopping_df[shopping_df['Best Store'] == store]
        with st.expander(f"📍 {store} - Subtotal: ${items_at_store['Best Price'].sum():.2f}", expanded=True):
            for _, item in items_at_store.iterrows():
                st.write(f"✅ **{item['Item']}**: ${item['Best Price']:.2f}")

    # 3. Save & Share Features
    st.divider()
    st.header("💾 Manage & Share List")
    
    list_name = st.text_input("List Name", "My Weekly List")
    
    # Generate Link for this specific list
    current_indices = ",".join([str(i) for i, row in filtered_df.iterrows() if st.session_state.get(f"check_{i}")])
    shareable_url = f"https://grocery-app-kqya53bcfcmexnes2bv3le.streamlit.app/?items={current_indices}"
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 Save to Dashboard"):
            indices = [int(k.split("_")[1]) for k, v in st.session_state.items() if k.startswith("check_") and v]
            st.session_state.saved_lists[list_name] = indices
            st.success(f"Saved '{list_name}'")
    
    with c2:
        sms_text = f"Grocery List: {shareable_url}"
        st.markdown(f'<a href="sms:?&body={urllib.parse.quote(sms_text)}" target="_blank"><button style="width:100%; border-radius:10px; background-color:#25D366; color:white; border:none; padding:10px; cursor:pointer;">📱 SMS Link</button></a>', unsafe_allow_html=True)
    
    with c3:
        st.markdown(f'<a href="mailto:?subject={list_name}&body={shareable_url}"><button style="width:100%; border-radius:10px; background-color:#0078D4; color:white; border:none; padding:10px; cursor:pointer;">✉️ Email Link</button></a>', unsafe_allow_html=True)

# 4. Saved Lists Dashboard
st.divider()
st.header("🗄️ Saved Lists Dashboard")

if st.session_state.saved_lists:
    for name, indices in list(st.session_state.saved_lists.items()):
        col_name, col_act, col_copy, col_ren, col_del = st.columns([3, 1, 1, 1, 1])
        
        col_name.write(f"**{name}** ({len(indices)} items)")
        
        if col_act.button("🔄 Activate", key=f"act_{name}"):
            reset_list()
            for idx in indices:
                st.session_state[f"check_{idx}"] = True
            st.rerun()
            
        if col_copy.button("👯 Copy", key=f"cp_{name}"):
            st.session_state.saved_lists[f"{name} (Copy)"] = indices
            st.rerun()
            
        if col_del.button("🗑️ Delete", key=f"del_{name}"):
            del st.session_state.saved_lists[name]
            st.rerun()
            
        new_name = col_ren.text_input("Rename", value=name, key=f"ren_in_{name}", label_visibility="collapsed")
        if new_name != name:
            st.session_state.saved_lists[new_name] = st.session_state.saved_lists.pop(name)
            st.rerun()
else:
    st.info("No saved lists yet. Select items and click 'Save to Dashboard'.")
