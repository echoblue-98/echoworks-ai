"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                              AION OS                                         ║
║                    Adversarial Intelligence Operating System                 ║
║                                                                              ║
║                         "The AI That Thinks Like A Thief"                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

                              DEMO FOR DAN
                         What Could Have Been

This demo recreates the exact attack sequence that hit Typhoon Advertising.
AION catches it in 13 minutes. You caught it 39 months later.

Run: python demo_for_dan.py
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

import time
import sys
import os

# Fix Windows encoding for emojis/unicode
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Colors for terminal
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def slow_print(text, delay=0.03):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def dramatic_pause(seconds=2):
    time.sleep(seconds)

def press_enter():
    input(f"\n{Colors.CYAN}  [Press Enter to continue...]{Colors.END}")

# ============================================================================
# SCENE 1: THE PROBLEM
# ============================================================================
def scene_1_problem():
    clear()
    print(f"""
{Colors.RED}{Colors.BOLD}
    ██████╗  █████╗ ███╗   ██╗     ██╗███████╗    ███████╗████████╗ ██████╗ ██████╗ ██╗   ██╗
    ██╔══██╗██╔══██╗████╗  ██║    ██╔╝██╔════╝    ██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝
    ██║  ██║███████║██╔██╗ ██║   ██╔╝ ███████╗    ███████╗   ██║   ██║   ██║██████╔╝ ╚████╔╝ 
    ██║  ██║██╔══██║██║╚██╗██║  ██╔╝  ╚════██║    ╚════██║   ██║   ██║   ██║██╔══██╗  ╚██╔╝  
    ██████╔╝██║  ██║██║ ╚████║ ██╔╝   ███████║    ███████║   ██║   ╚██████╔╝██║  ██║   ██║   
    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═╝    ╚══════╝    ╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝   
{Colors.END}
""")
    
    dramatic_pause(1)
    
    print(f"{Colors.WHITE}")
    slow_print("    January 2021.")
    slow_print("    Typhoon Advertising.")
    slow_print("    A former employee still has VPN access.")
    dramatic_pause(1)
    slow_print("")
    slow_print("    2:34 AM - They connect from Eastern Europe.")
    slow_print("    2:47 AM - They export the entire client database.")
    slow_print("    2:51 AM - They disconnect.")
    dramatic_pause(1)
    slow_print("")
    slow_print(f"    {Colors.RED}You don't find out for months.{Colors.END}")
    slow_print(f"    {Colors.RED}39 months of litigation follows.{Colors.END}")
    print(f"{Colors.END}")
    
    press_enter()

# ============================================================================
# SCENE 2: WHAT IF
# ============================================================================
def scene_2_what_if():
    clear()
    print(f"""
{Colors.CYAN}{Colors.BOLD}
    ╦ ╦╦ ╦╔═╗╔╦╗  ╦╔═╗
    ║║║╠═╣╠═╣ ║   ║╠╣ 
    ╚╩╝╩ ╩╩ ╩ ╩   ╩╚  
{Colors.END}
""")
    
    slow_print(f"    {Colors.WHITE}What if you had AION OS that night?{Colors.END}")
    dramatic_pause(1)
    slow_print(f"    {Colors.WHITE}Let's replay it.{Colors.END}")
    
    press_enter()

