import streamlit as st
import pandas as pd
import json
import os
import traceback

# --- DEFENSIVE IMPORTS ---
from services.alpha12_mapping_service import Alpha12MappingService
from services.alpha12_stability_service import Alpha12StabilityService
from services.alpha12_emergency_service import Alpha12EmergencyService

# --- CONFIG ---
st.set_page_config(page_title="AlphaForge Mobile", page_icon="🗼", layout="centered")

# --- SERVICE INITIALIZATION ---
@st.cache_resource
def load_core_services():
    mapping = Alpha12MappingService()
    stability = Alpha12StabilityService(mapping_service=mapping)
    emergency = Alpha12EmergencyService()
    return mapping, stability, emergency

map_svc, stab_svc, em_svc = load_core_services()

# --- LOAD DESKTOP JSON STATES ---
def load_desktop_state():
    base_dir = os.path.dirname(__file__)
    
    # 1. Load Portfolio & Reserve 8
    portfolio_path = os.path.join(base_dir, "portfolio_state.json")
    holdings = []
    reserve_8 = []
    
    if os.path.exists(portfolio_path):
        with open(portfolio_path, "r") as f:
            data = json.load(f)
            positions = data.get("positions", {})
            
            if isinstance(positions, list):
                for p in positions:
                    holdings.append({
                        'symbol': p.get('symbol', 'UNKNOWN'),
                        'category': p.get('category', p.get('market_cap_category', 'SMALLCAP')),
                        'current_price': float(p.get('current_price', 0.0)),
                        'peak_price': float(p.get('peak_price', p.get('current_price', 0.0))),
                        'fundamental_status': 'INTACT'
                    })
            else:
                for sym, p in positions.items():
                    holdings.append({
                        'symbol': sym,
                        'category': p.get('category', p.get('market_cap_category', 'SMALLCAP')),
                        'current_price': float(p.get('current_price', 0.0)),
                        'peak_price': float(p.get('peak_price', p.get('current_price', 0.0))),
                        'fundamental_status': 'INTACT'
                    })
            
            reserve_8 = data.get("reserve_8", [])
            
    # 2. Load Production Radar 30
    radar_path = os.path.join(base_dir, "data", "cache", "production_radar_snapshot.json")
    radar_30 = []
    if os.path.exists(radar_path):
        with open(radar_path, "r") as f:
            radar_data = json.load(f)
            # Handle both dictionary {"ranked": [...]} and raw list [...] structures
            radar_30 = radar_data.get("ranked", []) if isinstance(radar_data, dict) else radar_data
            
    return holdings, reserve_8, radar_30

# Load actual data
active_holdings, reserve_bench, radar_list = load_desktop_state()

# Run Health Services on Loaded Data
em_res = em_svc.evaluate_holdings(active_holdings) if active_holdings else None
map_res = map_svc.analyze()
stab_res = stab_svc.get_stability(mapping_result=map_res)

# --- HEADER UI ---
with st.container(border=True):
    col1, col2 = st.columns([3, 1], vertical_alignment="center")
    col1.markdown("<h2 style='margin-bottom:0;'>AlphaForge 🗼</h2>", unsafe_allow_html=True)
    if col2.button("🔄 Reload Glass", use_container_width=True):
        st.toast("✅ Synchronized with Desktop JSON Cache")

# --- MAIN DASHBOARD TABS ---
t_alpha12, t_reserve8, t_radar30, t_health, t_rebalance = st.tabs(["👑 Alpha 12", "🛡️ Reserve 8", "🎯 Radar 30", "🩺 Health", "⚖️ SIP"])

# 1. ALPHA 12
with t_alpha12:
    st.markdown("### Active Portfolio")
    if not active_holdings:
        st.warning("⚠️ `portfolio_state.json` missing or empty. Push desktop files to Git.")
    else:
        if em_res and em_res.analysis_status == "CRITICAL":
            st.error(f"**Action Required:** {em_res.summary}", icon="🚨")
        elif em_res:
            st.success(f"**System Nominal:** {em_res.summary}", icon="✅")
            
        for h in em_res.holdings_status:
            with st.container(border=True):
                cols = st.columns([2, 2, 1], vertical_alignment="center")
                cols[0].markdown(f"**{h.symbol}**")
                cols[1].markdown(f"LTP: ₹{h.current_price:.1f}")
                
                if h.emergency_level == "CRITICAL_EXIT":
                    cols[2].error("EXIT")
                elif h.emergency_level == "WARNING":
                    cols[2].warning("REVIEW")
                else:
                    cols[2].success("HOLD")

# 2. RESERVE 8
with t_reserve8:
    st.markdown("### High-Conviction Bench")
    if not reserve_bench:
        st.warning("⚠️ No Reserve 8 found in desktop state. Push latest sync.")
    else:
        for idx, sym in enumerate(reserve_bench, 1):
            with st.container(border=True):
                st.markdown(f"**{idx}. {sym}**")

# 3. RADAR 30
with t_radar30:
    st.markdown("### Desktop Production Radar")
    if not radar_list:
        st.warning("⚠️ `data/cache/production_radar_snapshot.json` missing. Run scan on PC and push to Git.")
    else:
        st.success(f"✅ Exact Desktop Mirror Loaded: {len(radar_list)} Stocks")
        df_display = pd.DataFrame(radar_list)
        if not df_display.empty:
            st.dataframe(df_display, use_container_width=True, hide_index=True)

# 4. HEALTH & STABILITY
with t_health:
    st.markdown("### Anti-Churn Governance")
    metrics = stab_res.stability_metrics
    col1, col2 = st.columns(2)
    with col1.container(border=True):
        st.metric("Stability Score", f"{metrics.stability_score}/100")
    with col2.container(border=True):
        st.metric("Churn Risk", metrics.churn_risk)
    st.progress(metrics.stability_score / 100.0)
    st.info(metrics.rationale)

# 5. SIP ALLOCATOR
with t_rebalance:
    st.markdown("### Capital Allocator")
    capital = st.number_input("Capital to Deploy (₹)", min_value=0, value=50000, step=5000)
    
    if st.button("Calculate SIP Targets", use_container_width=True):
        if not active_holdings:
            st.error("No active holdings to allocate to.")
        else:
            st.success(f"Optimal allocation for ₹{capital:,} across Alpha 12:")
            per_stock_target = capital / max(len(active_holdings), 1)
            
            for h in active_holdings:
                price = h.get('current_price', 1.0)
                if price > 0:
                    shares_to_buy = int(per_stock_target // price)
                    alloc = shares_to_buy * price
                    with st.container(border=True):
                        cols = st.columns([2, 1, 1])
                        cols[0].markdown(f"**{h['symbol']}**")
                        cols[1].markdown(f"{shares_to_buy} shares")
                        cols[2].markdown(f"₹{alloc:,.0f}")