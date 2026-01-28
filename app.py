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

# Logic for Clear All button
if "reset" not in st.session_state:
    st.session_state.reset = False

def reset_list():
    for key in st.session_state.keys():
        if key.startswith("check_"):
            st.session_state[key] = False

st.title("🛒 Smart Grocery List Builder")

# Top controls
col_reset, _ = st.columns([1, 4])
with col_reset:
    if st.button("🔄 Clear All Selections"):
        reset_list()
        st.rerun()

# 1. Selection Interface
categories = df['Category'].unique()
selected_items = []

st.sidebar.header("Filter")
category_filter = st.sidebar.multiselect("Select Categories", categories, default=categories)
filtered_df = df[df['Category'].isin(category_filter)]

st.subheader("Select Items to Buy")
with st.expander("Show Checklist", expanded=True):
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
    grand_total =
