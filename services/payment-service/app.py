from flask import Flask, jsonify, request
import random
import time
import os
import psutil

app = Flask(__name__)

SERVICE_HEALTHY = True
CHAOS_MODE = False
failed_transactions = 0
total_transactions = 0

@app.route('/health')
def health():
    """Observer Agent checks this endpoint"""
    global failed_transactions, total_transactions
    
    failure_rate = (failed_transactions / total_transactions * 100) if total_transactions > 0 else 0
    
    if CHAOS_MODE or failure_rate > 50:
        return jsonify({
            "status": "unhealthy",
            "service": "payment-service",
            "error": "High transaction failure rate",
            "failure_rate": f"{failure_rate:.1f}%"
        }), 500
        
    return jsonify({
        "status": "healthy",
        "service": "payment-service",
        "failure_rate": f"{failure_rate:.1f}%",
        "uptime": time.time()
    }), 200

@app.route('/pay', methods=['POST'])
def process_payment():
    """Process a payment"""
    global failed_transactions, total_transactions
    total_transactions += 1
    
    if CHAOS_MODE:
        failed_transactions += 1
        time.sleep(3)  # Latency spike
        return jsonify({
            "status": "failed",
            "error": "Payment gateway timeout",
            "transaction_id": None
        }), 500
    
    # Simulate occasional real failures (10% chance)
    if random.random() < 0.1:
        failed_transactions += 1
        return jsonify({
            "status": "failed",
            "error": "Insufficient funds",
            "transaction_id": None
        }), 402
    
    transaction_id = f"TXN-{random.randint(100000, 999999)}"
    return jsonify({
        "status": "success",
        "transaction_id": transaction_id,
        "amount": request.json.get('amount', 0) if request.json else 0,
        "message": "Payment processed successfully"
    }), 200

@app.route('/transactions', methods=['GET'])
def get_transactions():
    """Get transaction history"""
    if CHAOS_MODE:
        return jsonify({"error": "Database unavailable"}), 503
    
    return jsonify({
        "total": total_transactions,
        "failed": failed_transactions,
        "success": total_transactions - failed_transactions,
        "failure_rate": f"{(failed_transactions/total_transactions*100) if total_transactions > 0 else 0:.1f}%"
    }), 200

@app.route('/chaos/enable', methods=['POST'])
def enable_chaos():
    global CHAOS_MODE
    CHAOS_MODE = True
    return jsonify({"chaos": "enabled", "service": "payment-service"}), 200

@app.route('/chaos/disable', methods=['POST'])
def disable_chaos():
    global CHAOS_MODE, failed_transactions, total_transactions
    CHAOS_MODE = False
    failed_transactions = 0
    total_transactions = 0
    return jsonify({"chaos": "disabled", "service": "payment-service"}), 200

@app.route('/metrics')
def metrics():
    """Real system metrics"""
    return jsonify({
        "service": "payment-service",
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "chaos_mode": CHAOS_MODE,
        "total_transactions": total_transactions,
        "failed_transactions": failed_transactions,
        "healthy": not CHAOS_MODE
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    print(f"💳 Payment Service starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)