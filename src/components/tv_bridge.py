def render_chart(symbol: str, interval: str='D', theme: str='dark', height: int=600, overlays=None, mode: str='tvjs'):
    import json
    from streamlit.components.v1 import html

    if not symbol:
        st.warning("No symbol provided.")
        return

    if mode == 'iframe':
        url = _cachebust_url(tv_embed_url(symbol, interval=interval, theme=theme))
        html(f'<iframe src="{url}" height="{height}" width="100%" frameborder="0" style="border:0;" scrolling="yes"></iframe>', height=height)
        render_refresh_bar("Refresh after TradingView sign-in")
        return

    # Fixed order of studies so colors & panes map 1:1
    studies = [
        # --- EMAs (overlay on price) ---
        {"id": "MAExp@tv-basicstudies", "inputs": {"length": 9}},
        {"id": "MAExp@tv-basicstudies", "inputs": {"length": 21}},
        {"id": "MAExp@tv-basicstudies", "inputs": {"length": 50}},
        {"id": "MAExp@tv-basicstudies", "inputs": {"length": 200}},

        # --- Overlays ---
        {"id": "BollingerBands@tv-basicstudies", "inputs": {"length": 20, "mult": 2}},
        {"id": "IchimokuCloud@tv-basicstudies", "inputs": {"conversion": 9, "base": 26, "span": 52, "displacement": 26}},

        # --- Pane studies (order = top → bottom) ---
        {"id": "MACD@tv-basicstudies", "inputs": {"fastLength": 12, "slowLength": 26, "signalLength": 9}},
        {"id": "RSI@tv-basicstudies", "inputs": {"length": 14}},
        {"id": "OBV@tv-basicstudies", "inputs": {}},
        {"id": "ATR@tv-basicstudies", "inputs": {"length": 14}},
    ]

    # Per-instance color overrides (index = order above)
    studies_overrides = {
        "MAExp@tv-basicstudies.0.plot_0.color": "#1e90ff",  # EMA 9  blue
        "MAExp@tv-basicstudies.0.plot_0.linewidth": 2,
        "MAExp@tv-basicstudies.1.plot_0.color": "#001f5b",  # EMA 21 navy
        "MAExp@tv-basicstudies.1.plot_0.linewidth": 2,
        "MAExp@tv-basicstudies.2.plot_0.color": "#ff0000",  # EMA 50 red
        "MAExp@tv-basicstudies.2.plot_0.linewidth": 2,
        "MAExp@tv-basicstudies.3.plot_0.color": "#ffffff",  # EMA 200 white
        "MAExp@tv-basicstudies.3.plot_0.linewidth": 2,
    }

    cfg = {
        "container_id": "tv_chart",
        "symbol": symbol,
        "interval": interval,
        "theme": theme,
        "style": 3,                       # 3 = Heikin-Ashi
        "autosize": True,
        "timezone": "Etc/UTC",
        "locale": "en",
        "withdateranges": True,
        "allow_symbol_change": True,
        "hide_top_toolbar": False,
        "hide_legend": False,
        "details": True,
        "calendar": True,
        "studies": studies,
        "studies_overrides": studies_overrides,
        # Improve legend readability
        "overrides": {
            "paneProperties.legendProperties.showStudyTitles": True,
            "paneProperties.legendProperties.showStudyValues": True,
            "paneProperties.legendProperties.showSeriesOHLC": False,
        },
        # prevents default blue tint on overlays in light theme
        "custom_css_url": "",
    }

    html(
        '<div id="tv_chart" style="height:%spx;"></div>'
        '<script src="https://s3.tradingview.com/tv.js"></script>'
        '<script>new TradingView.widget(%s);</script>' % (height, json.dumps(cfg)),
        height=height
    )
