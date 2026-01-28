import streamlit as st
import pandas as pd
import urllib.parse

# Set app URL as a constant for easy sharing
APP_URL = "https://grocery-app-kqya53bcfcmexnes2bv3le.streamlit.app/"

st.set_page_config(page_title="Smart Grocery Planner", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('cleaned_food_list.csv')
    df.columns = df.columns.str.strip()
    store_cols = ['King Kullen', 'Aldi', 'Stop & Shop', 'Whole Foods', 'Target', 'Costco']
    
    # Standardize all price columns
    all_price_cols = store_cols + ['Best Price', 'Previous Price']
    for col in all_price_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
    
    df = df.dropna(subset=['Item'])
    return df, store_cols

df, STORES = load_data()

# --- PERSISTENT SELECTION MEMORY ---
if "persistent_selections" not in st.session_state:
    st.session_state.persistent_selections = set() 
if "saved_lists" not in st.session_state:
    st.session_state.saved_lists = {}

def reset_list():
    st.session_state.persistent_selections = set()
    for key in list(st.session_state.keys()):
        if key.startswith("check_"):
            st.session_state[key] = False

def toggle_selection(idx):
    if st.session_state[f"check_{idx}"]:
        st.session_state.persistent_selections.add(idx)
    else:
        st.session_state.persistent_selections.discard(idx)

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
with st.expander("Show Checklist", expanded=True):
    for index, row in filtered_df.iterrows():
        # Price History Indicator
        history_note = ""
        if 'Previous Price' in row and not pd.isna(row['Previous Price']):
            diff = row['Best Price'] - row['Previous Price']
            if diff < 0:
                history_note = f" 📉 (Saved ${abs(diff):.2f})"
            elif diff > 0:
                history_note = f" 📈 (Up ${diff:.2f})"
        
        item_label = f"{row['Item']} (${row['Best Price']:.2f} at {row['Best Store']}){history_note}"
        is_already_selected = index in st.session_state.persistent_selections
        st.checkbox(item_label, value=is_already_selected, key=f"check_{index}", on_change=toggle_selection, args=(index,))

# 2. Optimized List & Budget Breakdown
selected_indices = list(st.session_state.persistent_selections)
if selected_indices:
    selected_items_df = df.loc[selected_indices]
    
    st.divider()
    col_list, col_chart = st.columns([2, 1])
    
    with col_list:
        st.header("📋 Optimized Shopping List")
        best_grand_total = selected_items_df['Best Price'].sum()
        for store in selected_items_df['Best Store'].unique():
            items_at_store = selected_items_df[selected_items_df['Best Store'] == store]
            with st.expander(f"📍 {store} - Subtotal: ${items_at_store['Best Price'].sum():.2f}", expanded=True):
                for _, item in items_at_store.iterrows():
                    st.write(f"✅ **{item['Item']}**: ${item['Best Price']:.2f}")
        st.metric("Total Trip Cost", f"${best_grand_total:.2f}")

    with col_chart:
        st.header("📊 Budget by Category")
        cat_data = selected_items_df.groupby('Category')['Best Price'].sum().reset_index()
        st.bar_chart(data=cat_data, x='Category', y='Best Price')
        st.dataframe(cat_data.set_index('Category').style.format("${:.2f}"), use_container_width=True)

    # 3. Share Features (Now using your specific APP_URL)
    st.divider()
    list_name = st.text_input("List Name", "My Weekly List")
    current_ids = ",".join(map(str, selected_indices))
    share_url = f"{APP_URL}?items={current_ids}"
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'''
            <a href="sms:?&body={urllib.parse.quote(share_url)}" target="_blank">
                <button style="width:100%; border-radius:10px; background-color:#25D366; color:white; border:none; padding:10px; cursor:pointer;">
                    📱 SMS Link
                </button>
            </a>
            ''', unsafe_allow_html=True)
    with c2:
        st.markdown(f'''
            <a href="mailto:?subject={urllib.parse.quote(list_name)}&body={share_url}">
                <button style="width:100%; border-radius:10px; background-color:#0078D4; color:white; border:none; padding:10px; cursor:pointer;">
                    ✉️ Email Link
                </button>
            </a>
            ''', unsafe_allow_html=True)

# 4. Dashboard
st.divider()
st.header("🗄️ Saved Lists Dashboard")
if st.button("💾 Save Current Selections to Dashboard"):
    st.session_state.saved_lists[list_name] = list(st.session_state.persistent_selections)

for name, indices in list(st.session_state.saved_lists.items()):
    c_name, c_act, c_del = st.columns([4, 1, 1])
    c_name.write(f"**{name}** ({len(indices)} items)")
    if c_act.button("🔄 Activate", key=f"load_{name}"):
        st.session_state.persistent_selections = set(indices)
        st.rerun()
    if c_del.button("🗑️", key=f"del_{name}"):
        del st.session_state.saved_lists[name]
        st.rerun()
