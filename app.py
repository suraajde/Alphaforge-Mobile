import streamlit as st
import pandas as pd
import json
import os
from services.alpha12_mapping_service import Alpha12MappingService
from services.alpha12_stability_service import Alpha12StabilityService
from services.alpha12_emergency_service import Alpha12EmergencyService

# --- MOBILE VIEWPORT CONFIG ---
st.set_page_config(page_title="AlphaForge", page_icon="📈", layout="centered", initial_sidebar_state="collapsed")

# --- INIT SERVICES ---
@st.cache_resource
def load_services():
    mapping = Alpha12MappingService()
    stability = Alpha12StabilityService(mapping_service=mapping)
    emergency = Alpha12EmergencyService()
    return mapping, stability, emergency

mapping_svc, stability_svc, emergency_svc = load_services()

# --- LOAD REAL PORTFOLIO STATE DYNAMICALLY ---
json_path = os.path.join(os.path.dirname(__file__), "portfolio_state.json")
active_holdings = []

if os.path.exists(json_path):
    with open(json_path, "r") as f:
        state_data = json.load(f)
        for symbol, details in state_data.get("positions", {}).items():
            active_holdings.append({
                'symbol': symbol,
                'market_cap_category': details.get('category', 'SMALLCAP'),
                'current_price': details.get('current_price', 0.0),
                'peak_price': details.get('current_price', 0.0),
                'fundamental_status': 'INTACT'
            })

if not active_holdings:
    active_holdings = [
        {'symbol': 'CASTROLIND', 'market_cap_category': 'SMALLCAP', 'current_price': 186.02, 'peak_price': 186.02, 'fundamental_status': 'INTACT'}
    ]

map_res = mapping_svc.analyze()
stab_res = stability_svc.get_stability(mapping_result=map_res)
em_res = emergency_svc.evaluate_holdings(active_holdings)

# --- DASHBOARD UI ---
st.markdown("<h3 style='text-align: center; color: #4CAF50;'>AlphaForge Active</h3>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🚨 Radar", "🛡️ Overview", "🌐 Universe"])

# TAB 1: EMERGENCY RADAR
with tab1:
    if em_res.analysis_status == "CRITICAL":
        st.error(f"🚨 {em_res.summary}")
    elif em_res.analysis_status == "WARNING":
        st.warning(f"⚠️ {em_res.summary}")
    else:
        st.success(f"✅ {em_res.summary}")
        
    for h in em_res.holdings_status:
        with st.container(border=True):
            st.markdown(f"**{h.symbol}** ({h.market_cap_category})")
            cols = st.columns(3)
            cols[0].metric("Price", f"₹{h.current_price}")
            cols[1].metric("Drawdown", f"{h.drawdown_pct}%")
            
            if h.emergency_level == "CRITICAL_EXIT":
                cols[2].error(h.action_required)
                st.error(" | ".join(h.triggers))
            elif h.emergency_level in ["WARNING", "VOLATILITY_DIP"]:
                cols[2].warning(h.action_required)
                st.caption(" | ".join(h.triggers))
            else:
                cols[2].success(h.action_required)

# TAB 2: STABILITY OVERVIEW
with tab2:
    st.subheader("Tenure & Churn Protection")
    metrics = stab_res.stability_metrics
    c1, c2 = st.columns(2)
    c1.metric("Stability Score", f"{metrics.stability_score}/100")
    c2.metric("Churn Risk", metrics.churn_risk)
    
    st.info(metrics.rationale)
    st.progress(metrics.stability_score / 100.0)

# TAB 3: UNCAPPED UNIVERSE
with tab3:
    st.subheader(f"Candidates ({map_res.portfolio.total_alpha12_holdings})")
    df = pd.DataFrame([h.to_dict() for h in map_res.portfolio.holdings])
    if not df.empty:
        clean_df = df[['symbol', 'market_cap_category', 'mapping_status']]
        st.dataframe(clean_df, use_container_width=True, hide_index=True)