from flask import Flask, render_template, jsonify, request
import trader_core
import json
from datetime import datetime
import threading
import time

app = Flask(__name__)

# نمونه connector برای کل برنامه
connector = trader_core.TripleExchangeConnector()

# کش برای داده‌ها
analysis_cache = {
    'data': None,
    'timestamp': None,
    'last_update': None
}

def update_analysis():
    """به‌روزرسانی تحلیل در پس‌زمینه"""
    while True:
        try:
            print("🔄 در حال به‌روزرسانی تحلیل...")
            all_data = []
            
            for symbol in trader_core.SYMBOLS[:5]:  # فقط ۵ تا برای سرعت
                result = trader_core.analyze_symbol_complete(symbol, connector)
                if result:
                    all_data.append(result)
            
            if all_data:
                # مرتب کردن براساس score
                all_data.sort(key=lambda x: x['score'], reverse=True)
                analysis_cache['data'] = all_data
                analysis_cache['timestamp'] = datetime.now().strftime('%H:%M:%S')
                analysis_cache['last_update'] = datetime.now()
                print(f"✅ تحلیل به‌روز شد: {len(all_data)} ارز")
        
        except Exception as e:
            print(f"خطا در به‌روزرسانی: {e}")
        
        # هر ۶۰ ثانیه یکبار به‌روزرسانی کن
        time.sleep(60)

# شروع thread به‌روزرسانی
update_thread = threading.Thread(target=update_analysis, daemon=True)
update_thread.start()

@app.route('/')
def home():
    """صفحه اصلی - مناسب موبایل"""
    return render_template('index.html')

