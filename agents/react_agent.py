import google.generativeai as genai
import json
import requests
import time
from datetime import datetime

GEMINI_API_KEY = "GEMINI_API_KEY"

SERVICES = {
    "order-service": "http://localhost:5001",
    "payment-service": "http://localhost:5002",
    "inventory-service": "http://localhost:5003"
}

genai.configure(api_key=GEMINI_API_KEY)

def get_latest_report():
    try:
        with open('agents/latest_report.json', 'r') as f:
            return json.load(f)
    except:
        return None

def analyze_with_gemini(report):
    issues = report.get('issues', [])
    services = report.get('services', [])
    sys_metrics = report.get('system_metrics', {})

    if not issues:
        return None

    prompt = f"""
You are the ReAct Agent in AgentSentinel — an autonomous root cause analysis system.

CURRENT SYSTEM STATE:
- Timestamp: {report['timestamp']}
- Healthy Services: {report['healthy_count']}/{report['total_count']}
- System CPU: {sys_metrics.get('system_cpu')}%
- System Memory: {sys_metrics.get('system_memory')}%

DETECTED ISSUES:
{json.dumps(issues, indent=2)}

ALL SERVICES STATUS:
{json.dumps(services, indent=2)}

Using ReAct reasoning (Reasoning + Acting), analyze this situation step by step:
1. What exactly is wrong?
2. What is the root cause?
3. Is this cascading or isolated?
4. Severity? (LOW/MEDIUM/HIGH/CRITICAL)
5. What repair action is needed?

Respond ONLY in this exact JSON format, nothing else:
{{
    "reasoning": "Your step by step analysis here",
    "root_cause": "The specific root cause",
    "severity": "LOW/MEDIUM/HIGH/CRITICAL",
    "affected_services": ["service1"],
    "cascading_failure": false,
    "repair_actions": [
        {{
            "service": "service-name",
            "action": "disable_chaos",
            "reason": "why this action"
        }}
    ],
    "confidence": 0.95
}}
"""

    print("\n🧠 REACT AGENT - Analyzing with Gemini AI...")
    print(f"   Issues detected: {len(issues)}")
    print("   Sending to Gemini for root cause analysis...")

    model = genai.GenerativeModel("GPT-5.4")
    response = model.generate_content(prompt)
    raw_response = response.text

    try:
        start = raw_response.find('{')
        end = raw_response.rfind('}') + 1
        json_str = raw_response[start:end]
        analysis = json.loads(json_str)
        return analysis
    except:
        return {"reasoning": raw_response, "repair_actions": [], "severity": "UNKNOWN"}

def print_analysis(analysis):
    print("\n" + "="*60)
    print("🧠 GEMINI AI ROOT CAUSE ANALYSIS")
    print("="*60)
    print(f"\n📋 REASONING:\n{analysis.get('reasoning', 'N/A')}")
    print(f"\n🎯 ROOT CAUSE: {analysis.get('root_cause', 'N/A')}")
    print(f"⚡ SEVERITY: {analysis.get('severity', 'N/A')}")
    print(f"🔗 CASCADING FAILURE: {analysis.get('cascading_failure', False)}")
    print(f"🎲 CONFIDENCE: {analysis.get('confidence', 0) * 100:.0f}%")

    actions = analysis.get('repair_actions', [])
    if actions:
        print(f"\n🔧 RECOMMENDED REPAIR ACTIONS:")
        for i, action in enumerate(actions, 1):
            print(f"   {i}. {action['service']} → {action['action']}")
            print(f"      Reason: {action['reason']}")
    print("="*60)

def run_react_agent(interval=15):
    print("🚀 AgentSentinel ReAct Agent Starting...")
    print("🧠 Powered by Gemini AI\n")

    last_analyzed = None

    while True:
        try:
            report = get_latest_report()

            if not report:
                print("⏳ Waiting for Observer Agent report...")
                time.sleep(interval)
                continue

            current_timestamp = report.get('timestamp')
            issues = report.get('issues', [])

            if issues and current_timestamp != last_analyzed:
                analysis = analyze_with_gemini(report)

                if analysis:
                    print_analysis(analysis)
                    last_analyzed = current_timestamp

                    with open('agents/latest_analysis.json', 'w') as f:
                        json.dump(analysis, f, indent=2)

                    print("\n✅ Analysis saved → Repair Agent will now act!")
            else:
                print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] All services healthy - No action needed")

        except KeyboardInterrupt:
            print("\n⛔ ReAct Agent stopped")
            break
        except Exception as e:
            print(f"❌ ReAct Agent error: {e}")

        time.sleep(interval)

if __name__ == '__main__':
    run_react_agent(interval=15)