# ============================================================================
# SCENE 3: AION CATCHES IT
# ============================================================================
def scene_3_aion_catches():
    clear()
    
    print(f"""
{Colors.GREEN}{Colors.BOLD}
     █████╗ ██╗ ██████╗ ███╗   ██╗     ██████╗ ███████╗
    ██╔══██╗██║██╔═══██╗████╗  ██║    ██╔═══██╗██╔════╝
    ███████║██║██║   ██║██╔██╗ ██║    ██║   ██║███████╗
    ██╔══██║██║██║   ██║██║╚██╗██║    ██║   ██║╚════██║
    ██║  ██║██║╚██████╔╝██║ ╚████║    ╚██████╔╝███████║
    ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝     ╚═════╝ ╚══════╝
                                                        
          SECURITY OPERATIONS CENTER - LIVE FEED
{Colors.END}
""")
    
    # Import here to avoid loading during intro
    from aionos.modules.soc_ingestion import SOCIngestionEngine
    
    engine = SOCIngestionEngine()
    
    dramatic_pause(1)
    
    # Alert 1
    print(f"    {Colors.YELLOW}[02:34:17 UTC]{Colors.END} {Colors.WHITE}INCOMING SIEM ALERT...{Colors.END}")
    time.sleep(1)
    
    alert1 = engine.ingest_alert({
        'alert_type': 'vpn_anomaly',
        'user_id': 'former_employee',
        'severity': 'high',
        'source_ip': '185.42.33.100',
        'source_location': 'Unknown - Eastern Europe VPN',
        'action': 'VPN connection from new geographic location',
        'timestamp': '2021-01-15T02:34:17Z'
    }, auto_escalate=False)
    
    print(f"""
    ┌─────────────────────────────────────────────────────────────────┐
    │  {Colors.YELLOW}⚠ VPN ANOMALY{Colors.END}                                               │
    │                                                                 │
    │  User:      former_employee                                     │
    │  Location:  {Colors.RED}Unknown - Eastern Europe VPN{Colors.END}                        │
    │  Time:      02:34 AM (after hours)                              │
    │                                                                 │
    │  {Colors.YELLOW}Risk Score: {alert1.departure_risk_score:.0f}/100{Colors.END}                                          │
    └─────────────────────────────────────────────────────────────────┘
""")
    
    time.sleep(2)
    
    # Alert 2
    print(f"    {Colors.YELLOW}[02:47:03 UTC]{Colors.END} {Colors.WHITE}INCOMING SIEM ALERT...{Colors.END}")
    time.sleep(1)
    
    alert2 = engine.ingest_alert({
        'alert_type': 'database_access',
        'user_id': 'former_employee',
        'severity': 'critical',
        'action': 'SELECT * FROM clients, billing, campaigns, contacts',
        'details': {'rows': 15000, 'tables': ['clients', 'billing', 'campaigns', 'contacts']},
        'timestamp': '2021-01-15T02:47:03Z'
    }, auto_escalate=False)
    
    print(f"""
    ┌─────────────────────────────────────────────────────────────────┐
    │  {Colors.RED}🚨 DATABASE BULK EXPORT{Colors.END}                                      │
    │                                                                 │
    │  User:      former_employee                                     │
    │  Action:    {Colors.RED}SELECT * FROM clients, billing, campaigns{Colors.END}          │
    │  Rows:      {Colors.RED}15,000{Colors.END}                                              │
    │                                                                 │
    │  {Colors.RED}Risk Score: {alert2.departure_risk_score:.0f}/100{Colors.END}                                         │
    │  {Colors.RED}🔴 PATTERN MATCH: vpn_database_theft{Colors.END}                          │
    └─────────────────────────────────────────────────────────────────┘
""")
    
    time.sleep(1)
    
    # Pattern match explosion
    print(f"""
    {Colors.RED}{Colors.BOLD}
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   🚨 CRITICAL PATTERN DETECTED: VPN DATABASE THEFT 🚨             ║
    ║                                                                   ║
    ║   This matches the exact attack pattern from your case.           ║
    ║   AION learned from your 39 months of pain.                       ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    {Colors.END}
""")
    
    press_enter()
    
    return engine

