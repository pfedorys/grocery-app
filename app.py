import streamlit as st
import pandas as pd

st.set_page_config(page_title="Smart Grocery Planner", layout="wide")

@st.cache_data
def load_data():
    # Load the CSV
    df = pd.read_csv('cleaned_food_list.csv')
    
    # Clean column names (removes hidden spaces like 'Best Price ')
    df.columns = df.columns.str.strip()
    
    # Ensure 'Best Price' is a number even if it has '$' or ','
    if 'Best Price' in df.columns:
        df['Best Price'] = pd.to_numeric(df['Best Price'].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
    
    # Drop rows where the Item name is missing
    df = df.dropna(subset=['Item'])
    return df

df = load_data()

st.title("🛒 Smart Grocery List Builder")

# Safety Check: If the column is STILL missing, show the user what columns ARE there
if 'Best Price' not in df.columns:
    st.error(f"Column 'Best Price' not found. Your file has: {list(df.columns)}")
    st.stop()

# 1. Selection Interface
categories = df['Category'].unique()
selected_items = []

st.sidebar.header("Filter")
category_filter = st.sidebar.multiselect("Select Categories", categories, default=categories)
filtered_df = df[df['Category'].isin(category_filter)]

st.subheader("Select Items to Buy")
with st.expander("Show Checklist", expanded=True):
    for index, row in filtered_df.iterrows():
        # Display name, price, and store
        price_val = row['Best Price']
        store_val = row['Best Store'] if 'Best Store' in df.columns else "Unknown Store"
        
        item_label = f"{row['Item']} (${price_val:.2f} at {store_val})"
        if st.checkbox(item_label, key=f"check_{index}"):
            selected_items.append(row)

# 2. Build the List and Totals
if selected_items:
    st.divider()
    shopping_df = pd.DataFrame(selected_items)
    
    # Group by store for the shopping trip
    stores = shopping_df['Best Store'].unique() if 'Best Store' in df.columns else ["Unknown Store"]
    
    grand_total = 0
    for store in stores:
        store_items = shopping_df[shopping_df['Best Store'] == store]
        store_total = store_items['Best Price'].sum()
        grand_total += store_total
        
        with st.expander(f"📍 {store} - Subtotal: ${store_total:.2f}", expanded=True):
            for _, item in store_items.iterrows():
                st.write(f"- **{item['Item']}**: ${item['Best Price']:.2f}")
    
    st.divider()
    st.metric("Total Trip Cost", f"${grand_total:.2f}")
else:
    st.info("Check items above to build your list.")
