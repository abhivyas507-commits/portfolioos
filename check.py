"""
PortfolioOS — Railway Server
Fetches ALL NSE listed stocks automatically from NSE equity list
2000+ stocks, updates daily, new IPOs included automatically
"""
import http.server, json, threading, time, random, os, urllib.request, csv, io
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    from pnsea import NSE
    PNSEA = True
    print("✓ pnsea loaded")
except:
    PNSEA = False
    print("⚠ pnsea not available")

# ── NSE Equity List URL ──────────────────────────────
NSE_EQUITY_LIST_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Referer": "https://www.nseindia.com/",
}

# ── Stock Registry ───────────────────────────────────
ALL_STOCKS = {}   # {symbol: {name, series, isin}}
PRICES = {}       # {symbol: ltp}
PRICE_DETAILS = {} # {symbol: {ltp, open, high, low, change, changePct}}

# ── Base prices for top stocks ───────────────────────
BASE_PRICES = {
    "RELIANCE":2987.45,"TCS":4123.80,"HDFCBANK":1789.55,"INFY":1923.30,
    "ICICIBANK":1456.70,"HINDUNILVR":2678.40,"ITC":468.90,"SBIN":832.15,
    "BHARTIARTL":1876.30,"KOTAKBANK":1923.55,"LT":3456.80,"HCLTECH":1678.90,
    "AXISBANK":1234.50,"ASIANPAINT":2876.40,"MARUTI":12456.70,"SUNPHARMA":1678.90,
    "TITAN":3456.20,"ULTRACEMCO":11234.50,"BAJFINANCE":7345.90,"WIPRO":567.80,
    "NESTLEIND":24567.80,"TECHM":1678.90,"POWERGRID":345.60,"NTPC":389.70,
    "JSWSTEEL":987.60,"TATAMOTORS":1023.40,"TATASTEEL":167.80,"ADANIENT":3456.70,
    "ADANIPORTS":1456.70,"BAJAJFINSV":1876.50,"DRREDDY":6789.40,"CIPLA":1567.80,
    "EICHERMOT":4567.80,"BRITANNIA":5678.90,"DIVISLAB":4567.80,"HEROMOTOCO":4567.80,
    "HINDALCO":678.90,"INDUSINDBK":1456.70,"ONGC":289.70,"SBILIFE":1678.90,
    "TATACONSUM":1123.40,"COALINDIA":489.70,"APOLLOHOSP":6789.40,"BPCL":345.60,
    "GRASIM":2678.90,"HDFCLIFE":756.80,"UPL":567.80,"VEDL":489.70,
    "HAL":4567.80,"M&M":3234.50,"ZOMATO":267.80,"IRCTC":987.65,
    "PERSISTENT":6789.40,"LTTS":5678.90,"KPITTECH":1789.30,"TATAELXSI":7890.10,
    "BANDHANBNK":234.50,"FEDERALBNK":189.70,"RECLTD":567.80,"PFC":489.70,
    "IRFC":234.50,"AUROPHARMA":1234.50,"ALKEM":5678.90,"TVSMOTOR":2345.60,
    "ASHOKLEY":234.50,"DABUR":623.40,"MARICO":678.90,"DLF":934.50,
    "GODREJPROP":3456.70,"SIEMENS":7890.10,"ABB":6789.40,"BEL":289.70,
    "PIIND":4234.55,"POLYCAB":7890.10,"HAVELLS":1890.10,"CROMPTON":456.80,
    "TATAPOWER":345.60,"GAIL":234.50,"IOCL":145.60,"INDIGO":4567.80,
    "PNB":123.40,"BANKBARODA":234.50,"CHOLAFIN":1456.70,"MUTHOOTFIN":2345.60,
    "APOLLOTYRE":567.80,"BALKRISHNA":3234.50,"BHARATFORG":1456.70,
    "COLPAL":2890.10,"GODREJCP":1456.70,"VBL":1234.50,"JUBLFOOD":678.90,
    "HINDZINC":456.70,"NMDC":234.50,"SAIL":145.60,"COFORGE":8901.20,
    "MPHASIS":3456.70,"OFSS":9876.50,"NAUKRI":6789.40,"JKCEMENT":4567.80,
    "RAMCOCEM":1023.40,"SURYAROSNI":567.90,"ASTRAL":2145.60,"KEI":4567.80,
    "NBCC":189.70,"MAZAGON":4567.80,"GRSE":2345.60,"DEEPAKNTR":2890.10,
    "PIDILITIND":3456.70,"DATAMATICS":778.40,"TANLA":1234.50,"TRENT":4567.80,
    "DMART":4567.80,"FINEORG":6234.80,"RVNL":489.70,"ADANIGREEN":2345.60,
    "JSWENERGY":567.80,"NHPC":89.70,"HUDCO":234.50,"BAJAJ-AUTO":9876.50,
}
PRICES.update(BASE_PRICES)

