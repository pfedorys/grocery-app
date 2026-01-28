import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Smart Grocery Planner", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('cleaned_food_list.csv')
    df.columns = df.columns.str.strip()
    # List of all store columns from your Excel
    store_cols = ['King Kullen', 'Aldi', 'Stop & Shop', 'Whole Foods', 'Target', 'Costco']
    for col in store_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
    
    if 'Best Price' in df.columns:
        df['Best Price'] = pd.to_numeric(df['Best Price'].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
    
    df = df.dropna(subset=['Item'])
    return df, store_cols

df, STORES = load_data()

def reset_list():
    for key in st.session_state.keys():
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
        if st.checkbox(item_label, key=f"check_{index}"):
            selected_items.append(row)

# 2. Comparison & Totals
if selected_items:
    st.divider()
    shopping_df = pd.DataFrame(selected_items)
    
    st.header("📋 Optimized Shopping List")
    
    grand_total = 0
    share_text = "Shopping List Comparison:\n"
    
    # Store-by-Store Breakdown
    stores_to_visit = shopping_df['Best Store'].unique()
    for store in stores_to_visit:
        items_at_store = shopping_df[shopping_df['Best Store'] == store]
        subtotal = items_at_store['Best Price'].sum()
        grand_total += subtotal
        
        with st.expander(f"📍 {store} - Subtotal: ${subtotal:.2f}", expanded=True):
            for _, item in items_at_store.iterrows():
                # Find alternatives
                alts = []
                for s in STORES:
                    if s != store and not pd.isna(item[s]):
                        diff = item[s] - item['Best Price']
                        alts.append(f"{s} (+${diff:.2f})")
                
                alt_text = f" | Alts: {', '.join(alts)}" if alts else " | No other store listed"
                st.write(f"✅ **{item['Item']}**: ${item['Best Price']:.2f}{alt_text}")
                share_text += f"- {item['Item']} at {store}: ${item['Best Price']:.2f}{alt_text}\n"

    st.divider()
    st.metric("Total Trip Cost (Best Prices)", f"${grand_total:.2f}")

    # --- SAVE & SHARE ---
    st.header("💾 Save & Share")
    list_name = st.text_input("List Name", "My Grocery List")
    sms_body = urllib.parse.quote(share_text)
    email_body = urllib.parse.quote(share_text)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<a href="sms:?&body={sms_body}" target="_blank"><button style="width:100%; border-radius:10px; background-color:#25D366; color:white; border:none; padding:10px; cursor:pointer;">📱 Text List</button></a>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<a href="mailto:?subject={list_name}&body={email_body}"><button style="width:100%; border-radius:10px; background-color:#0078D4; color:white; border:none; padding:10px; cursor:pointer;">✉️ Email List</button></a>', unsafe_allow_html=True)
else:
    st.info("Select items above to build your list.")
