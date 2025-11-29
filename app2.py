import streamlit as st
from datetime import date

st.set_page_config(page_title="Financials", page_icon="💼", layout="wide")

def brl(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
    except:
        return "R$ 0,00"

with st.sidebar:
    st.markdown("## Navigation")
    route = st.radio("Go to:", ["Dashboard","Cards","Transactions","Debts","Reports"])

def page_dashboard():
    st.title("📊 Dashboard")
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Due this month", brl(0))
    with c2: st.metric("Cards", 0)
    with c3: st.metric("Avg Utilization", "0.0%")
    with c4: st.metric("Monthly Spend", brl(0))
    st.info("MVP placeholder. Next: connect to Supabase.")

def page_cards():
    st.title("💳 Cards")
    with st.expander("➕ Add"):
        col1,col2,col3 = st.columns(3)
        with col1:
            st.text_input("Name*", placeholder="Nubank", key="card_name")
            st.selectbox("Brand", ["Visa","Mastercard","Elo","Amex","Other"], key="card_brand")
        with col2:
            st.text_input("Last 4", max_chars=4, key="card_last4")
            st.number_input("Limit (R$)*", min_value=0.0, step=100.0, key="card_limit")
        with col3:
            st.number_input("Closing day*", 1, 31, 2, key="card_close")
            st.number_input("Due day*", 1, 31, 10, key="card_due")
        st.color_picker("Color", "#10B981", key="card_color")
        if st.button("Save", type="primary"):
            st.success("Saved (demo)")

def page_transactions():
    st.title("🧾 Transactions")
    today = date.today()
    c1,c2,c3 = st.columns(3)
    with c1: st.date_input("Start", today.replace(day=1))
    with c2: st.date_input("End", today)
    with c3: st.selectbox("Card", ["All"])
    with st.expander("➕ Add"):
        st.text_input("Description*", placeholder="Supermarket")
        st.text_input("Category", placeholder="Groceries")
        st.selectbox("Type*", ["purchase","payment","fee","interest","refund"])
        st.number_input("Amount (R$)*", step=10.0, format="%.2f")
        if st.button("Save transaction", type="primary"):
            st.success("Saved (demo)")

def page_debts():
    st.title("🏦 Debts")
    with st.expander("➕ Add"):
        st.text_input("Name*", placeholder="Car loan")
        st.number_input("Principal*", min_value=0.0, step=100.0)
        st.number_input("APR % (annual)", min_value=0.0, step=0.1)
        st.number_input("Min payment", min_value=0.0, step=50.0)
        if st.button("Save", type="primary"):
            st.success("Saved (demo)")

def page_reports():
    st.title("📈 Reports")
    st.date_input("Month", value=date.today().replace(day=1))
    st.info("Reports will appear here (demo).")
    st.download_button("⬇️ Export CSV (demo)", data="col1,col2\nval1,val2\n", file_name="demo.csv", mime="text/csv")

if route == "Dashboard": page_dashboard()
elif route == "Cards": page_cards()
elif route == "Transactions": page_transactions()
elif route == "Debts": page_debts()
else: page_reports()
