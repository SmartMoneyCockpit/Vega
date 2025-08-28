def render_stay_or_reenter():
    st.header("Stay Out vs. Get Back In")
    cfg = load_config()
    cfg = _config_pane(cfg)
    _links_bar(cfg)

    tabs = st.tabs(["Decision", "Re-Entry Tracker"])
    with tabs[0]:
        ticker = st.text_input("Ticker", value="SPY").upper().strip()
        st.caption("Use any tradable symbol supported by yfinance.")

        # Relative Strength mini-panel
        _relative_strength_panel(ticker, cfg)

        # Earnings
        dte = _earnings_block(ticker)

        # Breadth & risk mode
        breadth_mode, breadth_val, risk_on = _breadth_block(cfg)

        # Triggers
        exit_count, re_count = _trigger_checklists()

        # Entry / R:R / sizing
        entry, stop, target, computed_rr, psi = _entry_rr_block(cfg)

        # Options vs stock selector
        stance = _options_selector_block(ticker, cfg)

        # Decision
        action, why = decide_action(exit_count, re_count, cfg, dte, computed_rr)
        st.subheader("Decision")
        _decision_output(action)
        st.write(why)

        # Journal logging & export
        rationale_text = st.text_area(
            "Rationale note (optional)",
            value=("Re-entered on strength breakout" if action == "GET_BACK_IN"
                   else ("Exited for capital efficiency" if action == "STAY_OUT"
                         else "Mixed signals; on watch"))
        )

        if st.button("Log Decision", type="primary"):
            dec = Decision(
                timestamp=dt.datetime.now().isoformat(timespec='seconds'),
                ticker=ticker,
                action=action,
                rationale=rationale_text,
                entry=entry,
                stop=stop,
                target=target,
                reward_risk=float(computed_rr) if computed_rr is not None else None,
                days_to_earnings=int(dte) if dte is not None else None,
                exit_triggers=int(exit_count),
                reentry_triggers=int(re_count),
                breadth_mode=breadth_mode,
                breadth_value=float(breadth_val) if breadth_val is not None else None,
                sector_etf=cfg["relative_strength"].get("sector_etf", ""),
                rs_benchmark=cfg["relative_strength"].get("benchmark", "SPY"),
                rs_lookback_days=20,
                rs_vs_benchmark=None,
                rs_vs_sector=None,
                options_stance=stance,
            )
            row = asdict(dec)
            write_csv_row(LOG_CSV, row)
            log_to_gsheets(row, cfg)
            st.success("Logged.")

            # Flip alerts: compare last action for ticker
            state = read_state_cache()
            prev = state[state["ticker"] == ticker]
            last_action = prev.iloc[-1]["last_action"] if not prev.empty else None
            if last_action in ("STAY_OUT", "WAIT") and action == "GET_BACK_IN":
                send_alert(f"{ticker}: flipped to GET BACK IN — {why}", cfg)

            # update cache
            if prev.empty:
                state = pd.concat(
                    [state, pd.DataFrame({"ticker": [ticker], "last_action": [action]})],
                    ignore_index=True
                )
            else:
                state.loc[state["ticker"] == ticker, "last_action"] = action
            write_state_cache(state)

        cexp1, cexp2 = st.columns(2)

        # ---- Export PDF (guarded if fpdf2 missing) ----
        with cexp1:
            if st.button("Export PDF"):
                dec = Decision(
                    timestamp=dt.datetime.now().isoformat(timespec='seconds'),
                    ticker=ticker,
                    action=action,
                    rationale=rationale_text,
                    entry=entry,
                    stop=stop,
                    target=target,
                    reward_risk=float(computed_rr) if computed_rr is not None else None,
                    days_to_earnings=int(dte) if dte is not None else None,
                    exit_triggers=int(exit_count),
                    reentry_triggers=int(re_count),
                    breadth_mode=breadth_mode,
                    breadth_value=float(breadth_val) if breadth_val is not None else None,
                    sector_etf=cfg["relative_strength"].get("sector_etf", ""),
                    rs_benchmark=cfg["relative_strength"].get("benchmark", "SPY"),
                    rs_lookback_days=20,
                    rs_vs_benchmark=None,
                    rs_vs_sector=None,
                    options_stance=stance,
                )
                pdf_bytes = export_pdf(dec, cfg)
                if pdf_bytes is None:
                    st.warning(
                        "PDF export requires the package **fpdf2**. "
                        "Add `fpdf2>=2.7.9` to requirements.txt and redeploy."
                    )
                else:
                    st.download_button(
                        "Download PDF",
                        data=pdf_bytes,
                        file_name=f"{ticker}_decision.pdf",
                        mime="application/pdf"
                    )

        with cexp2:
            if st.button("Export CSV Row"):
                # dumps the most recent decision row for convenience
                try:
                    df = pd.read_csv(LOG_CSV)
                    last = df.tail(1)
                    csv = last.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "Download Last Row",
                        data=csv,
                        file_name="last_decision.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.warning(f"No rows yet: {e}")

        st.markdown("---")
        st.subheader("Watchlist Loop")
        watch_text = st.text_area("Tickers (comma/space separated)", value="SPY, QQQ, IWM")
        if st.button("Scan Watchlist"):
            toks = [
                t.strip().upper()
                for t in watch_text.replace("\n", " ").replace(",", " ").split(" ")
                if t.strip()
            ]
            rows = []
            for tk in toks:
                try:
                    rs_bmk, rs_sec = relative_strength(
                        tk,
                        cfg["relative_strength"]["benchmark"],
                        cfg["relative_strength"].get("sector_etf", ""),
                        20
                    )
                    dte_i = next_earnings_days(tk)
                    rows.append({
                        "ticker": tk,
                        "dte": dte_i,
                        "rs_vs_benchmark_pct": None if rs_bmk is None else round(rs_bmk * 100, 2),
                        "rs_vs_sector_pct": None if rs_sec is None else round(rs_sec * 100, 2),
                    })
                except Exception:
                    rows.append({
                        "ticker": tk,
                        "dte": None,
                        "rs_vs_benchmark_pct": None,
                        "rs_vs_sector_pct": None
                    })
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True)

    with tabs[1]:
        _reentry_tracker_tab()
