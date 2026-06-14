"""
PortfolioOS - Railway Production Server
Serves both the API and the HTML frontend
Run: python railway_server.py
"""

import http.server
import json
import threading
import time
import random
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
    print("✓ yfinance found - REAL NSE prices")
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠ Using simulated prices")

NIFTY50 = [
    "RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","HINDUNILVR","ITC",
    "SBIN","BHARTIARTL","KOTAKBANK","LT","HCLTECH","AXISBANK","ASIANPAINT",
    "MARUTI","SUNPHARMA","TITAN","ULTRACEMCO","BAJFINANCE","WIPRO",
    "NESTLEIND","TECHM","POWERGRID","NTPC","JSWSTEEL","TATAMOTORS",
    "TATASTEEL","ADANIENT","ADANIPORTS","BAJAJFINSV","DRREDDY","CIPLA",
    "EICHERMOT","BRITANNIA","DIVISLAB","HEROMOTOCO","HINDALCO","INDUSINDBK",
    "ONGC","SBILIFE","TATACONSUM","COALINDIA","APOLLOHOSP","BPCL",
    "GRASIM","HDFCLIFE","UPL","VEDL","HAL","M&M"
]

NIFTY500_EXTRA = [
    "PERSISTENT","LTTS","MPHASIS","COFORGE","KPITTECH","TATAELXSI",
    "ZOMATO","IRCTC","BANDHANBNK","FEDERALBNK","IDFCFIRSTB","AUBANK",
    "CHOLAFIN","MUTHOOTFIN","RECLTD","PFC","IRFC","ABCAPITAL",
    "AUROPHARMA","ALKEM","TORNTPHARM","LAURUSLABS","MAXHEALTH","FORTIS",
    "TVSMOTOR","ASHOKLEY","BHARATFORG","APOLLOTYRE","BALKRISHNA",
    "DABUR","MARICO","EMAMILTD","GODREJCP","VBL","JUBLFOOD",
    "DLF","GODREJPROP","OBEROIRLTY","PRESTIGE","BRIGADE","LODHA",
    "SIEMENS","ABB","THERMAX","CUMMINSIND","BEL","BEML",
    "PIIND","FINEORG","DEEPAKNTR","ATUL","GALAXYSURF","PIDILITIND",
    "RVNL","IRCON","NBCC","HUDCO","MAZAGON","GRSE","COCHINSHIP",
    "HINDZINC","NMDC","SAIL","APLAPOLLO","RATNAMANI",
    "DATAMATICS","HAPPSTMNDS","TANLA","LATENTVIEW","INTELLECT",
    "JKCEMENT","RAMCOCEM","DALMIABL","SURYAROSNI","ASTRAL",
    "POLYCAB","HAVELLS","CROMPTON","KEI","JSWENERGY","ADANIGREEN",
]

ALL_SYMBOLS = list(dict.fromkeys(NIFTY50 + NIFTY500_EXTRA))

PRICES = {
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
    "HAL":4567.80,"M&M":3234.50,"PERSISTENT":6789.40,"LTTS":5678.90,
    "MPHASIS":3456.70,"COFORGE":8901.20,"KPITTECH":1789.30,"TATAELXSI":7890.10,
    "ZOMATO":267.80,"IRCTC":987.65,"BANDHANBNK":234.50,"FEDERALBNK":189.70,
    "IDFCFIRSTB":89.70,"AUBANK":789.60,"CHOLAFIN":1456.70,"MUTHOOTFIN":2345.60,
    "RECLTD":567.80,"PFC":489.70,"IRFC":234.50,"ABCAPITAL":234.55,
    "AUROPHARMA":1234.50,"ALKEM":5678.90,"TORNTPHARM":3456.70,"LAURUSLABS":456.70,
    "MAXHEALTH":1023.40,"FORTIS":567.80,"TVSMOTOR":2345.60,"ASHOKLEY":234.50,
    "BHARATFORG":1456.70,"APOLLOTYRE":567.80,"BALKRISHNA":3234.50,
    "DABUR":623.40,"MARICO":678.90,"EMAMILTD":789.60,"GODREJCP":1456.70,
    "VBL":1234.50,"JUBLFOOD":678.90,"DLF":934.50,"GODREJPROP":3456.70,
    "OBEROIRLTY":2345.60,"PRESTIGE":2123.40,"BRIGADE":1456.70,"LODHA":1567.80,
    "SIEMENS":7890.10,"ABB":6789.40,"THERMAX":4567.80,"CUMMINSIND":3456.70,
    "BEL":289.70,"BEML":4567.80,"PIIND":4234.55,"FINEORG":6234.80,
    "DEEPAKNTR":2890.10,"ATUL":8901.20,"GALAXYSURF":3456.40,"PIDILITIND":3456.70,
    "RVNL":489.70,"IRCON":345.60,"NBCC":189.70,"HUDCO":234.50,
    "MAZAGON":4567.80,"GRSE":2345.60,"COCHINSHIP":2123.40,"HINDZINC":456.70,
    "NMDC":234.50,"SAIL":145.60,"APLAPOLLO":1678.90,"RATNAMANI":3456.70,
    "DATAMATICS":778.40,"HAPPSTMNDS":890.10,"TANLA":1234.50,"LATENTVIEW":678.90,
    "INTELLECT":1023.40,"JKCEMENT":4567.80,"RAMCOCEM":1023.40,"DALMIABL":2345.60,
    "SURYAROSNI":567.90,"ASTRAL":2145.60,"POLYCAB":7890.10,"HAVELLS":1890.10,
    "CROMPTON":456.80,"KEI":4567.80,"JSWENERGY":567.80,"ADANIGREEN":2345.60,
}

