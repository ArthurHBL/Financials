import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta, date
import bcrypt

st.set_page_config(page_title="Financials", page_icon="💼", layout="wide")

# ============ Supabase client (secrets-based) ============
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# ============ User Manager ============
class UserManager:
    def __init__(self, client: Client):
        self.client = client
        self.users = {}
        self.load_users()

    def load_users(self):
        try:
            resp = self.client.table('users').select('*').execute()
            self.users = {u['username']: u for u in (resp.data or [])}
            if "admin" not in self.users:
                self.create_default_admin()
        except Exception as e:
            st.error(f"Error loading users: {e}")
            self.users = {}

    def create_default_admin(self):
        row = {
            'username': 'admin',
            'password_hash': self.hash_pw('ChangeThis123!'),
            'name': 'System Administrator',
            'email': 'admin@example.com',
            'plan': 'admin',
            'expires': '2030-12-31',
            'created': datetime.utcnow().isoformat()
        }
        try:
            self.client.table('users').upsert(row).execute()
            self.users['admin'] = row
        except Exception as e:
            st.error(f"Error creating default admin: {e}")

    def hash_pw(self, pw: str) -> str:
        return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_pw(self, pw: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(pw.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False

    # Restrict to admin only
    def authenticate(self, username: str, password: str):
        if username != 'admin':
            return False, "Only the admin account is allowed."
        u = self.users.get('admin')
        if not u or not self.verify_pw(password, u.get('password_hash', '')):
            return False, "Invalid username or password"
        # Update login stats
        try:
            new_count = (u.get('login_count', 0) + 1)
            self.client.table('users').update({
                'last_login': datetime.utcnow().isoformat(),
                'login_count': new_count
            }).eq('username', 'admin').execute()
            u['login_count'] = new_count
        except Exception:
            pass
        return True, u

    def change_admin_password(self, current_pw: str, new_pw: str):
        u = self.users.get('admin')
        if not u:
            return False, "Admin not found."
        if not self.verify_pw(current_pw, u.get('password_hash', '')):
            return False, "Current password is incorrect."
        try:
            new_hash = self.hash_pw(new_pw)
            self.client.table('users').update({
                'password_hash': new_hash
            }).eq('username', 'admin').execute()
            # update local cache
            self.users['admin']['password_hash'] = new_hash
            return True, "Password updated successfully."
        except Exception as e:
            return False, f"Error updating password: {e}"

    def admin_using_default_password(self) -> bool:
        u = self.users.get('admin')
        if not u:
            return False
        # Verifica se a senha atual ainda é a padrão
        return self.verify_pw("ChangeThis123!", u.get('password_hash', ''))

user_manager = UserManager(supabase)

# ============ Session ============
if "user" not in st.session_state:
    st.session_state.user = None

# ============ Auth UI (somente admin, sem registro) ============
def render_auth_ui():
    st.title("🔐 Financials — Admin")
    with st.form("login_form"):
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password")
        ok = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if ok:
            success, res = user_manager.authenticate(username, password)
            if success:
                st.session_state.user = {
                    "username": res['username'],
                    "name": res.get('name', 'Admin'),
                    "plan": res.get('plan', 'admin'),
                    "expires": res.get('expires', '')
                }
                st.success("Logged in")
                st.rerun()
            else:
                st.error(res)

def require_login():
    if st.session_state.user is None:
        render_auth_ui()
        st.stop()

def user_header():
    u = st.session_state.user
    st.caption(f"Hello, {u['name']} — plan: {u.get('plan','admin')}")
    if user_manager.admin_using_default_password():
        st.warning("Você está usando a senha padrão do admin. Altere em Settings.")
    if st.button("Sign out", use_container_width=True):
        st.session_state.user = None
        st.rerun()

def brl(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
    except:
        return "R$ 0,00"

# ============ Protect before building sidebar ============
require_login()

# ============ Sidebar & Routing ============
with st.sidebar:
    user_header()
    st.markdown("## Navigation")
    route = st.radio(
        "Go to:",
        ["Dashboard","Cards","Transactions","Debts","Reports","Settings"],
        key="nav_radio"
    )

# ============ Pages ============
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

def page_settings():
    st.title("⚙️ Settings")
    st.subheader("Change admin password")
    with st.form("change_pw_form"):
        current = st.text_input("Current password", type="password")
        new = st.text_input("New password", type="password")
        confirm = st.text_input("Confirm new password", type="password")
        ok = st.form_submit_button("Update password", type="primary", use_container_width=False)
        if ok:
            if not current or not new or not confirm:
                st.error("Please fill all fields.")
            elif new != confirm:
                st.error("New password and confirmation do not match.")
            elif len(new) < 8:
                st.error("Password must be at least 8 characters.")
            else:
                success, msg = user_manager.change_admin_password(current, new)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# ============ Render ============
if route == "Dashboard": page_dashboard()
elif route == "Cards": page_cards()
elif route == "Transactions": page_transactions()
elif route == "Debts": page_debts()
elif route == "Reports": page_reports()
elif route == "Settings": page_settings()
else:
    page_dashboard()