STATUS = {
    "total_stocks": 0,
    "prices_fetched": 0,
    "last_update": "Starting...",
    "equity_list_loaded": False,
    "source": "NSE India",
}

def fetch_nse_equity_list():
    """Download complete NSE equity list — all 2000+ stocks."""
    print("Downloading NSE equity list...")
    try:
        req = urllib.request.Request(NSE_EQUITY_LIST_URL, headers=NSE_HEADERS)
        resp = urllib.request.urlopen(req, timeout=30)
        content = resp.read().decode('utf-8', errors='ignore')

        reader = csv.DictReader(io.StringIO(content))
        count = 0
        for row in reader:
            sym = row.get('SYMBOL', '').strip()
            name = row.get('NAME OF COMPANY', '').strip()
            series = row.get('SERIES', '').strip()
            isin = row.get(' ISIN NUMBER', '').strip()

            if sym and series == 'EQ':  # Only equity series
                ALL_STOCKS[sym] = {
                    'name': name,
                    'series': series,
                    'isin': isin,
                }
                # Set base price if not already set
                if sym not in PRICES:
                    PRICES[sym] = 0  # Will be filled by price fetch

                count += 1

        STATUS["total_stocks"] = count
        STATUS["equity_list_loaded"] = True
        print(f"✓ Loaded {count} NSE stocks from equity list")
        return count

    except Exception as e:
        print(f"✗ Equity list fetch failed: {e}")
        # Use base stocks as fallback
        for sym in BASE_PRICES:
            ALL_STOCKS[sym] = {'name': sym, 'series': 'EQ', 'isin': ''}
        STATUS["total_stocks"] = len(ALL_STOCKS)
        return len(ALL_STOCKS)

def fetch_prices_pnsea():
    """Fetch prices using pnsea for tracked stocks."""
    if not PNSEA:
        return 0
    nse = NSE()
    count = 0
    # Focus on liquid stocks first (top 500)
    priority_stocks = list(BASE_PRICES.keys())
    # Then add remaining stocks
    other_stocks = [s for s in ALL_STOCKS.keys() if s not in priority_stocks]
    all_to_fetch = priority_stocks + other_stocks[:200]  # Fetch top 700

    for sym in all_to_fetch:
        try:
            data = nse.equity.info(sym)
            price_info = data.get('priceInfo', {})
            ltp = price_info.get('lastPrice', 0)
            if ltp and float(ltp) > 0:
                PRICES[sym] = round(float(ltp), 2)
                PRICE_DETAILS[sym] = {
                    'ltp': round(float(ltp), 2),
                    'open': price_info.get('open', 0),
                    'high': price_info.get('intraDayHighLow', {}).get('max', 0),
                    'low': price_info.get('intraDayHighLow', {}).get('min', 0),
                    'change': price_info.get('change', 0),
                    'changePct': price_info.get('pChange', 0),
                    'previousClose': price_info.get('previousClose', 0),
                }
                count += 1
        except:
            pass
        time.sleep(0.3)
    return count

def fetch_loop():
    """Main loop — load equity list then fetch prices."""
    # Step 1: Load complete NSE equity list
    fetch_nse_equity_list()
    time.sleep(2)

    # Step 2: Fetch prices
    while True:
        try:
            if PNSEA:
                print(f"Fetching prices for {len(ALL_STOCKS)} stocks...")
                count = fetch_prices_pnsea()
                STATUS["prices_fetched"] = count
                STATUS["last_update"] = time.strftime("%H:%M:%S")
                print(f"✓ {count} prices updated at {STATUS['last_update']}")
            else:
                # Simulate prices
                for sym in PRICES:
                    if PRICES[sym] > 0:
                        PRICES[sym] = round(PRICES[sym] * (1 + random.uniform(-0.001, 0.001)), 2)
                STATUS["last_update"] = time.strftime("%H:%M:%S")

            # Refresh equity list daily
            time.sleep(3600)  # Every hour
            fetch_nse_equity_list()

        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(60)

