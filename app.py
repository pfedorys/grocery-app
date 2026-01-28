import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Smart Grocery Planner", layout="wide")

# Load the Database (the CSV you provided)
@st.cache_data
def load_data():
    df = pd.read_csv('cleaned_food_list.csv')
    return df

df = load_data()

st.title("🛒 Smart Grocery List Builder")
st.write("Select items from the list below to find the best stores and prices.")

# 1. Selection Interface
categories = df['Category'].unique()
selected_items = []

st.sidebar.header("Filter by Category")
category_filter = st.sidebar.multiselect("Select Categories", categories, default=categories)

# Filter dataframe based on sidebar
filtered_df = df[df['Category'].isin(category_filter)]

# Checklist for items
st.subheader("Select Items to Buy")
with st.expander("Show/Hide Checklist"):
    for index, row in filtered_df.iterrows():
        if st.checkbox(f"{row['Item']} (${row['Best Price']:.2f} at {row['Best Store']})", key=row['Item']):
            selected_items.append(row)

# 2. Build the List and Calculate Totals
if selected_items:
    st.divider()
    st.header("Your Optimized Shopping List")
    
    shopping_df = pd.DataFrame(selected_items)
    
    # Group by store to tell user where to go
    stores_to_visit = shopping_df['Best Store'].unique()
    
    grand_total = 0
    
    for store in stores_to_visit:
        store_items = shopping_df[shopping_df['Best Store'] == store]
        store_total = store_items['Best Price'].sum()
        grand_total += store_total
        
        with st.expander(f"📍 {store} - Total: ${store_total:.2f}", expanded=True):
            for _, item in store_items.iterrows():
                st.write(f"- **{item['Item']}**: ${item['Best Price']:.2f}")
    
    st.divider()
    st.metric("Grand Total for Trip", f"${grand_total:.2f}")
    
    if st.button("Clear List"):
        st.rerun()
else:
    st.info("Check some items above to start building your list!")