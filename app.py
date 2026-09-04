# 2. RADAR VIEW (With Diagnostic Logging & Correct Engine Call)
with t_radar:
    st.markdown("### Production Pre-Screen")
    
    if st.button("🚀 Execute Remote Deep Scan", type="primary", use_container_width=True):
        if radar_svc:
            try:
                with st.spinner("Running AlphaForge Quantitative Engines..."):
                    # 1. Get symbols to scan (Looks for your CSV, falls back to active holdings)
                    csv_path = os.path.join(os.path.dirname(__file__), "data", "nse_stocks.csv")
                    symbols_to_scan = []
                    
                    if os.path.exists(csv_path):
                        df_univ = pd.read_csv(csv_path)
                        # Assumes the column in your CSV is named 'symbol' or 'SYMBOL'
                        col_name = 'SYMBOL' if 'SYMBOL' in df_univ.columns else 'symbol'
                        if col_name in df_univ.columns:
                            symbols_to_scan = df_univ[col_name].dropna().tolist()
                    
                    # Fallback if CSV isn't found: Scan your current portfolio
                    if not symbols_to_scan:
                        symbols_to_scan = [h['symbol'] for h in active_holdings]
                        st.info("Universe CSV not found. Scanning current holdings instead.")

                    # 2. Call the CORRECT function from Layer 3
                    radar_results = radar_svc.rank_symbols(symbols=symbols_to_scan, limit=30)
                    
                    # 3. Extract the 'ranked' pool from the dictionary
                    top_30_data = radar_results.get("ranked", [])
                    
                    if top_30_data:
                        st.success(f"Scan Complete: {radar_results.get('live_analyses')} Live | {radar_results.get('cache_hits')} Cached")
                        st.dataframe(pd.DataFrame(top_30_data), use_container_width=True, hide_index=True)
                    else:
                        st.warning("Scan completed but no stocks passed the Alpha 12 hard gates.")
                        
            except Exception as e:
                st.error(f"**Engine Crash:** {str(e)}")
                with st.expander("Show Full Crash Log"):
                    import traceback
                    st.code(traceback.format_exc())
        else:
             st.warning("⚠️ PC Scanning engines unlinked. Run on desktop to generate cache.")
             
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