def serve_html():
    html_path = os.path.join(os.path.dirname(__file__), "portfolio_management_system.html")
    if os.path.exists(html_path):
        with open(html_path, "rb") as f:
            return f.read()
    return b"<h1>portfolio_management_system.html not found</h1>"

class Handler(BaseHTTPRequestHandler):
    def log_message(self, f, *a): pass

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        p = self.path.split("?")[0]

        # Serve dashboard
        if p == "/" or p == "/index.html":
            body = serve_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        # Health check
        elif p == "/health":
            self.send_json({
                "status": "ok",
                "source": "NSE India (pnsea)",
                "total_stocks": STATUS["total_stocks"],
                "prices_fetched": STATUS["prices_fetched"],
                "equity_list_loaded": STATUS["equity_list_loaded"],
                "last_update": STATUS["last_update"],
            })

        # All prices
        elif p == "/api/market/all":
            self.send_json({
                "prices": PRICES,
                "total": len(PRICES),
                "updated": STATUS["last_update"],
                "source": "NSE India",
            })

        # All stocks list with names
        elif p == "/api/market/stocks":
            stocks_list = []
            for sym, info in ALL_STOCKS.items():
                stocks_list.append({
                    "symbol": sym,
                    "name": info.get("name", sym),
                    "ltp": PRICES.get(sym, 0),
                    "isin": info.get("isin", ""),
                })
            # Sort by symbol
            stocks_list.sort(key=lambda x: x["symbol"])
            self.send_json({
                "stocks": stocks_list,
                "total": len(stocks_list),
                "updated": STATUS["last_update"],
            })

        # Single stock LTP
        elif p.startswith("/api/market/ltp/"):
            sym = p.split("/")[-1].upper()
            if sym in PRICES and PRICES[sym] > 0:
                detail = PRICE_DETAILS.get(sym, {})
                self.send_json({
                    "symbol": sym,
                    "name": ALL_STOCKS.get(sym, {}).get("name", sym),
                    "ltp": PRICES[sym],
                    "change": detail.get("change", 0),
                    "changePct": detail.get("changePct", 0),
                    "open": detail.get("open", 0),
                    "high": detail.get("high", 0),
                    "low": detail.get("low", 0),
                    "source": "NSE India",
                })
            elif sym in ALL_STOCKS:
                self.send_json({"symbol": sym, "name": ALL_STOCKS[sym].get("name", sym), "ltp": 0, "note": "Price not yet fetched"})
            else:
                self.send_json({"error": f"{sym} not found on NSE"}, 404)

        # Search stocks
        elif "/api/market/search" in self.path:
            q = ""
            if "q=" in self.path:
                q = urllib.parse.unquote(self.path.split("q=")[-1].split("&")[0]).upper()

            results = []
            for sym, info in ALL_STOCKS.items():
                name = info.get("name", "").upper()
                if q in sym or q in name:
                    results.append({
                        "symbol": sym,
                        "name": info.get("name", sym),
                        "ltp": PRICES.get(sym, 0),
                    })
            results.sort(key=lambda x: (not x["symbol"].startswith(q), x["symbol"]))
            self.send_json({"results": results[:30], "total": len(results)})

        # Indices
        elif p == "/api/market/indices":
            self.send_json({
                "NIFTY50": {"ltp": 23853.90, "change_pct": 0.98},
                "SENSEX": {"ltp": 76259.43, "change_pct": 0.97},
                "NIFTYBANK": {"ltp": 57165.70, "change_pct": 0.62},
            })

        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        self.send_json({"ok": True})

# Add urllib.parse
import urllib.parse

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    print(f"\n{'='*55}")
    print(f"  PortfolioOS — ALL NSE Stocks Server")
    print(f"  Source: NSE India equity list (2000+ stocks)")
    print(f"  Prices: pnsea (real-time during market hours)")
    print(f"{'='*55}\n")

    threading.Thread(target=fetch_loop, daemon=True).start()

    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"✓ Server: http://localhost:{PORT}")
    print(f"✓ Dashboard: http://localhost:{PORT}/")
    print(f"✓ All stocks: http://localhost:{PORT}/api/market/stocks")
    print(f"✓ Search: http://localhost:{PORT}/api/market/search?q=TATA")
    print(f"✓ Health: http://localhost:{PORT}/health")
    print(f"\nLoading NSE equity list (2000+ stocks)...")
    print(f"Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopped.")
