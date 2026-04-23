from flask import Flask, jsonify, request
import random
import time
import os
import psutil

app = Flask(__name__)

CHAOS_MODE = False

# Real inventory data
inventory = {
    "laptop": {"stock": 50, "reserved": 5, "price": 1200},
    "phone": {"stock": 100, "reserved": 20, "price": 800},
    "tablet": {"stock": 30, "reserved": 8, "price": 500},
    "headphones": {"stock": 75, "reserved": 10, "price": 150},
    "charger": {"stock": 200, "reserved": 30, "price": 30},
}

@app.route('/health')
def health():
    if CHAOS_MODE:
        return jsonify({
            "status": "unhealthy",
            "service": "inventory-service",
            "error": "Stock database corrupted"
        }), 500
    return jsonify({
        "status": "healthy",
        "service": "inventory-service",
        "total_products": len(inventory),
        "uptime": time.time()
    }), 200

@app.route('/inventory', methods=['GET'])
def get_inventory():
    if CHAOS_MODE:
        return jsonify({"error": "Inventory database unreachable"}), 503
    return jsonify({"inventory": inventory, "total_products": len(inventory)}), 200

@app.route('/inventory/<product>', methods=['GET'])
def get_product(product):
    if CHAOS_MODE:
        return jsonify({"error": "Service unavailable"}), 503
    if product not in inventory:
        return jsonify({"error": f"Product '{product}' not found"}), 404
    return jsonify({"product": product, "details": inventory[product]}), 200

@app.route('/inventory/reserve', methods=['POST'])
def reserve_stock():
    if CHAOS_MODE:
        return jsonify({"error": "Cannot reserve - service down"}), 500
    
    data = request.json or {}
    product = data.get('product')
    quantity = data.get('quantity', 1)
    
    if product not in inventory:
        return jsonify({"error": "Product not found"}), 404
    
    available = inventory[product]['stock'] - inventory[product]['reserved']
    if available < quantity:
        return jsonify({"error": "Insufficient stock", "available": available}), 400
    
    inventory[product]['reserved'] += quantity
    return jsonify({
        "status": "reserved",
        "product": product,
        "quantity": quantity,
        "remaining": available - quantity
    }), 200

@app.route('/chaos/enable', methods=['POST'])
def enable_chaos():
    global CHAOS_MODE
    CHAOS_MODE = True
    return jsonify({"chaos": "enabled", "service": "inventory-service"}), 200

@app.route('/chaos/disable', methods=['POST'])
def disable_chaos():
    global CHAOS_MODE
    CHAOS_MODE = False
    return jsonify({"chaos": "disabled", "service": "inventory-service"}), 200

@app.route('/metrics')
def metrics():
    return jsonify({
        "service": "inventory-service",
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "chaos_mode": CHAOS_MODE,
        "total_products": len(inventory),
        "healthy": not CHAOS_MODE
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    print(f"📦 Inventory Service starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)