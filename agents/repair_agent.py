import requests
import json
import time
from datetime import datetime

SERVICES = {
    "order-service": "http://localhost:5001",
    "payment-service": "http://localhost:5002",
    "inventory-service": "http://localhost:5003"
}

def get_latest_analysis():
    """Read ReAct Agent's latest analysis"""
    try:
        with open('agents/latest_analysis.json', 'r') as f:
            return json.load(f)
    except:
        return None

def disable_chaos(service_name):
    """Actually fix the service by disabling chaos mode"""
    base_url = SERVICES.get(service_name)
    if not base_url:
        return False, "Service not found"
    
    try:
        response = requests.post(f"{base_url}/chaos/disable", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def verify_service_health(service_name):
    """Verify service is healthy after repair"""
    base_url = SERVICES.get(service_name)
    if not base_url:
        return False
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def execute_repair(analysis):
    """Execute repair actions from ReAct Agent's analysis"""
    
    repair_actions = analysis.get('repair_actions', [])
    severity = analysis.get('severity', 'UNKNOWN')
    root_cause = analysis.get('root_cause', 'Unknown')
    
    if not repair_actions:
        print("⚠️  No repair actions recommended")
        return
    
    print("\n" + "="*60)
    print("🔧 REPAIR AGENT - Executing Fixes")
    print("="*60)
    print(f"⚡ Severity  : {severity}")
    print(f"🎯 Root Cause: {root_cause}")
    print(f"🔧 Actions   : {len(repair_actions)} repair(s) to execute")
    print("="*60)
    
    repair_log = []
    
    for i, action in enumerate(repair_actions, 1):
        service = action.get('service')
        act = action.get('action')
        reason = action.get('reason')
        
        print(f"\n[{i}/{len(repair_actions)}] Repairing: {service}")
        print(f"   Action : {act}")
        print(f"   Reason : {reason}")
        print(f"   Status : Executing...", end=' ', flush=True)
        
        success = False
        message = ""
        
        # Execute the actual repair
        if act == "disable_chaos":
            success, message = disable_chaos(service)
        elif act == "restart":
            # First disable chaos then verify
            success, message = disable_chaos(service)
        elif act == "check_dependencies":
            success, message = disable_chaos(service)
        else:
            success, message = disable_chaos(service)
        
        if success:
            print("✅ DONE")
        else:
            print(f"❌ FAILED - {message}")
        
        # Wait a moment then verify
        time.sleep(2)
        is_healthy = verify_service_health(service)
        
        if is_healthy:
            print(f"   Verify : ✅ {service} is now HEALTHY!")
        else:
            print(f"   Verify : ❌ {service} still unhealthy - may need manual intervention")
        
        repair_log.append({
            "service": service,
            "action": act,
            "success": success,
            "verified_healthy": is_healthy,
            "timestamp": datetime.now().isoformat()
        })
    
    # Final summary
    successful = sum(1 for r in repair_log if r['verified_healthy'])
    print(f"\n{'='*60}")
    print(f"📊 REPAIR SUMMARY")
    print(f"   Total Repairs : {len(repair_log)}")
    print(f"   Successful    : {successful}")
    print(f"   Failed        : {len(repair_log) - successful}")
    
    if successful == len(repair_log):
        print(f"\n🎉 ALL SERVICES RESTORED! System is healthy!")
    else:
        print(f"\n⚠️  Some services need manual attention!")
    
    print("="*60)
    
    # Save repair log
    with open('agents/repair_log.json', 'w') as f:
        json.dump({
            "repair_actions": repair_log,
            "timestamp": datetime.now().isoformat(),
            "all_healthy": successful == len(repair_log)
        }, f, indent=2)

def run_repair_agent(interval=20):
    """Run Repair Agent continuously"""
    print("🚀 AgentSentinel Repair Agent Starting...")
    print("🔧 Waiting for ReAct Agent analysis...\n")
    
    last_repaired = None
    
    while True:
        try:
            analysis = get_latest_analysis()
            
            if not analysis:
                print(f"⏳ [{datetime.now().strftime('%H:%M:%S')}] No analysis yet - waiting...")
                time.sleep(interval)
                continue
            
            repair_actions = analysis.get('repair_actions', [])
            
            # Check if this is a new analysis we haven't acted on
            analysis_str = json.dumps(analysis)
            
            if repair_actions and analysis_str != last_repaired:
                execute_repair(analysis)
                last_repaired = analysis_str
            else:
                print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] System stable - monitoring...")
                
        except KeyboardInterrupt:
            print("\n⛔ Repair Agent stopped")
            break
        except Exception as e:
            print(f"❌ Repair Agent error: {e}")
            
        time.sleep(interval)

if __name__ == '__main__':
    run_repair_agent(interval=20)