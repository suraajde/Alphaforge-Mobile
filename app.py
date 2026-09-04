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
@st.cache_data(ttl=60)
def load_portfolio():
    json_path = os.path.join(os.path.dirname(__file__), "portfolio_state.json")
    holdings = []
    reserve = []
    
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
            positions = data.get("positions", {})
            
            # Load Active Holdings
            if isinstance(positions, list):
                for p in positions:
                    holdings.append({
                        'symbol': p.get('symbol', 'UNKNOWN'),
                        'category': p.get('category', 'SMALLCAP'),
                        'current_price': float(p.get('current_price', 0.0)),
                        'peak_price': float(p.get('peak_price', p.get('current_price', 0.0))),
                        'fundamental_status': 'INTACT'
                    })
            else:
                for sym, p in positions.items():
                    holdings.append({
                        'symbol': sym,
                        'category': p.get('category', 'SMALLCAP'),
                        'current_price': float(p.get('current_price', 0.0)),
                        'peak_price': float(p.get('peak_price', p.get('current_price', 0.0))),
                        'fundamental_status': 'INTACT'
                    })
            
            # Load Reserve (if exists in JSON)
            reserve_data = data.get("reserve_8", [])
            if reserve_data:
                reserve = reserve_data
                
    if not holdings:
        holdings = [{'symbol': 'CASTROLIND', 'category': 'SMALLCAP', 'current_price': 186.0, 'peak_price': 186.0, 'fundamental_status': 'INTACT'}]
    
    # Fallback Reserve 8 if not found in JSON
    if not reserve:
        reserve = ["SYNGENE", "CAMS", "CDSL", "KPITTECH", "TATAELXSI", "ASTRAL", "POLYCAB", "DIXON"]
        
    return holdings, reserve

active_holdings, reserve_8 = load_portfolio()
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
t_alpha12, t_reserve8, t_radar30, t_health, t_rebalance = st.tabs(["👑 Alpha 12", "🛡️ Reserve 8", "🎯 Radar 30", "🩺 Health", "⚖️ SIP"])

# 1. ALPHA 12 (Active Portfolio + Emergency)
with t_alpha12:
    st.markdown("### Active Portfolio")
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

# 2. RESERVE 8 (Bench)
with t_reserve8:
    st.markdown("### High-Conviction Bench")
    st.info("Top-ranked candidates ready for rotation upon Alpha 12 exit triggers.")
    for idx, sym in enumerate(reserve_8, 1):
        with st.container(border=True):
            st.markdown(f"**{idx}. {sym}**")

# 3. RADAR 30 (Engine)
with t_radar30:
    st.markdown("### Production Pre-Screen")
    
    if st.button("🚀 Execute Remote Deep Scan", type="primary", use_container_width=True):
        if radar_svc:
            try:
                with st.spinner("Running AlphaForge Quantitative Engines..."):
                    csv_path = os.path.join(os.path.dirname(__file__), "data", "nse_stocks.csv")
                    symbols_to_scan = []
                    
                    if os.path.exists(csv_path):
                        df_univ = pd.read_csv(csv_path)
                        col_name = 'SYMBOL' if 'SYMBOL' in df_univ.columns else 'symbol'
                        if col_name in df_univ.columns:
                            symbols_to_scan = df_univ[col_name].dropna().tolist()
                    
                    if not symbols_to_scan:
                        st.info("Initiating standalone cloud scan (Mid/Small Cap Universe)...")
                        symbols_to_scan = [
                            "CASTROLIND", "AJANTPHARM", "NAVINFLUOR", "ASTRAL", "POLYCAB", 
                            "DIXON", "KPITTECH", "TATAELXSI", "DEEPAKNTR", "LALPATHLAB", 
                            "SYNGENE", "CAMS", "CDSL", "RADICO", "DEVYANI", 
                            "SUVENPHAR", "ANGELONE", "JBCHEPHARM", "NATCOPHARM", "GRANULES", 
                            "BALAMINES", "ALKYLAMINE", "FINEORG", "CLEAN", "CERA", 
                            "KEI", "RATNAMANI", "SUPREMEIND", "FINCABLES", "CENTURYPLY"
                        ]

                    radar_results = radar_svc.rank_symbols(symbols=symbols_to_scan, limit=30)
                    top_30_data = radar_results.get("ranked", [])
                    
                    if top_30_data:
                        st.success(f"Scan Complete: {radar_results.get('live_analyses')} Live | {radar_results.get('cache_hits')} Cached")
                        
                        # Format the DataFrame for Mobile Readability
                        df_display = pd.DataFrame(top_30_data)
                        if not df_display.empty:
                            display_cols = ['symbol', 'composite_score', 'classification', 'readiness_score']
                            existing_cols = [c for c in display_cols if c in df_display.columns]
                            st.dataframe(df_display[existing_cols], use_container_width=True, hide_index=True)
                    else:
                        st.warning("Scan completed but no stocks passed the Alpha 12 hard gates.")
                        
            except Exception as e:
                st.error(f"**Engine Crash:** {str(e)}")
                with st.expander("Show Full Crash Log"):
                    st.code(traceback.format_exc())
        else:
             st.warning("⚠️ PC Scanning engines unlinked. Verify services folder is deployed.")

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

# 5. REBALANCING & SIP (Layer 6)
with t_rebalance:
    st.markdown("### Capital Allocator")
    st.caption("Route fresh capital to target weights.")
    
    capital = st.number_input("Capital to Deploy (₹)", min_value=0, value=50000, step=5000)
    
    if st.button("Calculate SIP Targets", use_container_width=True):
        st.success(f"Calculating optimal allocation for ₹{capital:,} across Alpha 12...")
        
        # Simple Equal-Weight Simulation for the UI
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