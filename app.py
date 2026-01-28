import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Smart Grocery Planner", layout="wide")

# Load and clean data
@st.cache_data
def load_data():
    df = pd.read_csv('cleaned_food_list.csv')
    df.columns = df.columns.str.strip()
    if 'Best Price' in df.columns:
        df['Best Price'] = pd.to_numeric(df['Best Price'].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
    df = df.dropna(subset=['Item'])
    return df

df = load_data()

# Session state for checkboxes
if "reset" not in st.session_state:
    st.session_state.reset = False

def reset_list():
    for key in st.session_state.keys():
        if key.startswith("check_"):
            st.session_state[key] = False

st.title("🛒 Smart Grocery List Builder")

# Top controls: Search and Reset
col_search, col_reset = st.columns([3, 1])
with col_search:
    search_query = st.text_input("🔍 Search for items (e.g. 'Berries' or 'Brisket')", "")
with col_reset:
    st.write(" ") # Padding
    if st.button("🔄 Clear Selections"):
        reset_list()
        st.rerun()

# 1. Selection Interface
categories = df['Category'].unique()
selected_items = []

st.sidebar.header("Filter")
category_filter = st.sidebar.multiselect("Select Categories", categories, default=categories)

# Apply Filters: Category + Search Query
filtered_df = df[
    (df['Category'].isin(category_filter)) & 
    (df['Item'].str.contains(search_query, case=False, na=False))
]

st.subheader("Select Items to Buy")
with st.expander("Show Checklist", expanded=True):
    if filtered_df.empty:
        st.warning("No items found matching your search or filters.")
    else:
        for index, row in filtered_df.iterrows():
            item_label = f"{row['Item']} (${row['Best Price']:.2f} at {row['Best Store']})"
            if st.checkbox(item_label, key=f"check_{index}"):
                selected_items.append(row)

# 2. Build the List
if selected_items:
    st.divider()
    shopping_df = pd.DataFrame(selected_items)
    stores = shopping_df['Best Store'].unique()
    
    share_text = "My Shopping List:\n"
    grand_total = 0
    
    for store in stores:
        store_items = shopping_df[shopping_df['Best Store'] == store]
        store_total = store_items['Best Price'].sum()
        grand_total += store_total
        
        share_text += f"\n📍 {store} (Total: ${store_total:.2f}):\n"
        
        with st.expander(f"📍 {store} - Subtotal: ${store_total:.2f}", expanded=True):
            for _, item in store_items.iterrows():
                st.write(f"- **{item['Item']}**: ${item['Best Price']:.2f}")
                share_text += f"- {item['Item']}: ${item['Best Price']:.2f}\n"
    
    share_text += f"\nGrand Total: ${grand_total:.2f}"
    
    st.divider()
    st.metric("Total Trip Cost", f"${grand_total:.2f}")

    # --- SAVE & SHARE SECTION ---
    st.header("💾 Save & Share")
    list_name = st.text_input("List Name", "My Grocery List")
    
    col_sms, col_email = st.columns(2)
    sms_body = urllib.parse.quote(share_text)
    email_subject = urllib.parse.quote(list_name)
    email_body = urllib.parse.quote(share_text)
    
    with col_sms:
        st.markdown(f'''
            <a href="sms:?&body={sms_body}" target="_blank">
                <button style="width:100%; border-radius:10px; background-color:#25D366; color:white; border:none; padding:10px; cursor:pointer;">
                    📱 Send via Text / SMS
                </button>
            </a>
            ''', unsafe_allow_html=True)

    with col_email:
        st.markdown(f'''
            <a href="mailto:?subject={email_subject}&body={email_body}">
                <button style="width:100%; border-radius:10px; background-color:#0078D4; color:white; border:none; padding:10px; cursor:pointer;">
                    ✉️ Send via Email
                </button>
            </a>
            ''', unsafe_allow_html=True)
else:
    st.info("Select items above to build your list.")
