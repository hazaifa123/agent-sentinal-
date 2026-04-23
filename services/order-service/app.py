from flask import Flask, jsonify
import random
import time
import os

app = Flask(__name__)

# Simulate service health - can be made unhealthy
SERVICE_HEALTHY = True
CHAOS_MODE = False  # When True, service starts failing

@app.route('/health')
def health():
    """Observer Agent checks this endpoint"""
    if not SERVICE_HEALTHY or CHAOS_MODE:
        return jsonify({
            "status": "unhealthy",
            "service": "order-service",
            "error": "Database connection failed"
        }), 500
    return jsonify({
        "status": "healthy",
        "service": "order-service",
        "uptime": time.time()
    }), 200

@app.route('/orders', methods=['GET'])
def get_orders():
    """Main business endpoint"""
    if CHAOS_MODE:
        time.sleep(5)  # Simulate latency spike
        return jsonify({"error": "Service overloaded"}), 503
    
    orders = [
        {"id": 1, "product": "Laptop", "status": "processing", "amount": 1200},
        {"id": 2, "product": "Phone", "status": "shipped", "amount": 800},
        {"id": 3, "product": "Tablet", "status": "delivered", "amount": 500},
    ]
    return jsonify({"orders": orders, "count": len(orders)}), 200

@app.route('/orders/create', methods=['POST'])
def create_order():
    """Create new order"""
    if CHAOS_MODE:
        return jsonify({"error": "Cannot process orders - service down"}), 500
    
    order_id = random.randint(1000, 9999)
    return jsonify({
        "order_id": order_id,
        "status": "created",
        "message": "Order successfully created"
    }), 201

@app.route('/chaos/enable', methods=['POST'])
def enable_chaos():
    """Observer Agent triggers chaos to test system"""
    global CHAOS_MODE
    CHAOS_MODE = True
    return jsonify({"chaos": "enabled", "service": "order-service"}), 200

@app.route('/chaos/disable', methods=['POST'])
def disable_chaos():
    """Repair Agent calls this to fix the service"""
    global CHAOS_MODE
    CHAOS_MODE = False
    return jsonify({"chaos": "disabled", "service": "order-service"}), 200

@app.route('/metrics')
def metrics():
    """Real system metrics - Observer Agent collects these"""
    import psutil
    return jsonify({
        "service": "order-service",
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "chaos_mode": CHAOS_MODE,
        "healthy": not CHAOS_MODE
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"🛒 Order Service starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)