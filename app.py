import streamlit as st
import pandas as pd
import json
import os
import traceback

# --- CORE SERVICES ---
from services.alpha12_mapping_service import Alpha12MappingService
from services.alpha12_stability_service import Alpha12StabilityService
from services.alpha12_emergency_service import Alpha12EmergencyService
from services.research_radar_service import ResearchRadarService

# Try to load Layer 4 (Ensure this exists in your services folder)
try:
    from services.alpha12_selection_service import Alpha12SelectionService
    selection_svc = Alpha12SelectionService()
except ImportError:
    selection_svc = None

# --- CONFIG ---
st.set_page_config(page_title="AlphaForge Cloud", page_icon="🗼", layout="centered")

@st.cache_resource
def load_core_services():
    return Alpha12MappingService(), Alpha12StabilityService(mapping_service=Alpha12MappingService()), Alpha12EmergencyService(), ResearchRadarService()

map_svc, stab_svc, em_svc, radar_svc = load_core_services()

# --- STATE MANAGEMENT ---
if 'radar_30' not in st.session_state:
    st.session_state.radar_30 = []
if 'alpha_12' not in st.session_state:
    st.session_state.alpha_12 = []
if 'reserve_8' not in st.session_state:
    st.session_state.reserve_8 = []

# --- HEADER UI ---
st.markdown("<h2 style='margin-bottom:0;'>AlphaForge 🗼</h2>", unsafe_allow_html=True)
st.caption("Fully Autonomous Cloud Engine")

if st.button("🚀 Execute Autonomous Market Scan", type="primary", use_container_width=True):
    try:
        with st.spinner("Scanning universe & compiling Alpha 12... This may take a minute."):
            # 1. Load the Full Universe
            csv_path = os.path.join(os.path.dirname(__file__), "data", "nse_stocks.csv")
            if not os.path.exists(csv_path):
                st.error("⚠️ Universe CSV missing. Please upload `nse_stocks.csv` to the data folder.")
                st.stop()
                
            df_univ = pd.read_csv(csv_path)
            col_name = 'SYMBOL' if 'SYMBOL' in df_univ.columns else 'symbol'
            symbols_to_scan = df_univ[col_name].dropna().tolist()

            # 2. Layer 3: Execute Radar Scan
            radar_results = radar_svc.rank_symbols(symbols=symbols_to_scan, limit=30)
            st.session_state.radar_30 = radar_results.get("ranked", [])
            
            # 3. Layer 4: Selection & Sector Caps
            if selection_svc and st.session_state.radar_30:
                selection_results = selection_svc.select_portfolio(st.session_state.radar_30)
                st.session_state.alpha_12 = selection_results.get("alpha_12", [])
                st.session_state.reserve_8 = selection_results.get("reserve_8", [])
            elif st.session_state.radar_30:
                # Fallback if Layer 4 service is missing: Top 12 and Next 8 mathematically
                st.session_state.alpha_12 = st.session_state.radar_30[:12]
                st.session_state.reserve_8 = st.session_state.radar_30[12:20]
                
            st.success("✅ Market Scan & Layer 4 Allocation Complete!")
    except Exception as e:
        st.error(f"Engine Crash: {e}")
        with st.expander("Show Log"):
            st.code(traceback.format_exc())

# --- DYNAMIC TABS ---
t_alpha12, t_reserve8, t_radar30 = st.tabs(["👑 Alpha 12", "🛡️ Reserve 8", "🎯 Radar 30"])

with t_alpha12:
    if not st.session_state.alpha_12:
        st.info("Run the market scan to generate Alpha 12.")
    else:
        for idx, h in enumerate(st.session_state.alpha_12, 1):
            with st.container(border=True):
                st.markdown(f"**{idx}. {h.get('symbol', 'UNKNOWN')}**")

with t_reserve8:
    if not st.session_state.reserve_8:
        st.info("Run the market scan to generate Reserve 8.")
    else:
        for idx, h in enumerate(st.session_state.reserve_8, 1):
            with st.container(border=True):
                st.markdown(f"**{idx}. {h.get('symbol', 'UNKNOWN')}**")

with t_radar30:
    if not st.session_state.radar_30:
        st.info("Run the market scan to view the Top 30.")
    else:
        st.dataframe(pd.DataFrame(st.session_state.radar_30), use_container_width=True, hide_index=True)