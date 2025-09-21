def render_chart(symbol: str,
                 interval: str='D',
                 theme: str='dark',
                 height: int=600,
                 overlays=None,
                 mode: str='tvjs'):
    import json
    from streamlit.components.v1 import html

    if not symbol:
        st.warning("No symbol provided.")
        return

    use_iframe = (str(mode).lower() == "iframe")
    if use_iframe:
        url = _cachebust_url(tv_embed_url(symbol, interval=interval, theme=theme))
        html(f'<iframe src="{url}" height="{height}" width="100%" frameborder="0" style="border:0;" scrolling="yes"></iframe>', height=height)
        render_refresh_bar("Refresh after TradingView sign-in")
        return

    # Minimal cfg: do NOT preload studies here (some widget builds ignore colors/panes).
    cfg = {
        "container_id": "tv_chart",
        "symbol": symbol,
        "interval": interval,
        "theme": theme,
        "style": 3,                 # Heikin-Ashi
        "autosize": True,
        "timezone": "Etc/UTC",
        "locale": "en",
        "withdateranges": True,
        "allow_symbol_change": True,
        "details": True,
        "calendar": True,
        "studies": [],              # we will add studies programmatically below
        "overrides": {
            "paneProperties.legendProperties.showStudyTitles": True,
            "paneProperties.legendProperties.showStudyValues": True,
            "paneProperties.legendProperties.showSeriesOHLC": False,
        },
    }

    # Create the widget, then add all studies with inputs + colors via createStudy().
    # This path reliably applies colors and puts indicators in their own panes.
    html(
        """
        <div id="tv_chart" style="height:%(H)spx;"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
        (function(){
          const cfg = %(CFG)s;
          window.vegaTV = new TradingView.widget(cfg);

          function addStudies(){
            if (!window.vegaTV || !window.vegaTV.onChartReady) return;
            window.vegaTV.onChartReady(function(){
              const c = window.vegaTV.chart();
              const add = (name, inputs, styles, overlay) => {
                try {
                  c.createStudy(name, !!overlay, false, inputs || [], null, styles || {});
                } catch (e) { /* ignore */ }
              };

              // ----- PRICE PANE -----
              // EMAs with exact colors/widths
              add('Moving Average Exponential', [9],   {'Plot.color':'#1e90ff','Plot.linewidth':2,'plot.color':'#1e90ff','plot.linewidth':2},  true);
              add('Moving Average Exponential', [21],  {'Plot.color':'#001f5b','Plot.linewidth':2,'plot.color':'#001f5b','plot.linewidth':2}, true);
              add('Moving Average Exponential', [50],  {'Plot.color':'#ff0000','Plot.linewidth':2,'plot.color':'#ff0000','plot.linewidth':2}, true);
              add('Moving Average Exponential', [200], {'Plot.color':'#ffffff','Plot.linewidth':2,'plot.color':'#ffffff','plot.linewidth':2}, true);

              // Bollinger Bands (20,2) + Ichimoku (9/26/52, +26)
              add('Bollinger Bands', [20, 2], null, true);
              add('Ichimoku Cloud', [9, 26, 52, 26], null, true);

              // ----- SEPARATE PANES -----
              add('MACD', [12, 26, 9], null, false);
              add('Relative Strength Index', [14], null, false);
              add('On Balance Volume', [], null, false);
              add('Average True Range', [14], null, false);
            });
          }

          // Add on first load
          addStudies();

          // Instant symbol switch support (from cockpit tiles)
          window.addEventListener("message", function(e){
            try {
              var d = e.data || {};
              if (d && d.type === "VEGA_SET_SYMBOL" && window.vegaTV && window.vegaTV.onChartReady) {
                window.vegaTV.onChartReady(function(){
                  var sym = d.symbol || "%(SYM)s";
                  var ivl = d.interval || "%(IVL)s";
                  window.vegaTV.chart().setSymbol(sym, ivl);
                  // re-add studies for the new symbol to guarantee panes/colors
                  setTimeout(addStudies, 250);
                });
              }
            } catch(err) {}
          }, false);
        })();
        </script>
        """ % {
            "H": height,
            "CFG": json.dumps(cfg),
            "SYM": symbol,
            "IVL": interval
        },
        height=height
    )
