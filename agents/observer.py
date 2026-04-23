import requests
import time
import json
import psutil
from datetime import datetime

SERVICES = {
    "order-service": "http://localhost:5001",
    "payment-service": "http://localhost:5002",
    "inventory-service": "http://localhost:5003"
}

def check_service_health(name, base_url):
    """Check if a service is healthy"""
    try:
        start = time.time()
        response = requests.get(f"{base_url}/health", timeout=5)
        response_time = (time.time() - start) * 1000  # ms

        data = response.json()
        is_healthy = response.status_code == 200

        return {
            "service": name,
            "healthy": is_healthy,
            "status_code": response.status_code,
            "response_time_ms": round(response_time, 2),
            "details": data,
            "timestamp": datetime.now().isoformat()
        }

    except requests.exceptions.ConnectionError:
        return {
            "service": name,
            "healthy": False,
            "status_code": None,
            "response_time_ms": None,
            "details": {"error": "Service unreachable - connection refused"},
            "timestamp": datetime.now().isoformat()
        }
    except requests.exceptions.Timeout:
        return {
            "service": name,
            "healthy": False,
            "status_code": None,
            "response_time_ms": 5000,
            "details": {"error": "Service timeout - took more than 5 seconds"},
            "timestamp": datetime.now().isoformat()
        }

def get_service_metrics(name, base_url):
    """Get real CPU and memory metrics from service"""
    try:
        response = requests.get(f"{base_url}/metrics", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_system_metrics():
    """Get real system-level metrics"""
    return {
        "system_cpu": psutil.cpu_percent(interval=1),
        "system_memory": psutil.virtual_memory().percent,
        "system_memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
        "disk_usage": psutil.disk_usage('/').percent if hasattr(psutil.disk_usage('/'), 'percent') else 0
    }

def observe_all():
    """Main observation loop - checks all services"""
    print("\n" + "="*60)
    print(f"👁️  OBSERVER AGENT - {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)

    results = []
    issues_found = []

    for name, url in SERVICES.items():
        health = check_service_health(name, url)
        metrics = get_service_metrics(name, url)
        
        # Combine health + metrics
        if metrics:
            health['cpu'] = metrics.get('cpu_percent', 'N/A')
            health['memory'] = metrics.get('memory_percent', 'N/A')
            health['chaos_mode'] = metrics.get('chaos_mode', False)
        
        results.append(health)

        # Print status
        status_icon = "✅" if health['healthy'] else "❌"
        print(f"\n{status_icon} {name.upper()}")
        print(f"   Status     : {'HEALTHY' if health['healthy'] else 'UNHEALTHY'}")
        print(f"   Response   : {health['response_time_ms']}ms")
        if metrics:
            print(f"   CPU        : {health.get('cpu', 'N/A')}%")
            print(f"   Memory     : {health.get('memory', 'N/A')}%")
        if not health['healthy']:
            error = health['details'].get('error', 'Unknown error')
            print(f"   ⚠️  Error   : {error}")
            issues_found.append({
                "service": name,
                "error": error,
                "response_time": health['response_time_ms'],
                "timestamp": health['timestamp']
            })

    # System metrics
    sys_metrics = get_system_metrics()
    print(f"\n💻 SYSTEM METRICS")
    print(f"   CPU Usage  : {sys_metrics['system_cpu']}%")
    print(f"   Memory     : {sys_metrics['system_memory']}%")
    print(f"   Free RAM   : {sys_metrics['system_memory_available_gb']} GB")

    # Summary
    healthy_count = sum(1 for r in results if r['healthy'])
    print(f"\n📊 SUMMARY: {healthy_count}/{len(SERVICES)} services healthy")

    if issues_found:
        print(f"\n🚨 {len(issues_found)} ISSUE(S) DETECTED - Alerting ReAct Agent...")

    print("="*60)

    return {
        "services": results,
        "issues": issues_found,
        "system_metrics": sys_metrics,
        "timestamp": datetime.now().isoformat(),
        "healthy_count": healthy_count,
        "total_count": len(SERVICES)
    }

def run_observer(interval=10):
    """Run observer continuously"""
    print("🚀 AgentSentinel Observer Agent Starting...")
    print(f"📡 Monitoring {len(SERVICES)} services every {interval} seconds\n")
    
    while True:
        try:
            report = observe_all()
            
            # Save report to file so other agents can read it
            with open('agents/latest_report.json', 'w') as f:
                json.dump(report, f, indent=2)
                
        except KeyboardInterrupt:
            print("\n⛔ Observer Agent stopped by user")
            break
        except Exception as e:
            print(f"❌ Observer error: {e}")
        
        time.sleep(interval)

if __name__ == '__main__':
    run_observer(interval=10)