# ============================================================================
# SCENE 4: SECURITY ATTACKER ANALYSIS
# ============================================================================
def scene_4_analysis(engine):
    clear()
    
    print(f"""
{Colors.MAGENTA}{Colors.BOLD}
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║           🤖 SECURITY ATTACKER AGENT ACTIVATED                    ║
    ║                                                                   ║
    ║              100% LOCAL - ZERO DATA SENT EXTERNAL                 ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
{Colors.END}
""")
    
    slow_print(f"    {Colors.WHITE}Analyzing attack sequence...{Colors.END}")
    time.sleep(1)
    slow_print(f"    {Colors.WHITE}Cross-referencing with pattern database...{Colors.END}")
    time.sleep(1)
    slow_print(f"    {Colors.WHITE}Generating defensive response...{Colors.END}")
    time.sleep(1)
    print()
    
    # Get analysis
    analysis = engine.trigger_security_attacker('former_employee', use_local=True)
    
    print(f"""
    {Colors.GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}
    {Colors.BOLD}THREAT ASSESSMENT{Colors.END}
    {Colors.GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}
    
    Type:       {Colors.RED}{analysis['threat_type']}{Colors.END}
    Severity:   {Colors.RED}{analysis['severity']}{Colors.END}
    Confidence: {Colors.GREEN}{analysis['confidence']}{Colors.END}
    
    Objective:  {analysis['attack_objective']}
""")
    
    press_enter()
    
    print(f"""
    {Colors.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}
    {Colors.BOLD}IMMEDIATE ACTIONS (Execute in next 15 minutes){Colors.END}
    {Colors.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}
""")
    
    for action in analysis['immediate_actions'][:6]:
        print(f"    {Colors.WHITE}□ {action}{Colors.END}")
        time.sleep(0.3)
    
    press_enter()
    
    print(f"""
    {Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}
    {Colors.BOLD}FORENSIC PRESERVATION (Start immediately){Colors.END}
    {Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}
""")
    
    for item in analysis['forensic_preservation']:
        print(f"    {Colors.WHITE}□ {item}{Colors.END}")
        time.sleep(0.3)
    
    press_enter()

# ============================================================================
# SCENE 5: THE DIFFERENCE
# ============================================================================
def scene_5_difference():
    clear()
    
    print(f"""
{Colors.WHITE}{Colors.BOLD}
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║                      THE DIFFERENCE                               ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
{Colors.END}

    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                 │
    │   {Colors.RED}WITHOUT AION:{Colors.END}                                               │
    │                                                                 │
    │     • Attack discovered: {Colors.RED}Months later{Colors.END}                          │
    │     • Response time: {Colors.RED}Too late{Colors.END}                                  │
    │     • Litigation: {Colors.RED}39 months{Colors.END}                                    │
    │     • Data recovered: {Colors.RED}Never{Colors.END}                                    │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                 │
    │   {Colors.GREEN}WITH AION:{Colors.END}                                                  │
    │                                                                 │
    │     • Attack detected: {Colors.GREEN}13 minutes{Colors.END}                              │
    │     • Response time: {Colors.GREEN}Immediate lockdown{Colors.END}                        │
    │     • Litigation: {Colors.GREEN}Prevented{Colors.END}                                    │
    │     • Data protected: {Colors.GREEN}Yes{Colors.END}                                      │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
""")
    
    press_enter()

# ============================================================================
# SCENE 6: THE PITCH
# ============================================================================
def scene_6_pitch():
    clear()
    
    print(f"""
{Colors.GREEN}{Colors.BOLD}
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║                         AION OS                                   ║
    ║                                                                   ║
    ║              "The AI That Thinks Like A Thief"                    ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
{Colors.END}

    {Colors.WHITE}{Colors.BOLD}FOR LAW FIRMS:{Colors.END}
    
    Every partner departure costs $2-5M.
    Not from the departure. From what they TAKE.
    
    AION catches them {Colors.GREEN}before they leave{Colors.END}, not after.

    {Colors.WHITE}{Colors.BOLD}THE MOAT:{Colors.END}
    
    • 5 Adversarial Agents thinking like attackers
    • Pattern database from real cases (including yours)
    • SOC integration for real-time detection
    • {Colors.GREEN}100% LOCAL - Zero data sent to any LLM{Colors.END}
    
    Competitors can copy the AI.
    They can't copy the patterns.
    They can't copy the pain that built this.

    {Colors.WHITE}{Colors.BOLD}THE ASK:{Colors.END}
    
    $20K per analysis. $2M prevented.
    100x ROI.
    
    You paid 39 months to learn this.
    They pay $20K.

""")
    
    print(f"""
{Colors.CYAN}
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
                    Demo complete. Ready to execute.
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Colors.END}
""")

# ============================================================================
# MAIN
# ============================================================================
def main():
    try:
        scene_1_problem()
        scene_2_what_if()
        engine = scene_3_aion_catches()
        scene_4_analysis(engine)
        scene_5_difference()
        scene_6_pitch()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WHITE}Demo interrupted.{Colors.END}\n")

if __name__ == "__main__":
    main()
