import streamlit as st
import pandas as pd
import json
import os

# --- IMPORT LAYER 4 & 5 SERVICES ---
from services.alpha12_mapping_service import Alpha12MappingService
from services.alpha12_stability_service import Alpha12StabilityService
from services.alpha12_emergency_service import Alpha12EmergencyService

# --- IMPORT LAYER 3 & 7 SERVICES ---
try:
    from services.portfolio_market_refresh_service import PortfolioMarketRefreshService
    from services.research_radar_service import ResearchRadarService
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False

# --- MOBILE VIEWPORT CONFIG ---
st.set_page_config(page_title="AlphaForge", page_icon="📈", layout="centered", initial_sidebar_state="collapsed")

# --- INIT SERVICES (DEFENSIVE PATTERN) ---
@st.cache_resource
def load_services():
    mapping = Alpha12MappingService()
    stability = Alpha12StabilityService(mapping_service=mapping)
    emergency = Alpha12EmergencyService()
    
    market_refresh = None
    research_radar = None
    
    if SERVICES_AVAILABLE:
        try:
            market_refresh = PortfolioMarketRefreshService()
            research_radar = ResearchRadarService()
        except Exception:
            pass # Graceful degradation
            
    return mapping, stability, emergency, market_refresh, research_radar

mapping_svc, stability_svc, emergency_svc, market_refresh_svc, radar_svc = load_services()

# --- SIDEBAR: ENGINE CONTROLS ---
with st.sidebar:
    st.subheader("⚙️ Engine Controls")
    if st.button("🔄 Force Refresh Live Data"):
        if market_refresh_svc:
            with st.spinner("Syncing live NSE prices via StockService..."):
                try:
                    # Trigger the Layer 7 market refresh
                    market_refresh_svc.refresh_portfolio()
                    st.success("Market data synchronized!")
                    st.rerun()
                except Exception as e:
                    st.error("API timeout or data error. Try again.")
        else:
            st.warning("Refresh service unavailable on cloud.")

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
    active_holdings = [{'symbol': 'CASTROLIND', 'market_cap_category': 'SMALLCAP', 'current_price': 186.02, 'peak_price': 186.02, 'fundamental_status': 'INTACT'}]

map_res = mapping_svc.analyze()
stab_res = stability_svc.get_stability(mapping_result=map_res)
em_res = emergency_svc.evaluate_holdings(active_holdings)

# --- DASHBOARD UI ---
st.markdown("<h3 style='text-align: center; color: #4CAF50;'>AlphaForge Engine</h3>", unsafe_allow_html=True)

# Expanded tabs for full parity
tab1, tab2, tab3, tab4 = st.tabs(["🚨 Emergency", "🛡️ Stability", "🎯 Top 30 Radar", "🌐 Universe"])

# TAB 1: EMERGENCY RADAR
with tab1:
    if em_res.analysis_status == "CRITICAL":
        st.error(f"🚨 {em_res.summary}")
    else:
        st.success(f"✅ {em_res.summary}")
        
    for h in em_res.holdings_status:
        with st.container(border=True):
            cols = st.columns([2, 1, 1])
            cols[0].markdown(f"**{h.symbol}**")
            cols[1].metric("LTP", f"₹{h.current_price}")
            
            if h.emergency_level == "CRITICAL_EXIT":
                cols[2].error("EXIT")
            else:
                cols[2].success("HOLD")

# TAB 2: STABILITY OVERVIEW
with tab2:
    st.subheader("Anti-Churn Governance")
    c1, c2 = st.columns(2)
    c1.metric("Stability Score", f"{stab_res.stability_metrics.stability_score}/100")
    c2.metric("Churn Risk", stab_res.stability_metrics.churn_risk)
    st.progress(stab_res.stability_metrics.stability_score / 100.0)

# TAB 3: PRODUCTION RESEARCH RADAR (NEW)
with tab3:
    st.subheader("Elite Quality Pool")
    if radar_svc:
        if st.button("🚀 Run Deep Scan"):
            with st.spinner("Running quantitative composite engines..."):
                try:
                    top_30_data = radar_svc.get_current_radar()
                    st.dataframe(top_30_data, use_container_width=True)
                except Exception:
                    st.error("Could not fetch radar data. Ensure universe data is cached.")
    else:
        st.info("Research Radar service is initializing or missing dependencies.")

# TAB 4: UNCAPPED UNIVERSE
with tab4:
    df = pd.DataFrame([h.to_dict() for h in map_res.portfolio.holdings])
    if not df.empty:
        st.dataframe(df[['symbol', 'market_cap_category', 'mapping_status']], use_container_width=True)