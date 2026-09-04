import streamlit as st
import pandas as pd
import json
import os
import traceback

# --- DEFENSIVE IMPORTS ---
from services.alpha12_mapping_service import Alpha12MappingService
from services.alpha12_stability_service import Alpha12StabilityService
from services.alpha12_emergency_service import Alpha12EmergencyService

# Try to load PC-only services, fallback if running on cloud without local DBs
try:
    from services.portfolio_market_refresh_service import PortfolioMarketRefreshService
    from services.research_radar_service import ResearchRadarService
    PC_SERVICES_AVAILABLE = True
except ImportError:
    PC_SERVICES_AVAILABLE = False

# --- CONFIG ---
st.set_page_config(page_title="AlphaForge Mobile", page_icon="🗼", layout="centered")

# --- SERVICE INITIALIZATION ---
@st.cache_resource
def load_core_services():
    mapping = Alpha12MappingService()
    stability = Alpha12StabilityService(mapping_service=mapping)
    emergency = Alpha12EmergencyService()
    
    market_refresh = None
    research_radar = None
    if PC_SERVICES_AVAILABLE:
        try:
            market_refresh = PortfolioMarketRefreshService()
            research_radar = ResearchRadarService()
        except Exception:
            pass
            
    return mapping, stability, emergency, market_refresh, research_radar

map_svc, stab_svc, em_svc, refresh_svc, radar_svc = load_core_services()

# --- LOAD PORTFOLIO LEDGER ---
@st.cache_data(ttl=60) # Cache for 60s to prevent constant disk reads
def load_portfolio():
    json_path = os.path.join(os.path.dirname(__file__), "portfolio_state.json")
    holdings = []
    
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
            # Support both flat and nested JSON structures
            positions = data.get("positions", {})
            if isinstance(positions, list):
                for p in positions:
                    holdings.append({
                        'symbol': p.get('symbol', 'UNKNOWN'),
                        'market_cap_category': p.get('category', p.get('market_cap_category', 'SMALLCAP')),
                        'current_price': float(p.get('current_price', 0.0)),
                        'peak_price': float(p.get('current_price', 0.0)),
                        'fundamental_status': 'INTACT'
                    })
            else:
                for sym, p in positions.items():
                    holdings.append({
                        'symbol': sym,
                        'market_cap_category': p.get('category', p.get('market_cap_category', 'SMALLCAP')),
                        'current_price': float(p.get('current_price', 0.0)),
                        'peak_price': float(p.get('current_price', 0.0)),
                        'fundamental_status': 'INTACT'
                    })
    
    if not holdings:
        holdings = [{'symbol': 'CASTROLIND', 'market_cap_category': 'SMALLCAP', 'current_price': 186.0, 'peak_price': 186.0, 'fundamental_status': 'INTACT'}]
    return holdings

active_holdings = load_portfolio()
em_res = em_svc.evaluate_holdings(active_holdings)
map_res = map_svc.analyze()
stab_res = stab_svc.get_stability(mapping_result=map_res)

# --- HEADER UI ---
with st.container(border=True):
    col1, col2 = st.columns([3, 1], vertical_alignment="center")
    col1.markdown("<h2 style='margin-bottom:0;'>AlphaForge 🗼</h2>", unsafe_allow_html=True)
    if col2.button("🔄 Sync", use_container_width=True):
        if refresh_svc:
            try:
                refresh_svc.refresh_portfolio()
                st.toast("✅ Live Data Synced")
            except Exception:
                st.toast("⚠️ Sync Error")
        else:
            st.toast("📡 Cloud Cache Loaded")

# --- MAIN DASHBOARD TABS ---
t_emerg, t_radar, t_health = st.tabs(["🚨 Emergency", "🎯 Top 30 Radar", "🩺 Health"])

# 1. EMERGENCY LAYER
with t_emerg:
    if em_res.analysis_status == "CRITICAL":
        st.error(f"**Action Required:** {em_res.summary}", icon="🚨")
    else:
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

# 2. RADAR VIEW (Independent Autonomous Scan)
with t_radar:
    st.markdown("### Production Pre-Screen")
    
    if st.button("🚀 Execute Remote Deep Scan", type="primary", use_container_width=True):
        if radar_svc:
            try:
                with st.spinner("Running AlphaForge Quantitative Engines..."):
                    
                    # 1. Look for CSV, but have a massive built-in fallback universe for true independence
                    csv_path = os.path.join(os.path.dirname(__file__), "data", "nse_stocks.csv")
                    symbols_to_scan = []
                    
                    if os.path.exists(csv_path):
                        df_univ = pd.read_csv(csv_path)
                        col_name = 'SYMBOL' if 'SYMBOL' in df_univ.columns else 'symbol'
                        if col_name in df_univ.columns:
                            symbols_to_scan = df_univ[col_name].dropna().tolist()
                    
                    # 2. THE INDEPENDENT FALLBACK: If no CSV, scan a built-in high-quality universe
                    if not symbols_to_scan:
                        st.info("Initiating standalone cloud scan (Built-in Nifty Universe)...")
                        symbols_to_scan = [
                            "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", 
                            "ITC", "SBIN", "LT", "BAJFINANCE", "BHARTIARTL", 
                            "KOTAKBANK", "HAL", "CASTROLIND", "TATASTEEL", "ASIANPAINT", 
                            "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "WIPRO", 
                            "NESTLEIND", "HCLTECH", "POWERGRID", "NTPC", "M&M",
                            "AJANTPHARM", "HDFCLIFE", "BAJAJFINSV", "ONGC", "COALINDIA"
                        ]

                    # 3. Fire the Layer 3 Quantitative Engine
                    radar_results = radar_svc.rank_symbols(symbols=symbols_to_scan, limit=30)
                    top_30_data = radar_results.get("ranked", [])
                    
                    if top_30_data:
                        st.success(f"Scan Complete: {radar_results.get('live_analyses')} Live | {radar_results.get('cache_hits')} Cached")
                        st.dataframe(pd.DataFrame(top_30_data), use_container_width=True, hide_index=True)
                    else:
                        st.warning("Scan completed but no stocks passed the Alpha 12 hard gates.")
                        
            except Exception as e:
                st.error(f"**Engine Crash:** {str(e)}")
                with st.expander("Show Full Crash Log"):
                    st.code(traceback.format_exc())
        else:
             st.warning("⚠️ PC Scanning engines unlinked. Verify services folder is deployed.")
             
    # Static cache fallback
    radar_path = os.path.join(os.path.dirname(__file__), "data", "cache", "production_radar_snapshot.json")
    if os.path.exists(radar_path):
        try:
             with open(radar_path, 'r') as f:
                 radar_data = json.load(f)
             if radar_data:
                 st.dataframe(pd.DataFrame(radar_data), use_container_width=True, hide_index=True)
        except Exception:
             pass

# 3. HEALTH & STABILITY
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