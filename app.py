import streamlit as st
import pandas as pd
import urllib.parse

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

# Add Stock Status filter to sidebar
if 'Stock Status' in df.columns:
    statuses = df['Stock Status'].unique()
    status_filter = st.sidebar.multiselect("Filter by Stock Status", statuses, default=statuses)
    filtered_df = df[
        (df['Category'].isin(category_filter)) & 
        (df['Stock Status'].isin(status_filter)) &
        (df['Item'].str.contains(search_query, case=False, na=False))
    ]
else:
    filtered_df = df[
        (df['Category'].isin(category_filter)) & 
        (df['Item'].str.contains(search_query, case=False, na=False))
    ]

st.subheader("Select Items to Buy")
selected_items = []
with st.expander("Show Checklist", expanded=True):
    for index, row in filtered_df.iterrows():
        stock_label = f" [{row['Stock Status']}]" if 'Stock Status' in df.columns else ""
        item_label = f"{row['Item']}{stock_label} (${row['Best Price']:.2f} at {row['Best Store']})"
        if st.checkbox(item_label, key=f"check_{index}"):
            selected_items.append(row)

# 2. Optimized List & Comparisons
if selected_items:
    st.divider()
    shopping_df = pd.DataFrame(selected_items)
    
    st.header("📋 Optimized Shopping List")
    best_grand_total = 0
    
    stores_to_visit = shopping_df['Best Store'].unique()
    for store in stores_to_visit:
        items_at_store = shopping_df[shopping_df['Best Store'] == store]
        subtotal = items_at_store['Best Price'].sum()
        best_grand_total += subtotal
        
        with st.expander(f"📍 {store} - Subtotal: ${subtotal:.2f}", expanded=True):
            for _, item in items_at_store.iterrows():
                alts = []
                for s in STORES:
                    if s != store and not pd.isna(item[s]):
                        diff = item[s] - item['Best Price']
                        alts.append(f"{s} (+${diff:.2f})")
                alt_text = f" | Alts: {', '.join(alts)}" if alts else " | No alts"
                st.write(f"✅ **{item['Item']}**: ${item['Best Price']:.2f}{alt_text}")

    # 3. One-Stop Comparison
    st.divider()
    st.header("🚗 One-Stop Shopping Calculator")
    one_stop_data = []
    for store in STORES:
        available_items = shopping_df[~shopping_df[store].isna()]
        store_total = available_items[store].sum()
        missing_count = len(shopping_df) - len(available_items)
        if len(available_items) > 0:
            diff = store_total - best_grand_total
            status = f"Missing {missing_count} items" if missing_count > 0 else "All items available"
            one_stop_data.append({"Store": store, "Total Price": f"${store_total:.2f}", "Extra Cost": f"+${diff:.2f}", "Availability": status})

    st.table(pd.DataFrame(one_stop_data))
    st.metric("Best Possible Total", f"${best_grand_total:.2f}")

    # 4. Save & Share
    st.header("💾 Save & Share")
    list_name = st.text_input("List Name", "My Grocery List")
    share_text = f"Optimized Total: ${best_grand_total:.2f}\n" + "\n".join([f"- {row['Item']}: ${row['Best Price']:.2f} at {row['Best Store']}" for _, row in shopping_df.iterrows()])
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<a href="sms:?&body={urllib.parse.quote(share_text)}" target="_blank"><button style="width:100%; border-radius:10px; background-color:#25D366; color:white; border:none; padding:10px; cursor:pointer;">📱 Text List</button></a>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<a href="mailto:?subject={urllib.parse.quote(list_name)}&body={urllib.parse.quote(share_text)}"><button style="width:100%; border-radius:10px; background-color:#0078D4; color:white; border:none; padding:10px; cursor:pointer;">✉️ Email List</button></a>', unsafe_allow_html=True)
else:
    st.info("Select items above to build your list.")