for sym in ALL_SYMBOLS:
    if sym not in PRICES:
        PRICES[sym] = round(random.uniform(100, 3000), 2)

def fetch_prices():
    while True:
        if YFINANCE_AVAILABLE:
            for sym in ALL_SYMBOLS:
                try:
                    clean = sym.replace("&","")
                    t = yf.Ticker(f"{clean}.NS")
                    ltp = t.fast_info["lastPrice"]
                    if ltp and ltp > 0:
                        PRICES[sym] = round(float(ltp), 2)
                except:
                    pass
            print(f"✓ Prices updated {time.strftime('%H:%M:%S')}")
        else:
            for sym in PRICES:
                PRICES[sym] = round(PRICES[sym] * (1 + random.uniform(-0.002, 0.002)), 2)
        time.sleep(60)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, content):
        body = content if isinstance(content, bytes) else content.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/" or path == "/index.html":
            # Serve the HTML dashboard
            html_path = os.path.join(os.path.dirname(__file__), "portfolio_management_system.html")
            if os.path.exists(html_path):
                with open(html_path, "rb") as f:
                    self.send_html(f.read())
            else:
                self.send_html(b"<h1>portfolio_management_system.html not found</h1>")

        elif path == "/health":
            self.send_json({"status":"ok","source":"yfinance","symbols":len(ALL_SYMBOLS)})

        elif path.startswith("/api/market/ltp/"):
            sym = path.split("/")[-1].upper()
            ltp = PRICES.get(sym)
            if ltp:
                self.send_json({"symbol":sym,"ltp":ltp})
            else:
                self.send_json({"error":"Not found"},404)

        elif path == "/api/market/all":
            self.send_json({"prices":PRICES,"total":len(PRICES),"updated":time.strftime("%H:%M:%S")})

        elif path == "/api/market/indices":
            self.send_json({
                "NIFTY50":{"ltp":24500.0,"change_pct":round(random.uniform(-0.8,0.8),2)},
                "SENSEX":{"ltp":80500.0,"change_pct":round(random.uniform(-0.8,0.8),2)},
                "NIFTYBANK":{"ltp":52300.0,"change_pct":round(random.uniform(-0.8,0.8),2)},
            })

        elif "q=" in self.path and "/api/market/search" in self.path:
            q = self.path.split("q=")[-1].upper()
            results = [{"symbol":s,"ltp":PRICES.get(s,0)} for s in ALL_SYMBOLS if q in s]
            self.send_json({"results":results[:20]})

        else:
            self.send_json({"error":"Not found"},404)

    def do_POST(self):
        self.send_json({"message":"OK"})

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    print(f"\n{'='*50}")
    print(f"  PortfolioOS — {len(ALL_SYMBOLS)} NSE Stocks")
    print(f"  Running on port {PORT}")
    print(f"{'='*50}\n")
    t = threading.Thread(target=fetch_prices, daemon=True)
    t.start()
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"✓ Open: http://localhost:{PORT}")
    print("Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopped.")