@app.route('/mobile')
def mobile_dashboard():
    """داشبورد مخصوص موبایل"""
    return '''
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📱 ربات تریدینگ موبایل</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                min-height: 100vh;
            }
            .container { max-width: 100%; }
            .header {
                text-align: center;
                padding: 20px 0;
                margin-bottom: 20px;
            }
            .header h1 {
                font-size: 24px;
                margin-bottom: 10px;
            }
            .status-card {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }
            .symbol-card {
                background: white;
                color: #333;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .symbol-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            .symbol-name { font-weight: bold; font-size: 18px; }
            .symbol-price { font-size: 16px; color: #666; }
            .score-badge {
                padding: 5px 10px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            .score-high { background: #10b981; color: white; }
            .score-medium { background: #f59e0b; color: white; }
            .score-low { background: #ef4444; color: white; }
            .signal {
                padding: 8px 12px;
                border-radius: 8px;
                margin-top: 10px;
                text-align: center;
                font-weight: bold;
            }
            .signal-buy { background: #10b98120; color: #10b981; border: 1px solid #10b981; }
            .signal-sell { background: #ef444420; color: #ef4444; border: 1px solid #ef4444; }
            .signal-neutral { background: #6b728020; color: #6b7280; border: 1px solid #6b7280; }
            .info-row {
                display: flex;
                justify-content: space-between;
                margin: 5px 0;
                font-size: 14px;
            }
            .last-update {
                text-align: center;
                margin-top: 20px;
                font-size: 12px;
                color: rgba(255, 255, 255, 0.7);
            }
            .refresh-btn {
                background: white;
                color: #667eea;
                border: none;
                padding: 12px 20px;
                border-radius: 25px;
                font-size: 16px;
                font-weight: bold;
                width: 100%;
                margin-top: 10px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📱 ربات تریدینگ</h1>
                <p>تحلیل زنده بازار ارز دیجیتال</p>
            </div>
            
            <div class="status-card">
                <h3>📊 وضعیت سیستم</h3>
                <div class="info-row">
                    <span>وضعیت:</span>
                    <span style="color: #10b981;">● فعال</span>
                </div>
                <div class="info-row">
                    <span>تعداد ارزها:</span>
                    <span id="symbol-count">در حال بارگذاری...</span>
                </div>
                <div class="info-row">
                    <span>آخرین به‌روزرسانی:</span>
                    <span id="last-update">--:--:--</span>
                </div>
            </div>
            
            <div id="symbols-container">
                <p style="text-align: center;">در حال بارگذاری داده‌ها...</p>
            </div>
            
            <div class="last-update">
                آخرین به‌روزرسانی: <span id="update-time">--:--:--</span>
            </div>
            
            <button class="refresh-btn" onclick="loadData()">🔄 به‌روزرسانی</button>
        </div>
        
        <script>
            function loadData() {
                fetch('/api/data')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('symbol-count').textContent = data.symbols.length + ' ارز';
                        document.getElementById('last-update').textContent = data.timestamp;
                        document.getElementById('update-time').textContent = data.timestamp;
                        
                        const container = document.getElementById('symbols-container');
                        container.innerHTML = '';
                        
                        data.symbols.forEach(symbol => {
                            const scoreClass = symbol.score >= 70 ? 'score-high' : 
                                             symbol.score >= 40 ? 'score-medium' : 'score-low';
                            
                            const signalClass = symbol.signal.includes('PUMP') ? 'signal-buy' :
                                               symbol.signal.includes('DUMP') ? 'signal-sell' : 'signal-neutral';
                            
                            const card = `
                                <div class="symbol-card">
                                    <div class="symbol-header">
                                        <div>
                                            <div class="symbol-name">${symbol.symbol_clean}</div>
                                            <div class="symbol-price">$${symbol.price.toFixed(4)}</div>
                                        </div>
                                        <div class="score-badge ${scoreClass}">
                                            ${symbol.score} امتیاز
                                        </div>
                                    </div>
                                    
                                    <div class="info-row">
                                        <span>RSI:</span>
                                        <span>${symbol.rsi}</span>
                                    </div>
                                    <div class="info-row">
                                        <span>حجم:</span>
                                        <span>${symbol.volume_signal}</span>
                                    </div>
                                    
                                    <div class="signal ${signalClass}">
                                        ${symbol.signal} - ${symbol.action}
                                    </div>
                                </div>
                            `;
                            container.innerHTML += card;
                        });
                    })
                    .catch(error => {
                        console.error('خطا:', error);
                        document.getElementById('symbols-container').innerHTML = 
                            '<p style="color: #ef4444; text-align: center;">خطا در دریافت داده‌ها</p>';
                    });
            }
            
            // بارگذاری اولیه
            loadData();
            
            // به‌روزرسانی خودکار هر ۳۰ ثانیه
            setInterval(loadData, 30000);
        </script>
    </body>
    </html>
    '''

@app.route('/api/data')
def get_data():
    """API برای دریافت داده‌های تحلیل"""
    if analysis_cache['data']:
        return jsonify({
            'status': 'success',
            'symbols': analysis_cache['data'],
            'timestamp': analysis_cache['timestamp'],
            'count': len(analysis_cache['data']),
            'plotly_available': trader_core.PLOTLY_AVAILABLE
        })
    else:
        return jsonify({
            'status': 'loading',
            'message': 'داده‌ها در حال بارگذاری...',
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })

@app.route('/api/test')
def test():
    """تست اتصال به صرافی‌ها"""
    try:
        result = connector.get_best_price_with_volume("BTCUSDT")
        return jsonify({
            'status': 'success',
            'btc_price': result['price'] if result else 'ناموفق',
            'source': result['source'] if result else 'ناموفق'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/health')
def health():
    """بررسی سلامت سرویس"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'plotly': trader_core.PLOTLY_AVAILABLE,
        'cache_age': analysis_cache['timestamp']
    })

if __name__ == '__main__':
    print("🚀 شروع ربات تریدینگ...")
    print(f"📊 Plotly available: {trader_core.PLOTLY_AVAILABLE}")
    print(f"🔢 تعداد ارزها: {len(trader_core.SYMBOLS)}")
    app.run(host='0.0.0.0', port=5000, debug=False)
