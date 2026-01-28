import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Smart Grocery Planner", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('cleaned_food_list.csv')
    df.columns = df.columns.str.strip()
    if 'Best Price' in df.columns:
        df['Best Price'] = pd.to_numeric(df['Best Price'].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
    df = df.dropna(subset=['Item'])
    return df

df = load_data()

st.title("🛒 Smart Grocery List Builder")

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
    
    # Prepare text for sharing
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

    # --- NEW: SAVE & SHARE SECTION ---
    st.header("💾 Save & Share")
    
    list_name = st.text_input("Give this list a name (e.g., 'Weekly Run' or 'BBQ Prep')", "My Grocery List")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # SMS Share (Works on Mobile)
        sms_body = urllib.parse.quote(share_text)
        st.markdown(f'<a href="sms:?&body={sms_body}" style="text-decoration:none;"><button style="width:100%; border-radius:10px; background-color:#25D366; color:white; border:none; padding:10px;">📱 Send via Text / SMS</button></a>', unsafe_allow_allow_html=True)

    with col2:
        # Email Share
        email_subject = urllib.parse.quote(list_name)
        email_body = urllib.parse.quote(share_text)
        st.markdown(f'<a href="mailto:?subject={email_subject}&body={email_body}" style="text-decoration:none;"><button style="width:100%; border-radius:10px; background-color:#0078D4; color:white; border:none; padding:10px;">✉️ Send via Email</button></a>', unsafe_allow_html=True)

    st.info("💡 To 'Save' this list for later, just click the Send via Email button and mail it to yourself!")

else:
    st.info("Check items above to build your list.")
