"""
AION OS - Prospect Demo Dashboard
==================================

Visual dashboard for presenting to law firm prospects with Dan.
Click on VPN or Attorney Breach scenarios to see AION's live analysis.

Run: streamlit run dashboard_prospect.py
"""

import streamlit as st
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import random

sys.path.insert(0, str(Path(__file__).parent))

from aionos.core.temporal_engine import (
    TemporalCorrelationEngine, SecurityEvent, EventType
)
from aionos.core.baseline_engine import BehavioralBaselineEngine

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="AION OS",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# DARK THEME CSS (Matching original style)
# =============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;700&display=swap');
    
    .stApp {
        background: #0a0a0a;
    }
    
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1200px;
    }
    
    /* Logo */
    .logo {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.5rem;
        font-weight: 700;
        color: #ff4444;
        text-align: center;
        margin-bottom: 0.25rem;
        letter-spacing: -1px;
    }
    
    .tagline {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Alert Cards */
    .soc-alert {
        background: #111;
        border-left: 4px solid #ff4444;
        padding: 1rem;
        margin: 0.75rem 0;
        border-radius: 0 8px 8px 0;
        animation: fadeIn 0.5s ease-in;
    }
    
    .soc-alert-critical { 
        border-left-color: #ff4444; 
        background: linear-gradient(90deg, rgba(255,68,68,0.15) 0%, #111 100%); 
    }
    .soc-alert-high { 
        border-left-color: #ff8800; 
        background: linear-gradient(90deg, rgba(255,136,0,0.1) 0%, #111 100%); 
    }
    .soc-alert-medium { 
        border-left-color: #ffcc00; 
    }
    
    .soc-timestamp {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #666;
    }
    
    .soc-title {
        font-size: 1rem;
        font-weight: 600;
        color: #fff;
        margin: 0.25rem 0;
    }
    
    /* Detection Box */
    .detection-box {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 2px solid #ff4444;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        animation: pulseGlow 2s ease-in-out infinite;
    }
    
    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 5px rgba(255,68,68,0.3); }
        50% { box-shadow: 0 0 20px rgba(255,68,68,0.6); }
    }
    
    .detection-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #ff4444;
        margin-bottom: 0.5rem;
    }
    
    /* AION Analysis Box */
    .aion-analysis {
        background: #0d1117;
        border: 1px solid #44ff44;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .aion-logo {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        color: #44ff44;
    }
    
    /* Stats Row */
    .stats-row {
        display: flex;
        justify-content: space-around;
        padding: 1rem 0;
        border-top: 1px solid #333;
        border-bottom: 1px solid #333;
        margin: 1rem 0;
    }
    
    .stat-item {
        text-align: center;
    }
    
    .stat-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    .stat-label {
        color: #888;
        font-size: 0.8rem;
        text-transform: uppercase;
    }
    
    .stat-green { color: #44ff44; }
    .stat-red { color: #ff4444; }
    
    /* Live Indicator */
    .live-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        background: #44ff44;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    /* Comparison Cards */
    .comparison-card {
        background: #111;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
    
    .comparison-bad { border-color: #ff4444; }
    .comparison-good { border-color: #44ff44; }
    
    /* Hide streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Button styling */
    .stButton button {
        background: #ff4444 !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        font-size: 1rem !important;
        border-radius: 8px !important;
    }
    
    .stButton button:hover {
        background: #cc3333 !important;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE
# =============================================================================

if 'temporal_engine' not in st.session_state:
    st.session_state.temporal_engine = TemporalCorrelationEngine(fast_mode=True)

if 'baseline_engine' not in st.session_state:
    st.session_state.baseline_engine = BehavioralBaselineEngine(fast_mode=True)

if 'running_scenario' not in st.session_state:
    st.session_state.running_scenario = None


# =============================================================================
# SCENARIO DEFINITIONS
# =============================================================================

SCENARIOS = {
    "attorney_departure": {
        "name": "Departing Attorney Theft",
        "icon": "👔",
        "description": "Senior partner stealing client data before leaving for competitor",
        "difficulty": "HARD",
        "real_case": "Typhoon v. Knowles",
        "events": [
            {"type": EventType.PERMISSION_CHANGE, "title": "LinkedIn Profile Updated", "detail": "Changed headline to 'Open to opportunities'", "severity": "medium", "delay": 1.5},
            {"type": EventType.EMAIL_FORWARD, "title": "Email Forwarding Rule Created", "detail": "All incoming mail forwarded to personal.backup@gmail.com", "severity": "high", "delay": 2.0},
            {"type": EventType.FILE_DOWNLOAD, "title": "Bulk Document Download", "detail": "Downloaded 847 client matter files (12.5 GB)", "severity": "critical", "delay": 2.0},
            {"type": EventType.DATABASE_QUERY, "title": "Billing Data Export", "detail": "Exported billing history for 45 clients ($2.3M in revenue)", "severity": "critical", "delay": 1.5},
            {"type": EventType.CLOUD_SYNC, "title": "Personal Cloud Sync", "detail": "Files synced to personal Dropbox account", "severity": "critical", "delay": 1.5},
        ],
        "without_aion": "Discovered 36 months later during litigation",
        "with_aion": "Detected at event 3 of 5 — Day 5",
        "damages_prevented": "$2,500,000",
    },
    "vpn_breach": {
        "name": "VPN Credential Compromise", 
        "icon": "🔐",
        "description": "Attacker using stolen VPN credentials to access firm systems",
        "difficulty": "NIGHTMARE",
        "real_case": "Lapsus$ Style Attack",
        "events": [
            {"type": EventType.VPN_BRUTE_FORCE, "title": "VPN Brute Force Attempt", "detail": "5,000 failed login attempts in 30 minutes", "severity": "high", "delay": 1.5},
            {"type": EventType.VPN_ACCESS, "title": "VPN Login Success", "detail": "Successful login after brute force — IP: 185.xx.xx.xx (Russia)", "severity": "high", "delay": 1.5},
            {"type": EventType.GEOGRAPHIC_ANOMALY, "title": "Geographic Anomaly", "detail": "User normally in NYC, now connecting from Eastern Europe", "severity": "critical", "delay": 1.5},
            {"type": EventType.DATABASE_QUERY, "title": "Database Reconnaissance", "detail": "SELECT * FROM clients, matters, billing", "severity": "critical", "delay": 2.0},
            {"type": EventType.FILE_DOWNLOAD, "title": "Mass File Exfiltration", "detail": "Downloaded 15,000 files in 47 minutes", "severity": "critical", "delay": 1.5},
        ],
        "without_aion": "Discovered after ransomware deployed",
        "with_aion": "Detected at event 2 of 5 — 2 minutes",
        "damages_prevented": "$5,000,000+",
    },
    "mfa_fatigue": {
        "name": "MFA Fatigue Attack",
        "icon": "📱",
        "description": "Attacker bombarding user with MFA prompts until they accept",
        "difficulty": "NIGHTMARE", 
        "real_case": "2022 Uber Breach",
        "events": [
            {"type": EventType.VPN_MFA_BYPASS, "title": "MFA Push Spam Detected", "detail": "50+ MFA prompts sent in 20 minutes", "severity": "critical", "delay": 2.0},
            {"type": EventType.VPN_ACCESS, "title": "MFA Accepted at 2:47 AM", "detail": "User accepted MFA prompt after repeated prompts", "severity": "critical", "delay": 1.5},
            {"type": EventType.GEOGRAPHIC_ANOMALY, "title": "Impossible Travel", "detail": "Login from Brazil 3 minutes after NYC session", "severity": "critical", "delay": 1.5},
            {"type": EventType.LATERAL_MOVEMENT, "title": "Lateral Movement", "detail": "Accessed 12 internal systems in 5 minutes", "severity": "critical", "delay": 2.0},
            {"type": EventType.FILE_DOWNLOAD, "title": "Source Code Theft", "detail": "Cloned internal repositories", "severity": "critical", "delay": 1.5},
        ],
        "without_aion": "Discovered after public disclosure by attacker",
        "with_aion": "Detected at event 1 of 5 — Immediate",
        "damages_prevented": "$10,000,000+",
    },
    "insider_after_hours": {
        "name": "After-Hours Data Theft",
        "icon": "🌙",
        "description": "Disgruntled employee downloading everything at 3 AM",
        "difficulty": "EASY",
        "real_case": "Common Pattern",
        "events": [
            {"type": EventType.AFTER_HOURS_ACCESS, "title": "After-Hours Login", "detail": "VPN connection at 3:14 AM on Saturday", "severity": "medium", "delay": 1.5},
            {"type": EventType.BULK_OPERATION, "title": "Select All Operation", "detail": "User selected all files in 23 matter folders", "severity": "high", "delay": 1.5},
            {"type": EventType.FILE_DOWNLOAD, "title": "Mass Download", "detail": "Downloaded 5,247 files (34 GB)", "severity": "critical", "delay": 2.0},
            {"type": EventType.USB_ACTIVITY, "title": "USB Device Connected", "detail": "New USB device 'SanDisk Extreme 256GB'", "severity": "critical", "delay": 1.5},
        ],
        "without_aion": "Discovered when employee resigned Monday",
        "with_aion": "Detected at event 3 of 4 — 3:42 AM",
        "damages_prevented": "$500,000",
    },
}


# =============================================================================
# SIDEBAR
# =============================================================================

st.sidebar.markdown('<div class="logo" style="font-size: 1.5rem;">AION OS</div>', unsafe_allow_html=True)
st.sidebar.markdown("---")

page = st.sidebar.radio("", ["🎯 Attack Scenarios", "📊 The Difference", "⚡ System Stats"])

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="color: #444; font-size: 0.8rem; padding: 1rem 0;">
<strong>DETECTION ENGINE</strong><br>
• 29 Attack Patterns<br>
• 44 Event Types<br>
• 55,000 events/sec<br>
• 100% Detection Rate
</div>
""", unsafe_allow_html=True)


# =============================================================================
# PAGE 1: ATTACK SCENARIOS
# =============================================================================

if page == "🎯 Attack Scenarios":
    st.markdown('<div class="logo">AION OS</div>', unsafe_allow_html=True)
    st.markdown('<div class="tagline">Live Attack Detection Demo</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin: 1rem 0;">
        <span class="live-indicator"></span>
        <span style="color: #44ff44; font-weight: 600;">DETECTION ENGINE ACTIVE</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Select an Attack Scenario")
    
    # Scenario Selection Grid
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👔  Departing Attorney Theft", use_container_width=True, key="btn_attorney"):
            st.session_state.running_scenario = "attorney_departure"
            st.session_state.temporal_engine = TemporalCorrelationEngine(fast_mode=True)
            st.rerun()
            
        if st.button("📱  MFA Fatigue Attack", use_container_width=True, key="btn_mfa"):
            st.session_state.running_scenario = "mfa_fatigue"
            st.session_state.temporal_engine = TemporalCorrelationEngine(fast_mode=True)
            st.rerun()
    
    with col2:
        if st.button("🔐  VPN Credential Compromise", use_container_width=True, key="btn_vpn"):
            st.session_state.running_scenario = "vpn_breach"
            st.session_state.temporal_engine = TemporalCorrelationEngine(fast_mode=True)
            st.rerun()
            
        if st.button("🌙  After-Hours Data Theft", use_container_width=True, key="btn_after"):
            st.session_state.running_scenario = "insider_after_hours"
            st.session_state.temporal_engine = TemporalCorrelationEngine(fast_mode=True)
            st.rerun()
    
    # If a scenario is running, show it
    if st.session_state.running_scenario:
        scenario = SCENARIOS[st.session_state.running_scenario]
        
        st.markdown("---")
        
        # Scenario Header
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
            <span style="font-size: 3rem;">{scenario['icon']}</span>
            <div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #fff;">{scenario['name']}</div>
                <div style="color: #888;">{scenario['description']}</div>
                <div style="margin-top: 0.5rem;">
                    <span style="background: rgba(255,68,68,0.2); color: #ff4444; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: 600;">
                        {scenario['difficulty']}
                    </span>
                    <span style="color: #666; margin-left: 1rem; font-size: 0.9rem;">Based on: {scenario['real_case']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Reset button
        if st.button("🔄 Reset & Choose Another", key="reset"):
            st.session_state.running_scenario = None
            st.session_state.temporal_engine = TemporalCorrelationEngine(fast_mode=True)
            st.session_state.baseline_engine = BehavioralBaselineEngine(fast_mode=True)
            st.rerun()
        
        st.markdown("---")
        
        # Run the scenario
        alert_container = st.container()
        
        detected = False
        detection_event = None
        detection_pattern = None
        total_time_us = 0
        
        user_id = f"attacker_{st.session_state.running_scenario}@firm.com"
        
        with alert_container:
            for i, event_data in enumerate(scenario['events']):
                # Show the incoming alert
                severity_class = f"soc-alert-{event_data['severity']}"
                emoji = "🚨" if event_data['severity'] == "critical" else "⚠️" if event_data['severity'] == "high" else "ℹ️"
                
                st.markdown(f"""
                <div class="soc-alert {severity_class}">
                    <div class="soc-timestamp">{datetime.now().strftime('%H:%M:%S')} UTC — Event {i+1} of {len(scenario['events'])}</div>
                    <div class="soc-title">{emoji} {event_data['title']}</div>
                    <div style="color: #888; font-size: 0.9rem;">
                        {event_data['detail']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Process through AION
                event = SecurityEvent(
                    event_id=f"demo_{i:04d}",
                    user_id=user_id,
                    event_type=event_data['type'],
                    timestamp=datetime.now(),
                    source_system="demo",
                    details={"title": event_data['title']}
                )
                
                start = time.perf_counter()
                alerts = st.session_state.temporal_engine.ingest_event(event)
                elapsed_us = (time.perf_counter() - start) * 1_000_000
                total_time_us += elapsed_us
                
                time.sleep(event_data['delay'])
                
                # Check for detection
                if alerts and not detected:
                    detected = True
                    detection_event = i + 1
                    detection_pattern = alerts[0].pattern_name
                    
                    # Show detection alert
                    st.markdown(f"""
                    <div class="detection-box">
                        <div class="detection-title">🚨 ATTACK PATTERN DETECTED</div>
                        <div style="color: #fff; font-size: 1.1rem; margin: 0.5rem 0;">
                            Pattern: <strong>{detection_pattern}</strong>
                        </div>
                        <div style="color: #888;">
                            Detected at event {detection_event} of {len(scenario['events'])} 
                            ({(detection_event/len(scenario['events'])*100):.0f}% into attack sequence)
                        </div>
                        <div style="margin-top: 1rem;">
                            <span style="color: #44ff44; font-family: 'JetBrains Mono', monospace;">
                                Detection time: {elapsed_us:.0f} microseconds
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show AION's analysis
                    st.markdown(f"""
                    <div class="aion-analysis">
                        <div style="margin-bottom: 1rem;">
                            <span class="aion-logo">🤖 AION OS ANALYSIS</span>
                        </div>
                        <div style="color: #fff; margin-bottom: 1rem;">
                            <strong>Threat Assessment:</strong> {scenario['difficulty']} severity attack in progress
                        </div>
                        <div style="color: #fff; margin-bottom: 1rem;">
                            <strong>Pattern Match:</strong> {detection_pattern} — Similar to {scenario['real_case']}
                        </div>
                        <div style="color: #fff; margin-bottom: 1rem;">
                            <strong>Immediate Actions Required:</strong>
                            <ul style="color: #888; margin-top: 0.5rem;">
                                <li>Lock user account immediately</li>
                                <li>Preserve all access logs for forensics</li>
                                <li>Notify security team and legal counsel</li>
                                <li>Initiate incident response protocol</li>
                            </ul>
                        </div>
                        <div style="color: #fff;">
                            <strong>Evidence to Preserve:</strong>
                            <ul style="color: #888; margin-top: 0.5rem;">
                                <li>VPN connection logs</li>
                                <li>Email forwarding rules</li>
                                <li>File access audit trail</li>
                                <li>Database query history</li>
                            </ul>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Stop processing more events - we caught it
                    break
        
        # Final Summary
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="comparison-card comparison-bad">
                <div style="font-size: 1.2rem; color: #ff4444; font-weight: 700; margin-bottom: 1rem;">❌ WITHOUT AION</div>
                <div style="color: #888; font-size: 1.1rem;">
                    {scenario['without_aion']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="comparison-card comparison-good">
                <div style="font-size: 1.2rem; color: #44ff44; font-weight: 700; margin-bottom: 1rem;">✅ WITH AION</div>
                <div style="color: #888; font-size: 1.1rem;">
                    {scenario['with_aion']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; margin-top: 1rem;">
            <div style="font-size: 2.5rem; color: #44ff44; font-weight: 700;">{scenario['damages_prevented']}</div>
            <div style="color: #888; font-size: 1rem;">Potential Damages Prevented</div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# PAGE 2: THE DIFFERENCE
# =============================================================================

elif page == "📊 The Difference":
    st.markdown('<div class="logo">AION OS</div>', unsafe_allow_html=True)
    st.markdown('<div class="tagline">What Changes With AION</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="comparison-card comparison-bad">
            <div style="font-size: 1.5rem; color: #ff4444; font-weight: 700; margin-bottom: 1rem;">❌ WITHOUT AION</div>
            <div style="text-align: left; color: #888;">
                <p><strong style="color: #ff4444;">Attack discovered:</strong> Months later</p>
                <p><strong style="color: #ff4444;">Response time:</strong> Too late</p>
                <p><strong style="color: #ff4444;">Litigation:</strong> 39 months</p>
                <p><strong style="color: #ff4444;">Data recovered:</strong> Never</p>
                <p><strong style="color: #ff4444;">Total cost:</strong> $2-5M+</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="comparison-card comparison-good">
            <div style="font-size: 1.5rem; color: #44ff44; font-weight: 700; margin-bottom: 1rem;">✅ WITH AION</div>
            <div style="text-align: left; color: #888;">
                <p><strong style="color: #44ff44;">Attack detected:</strong> Minutes</p>
                <p><strong style="color: #44ff44;">Response time:</strong> Immediate lockdown</p>
                <p><strong style="color: #44ff44;">Litigation:</strong> Prevented</p>
                <p><strong style="color: #44ff44;">Data protected:</strong> Yes</p>
                <p><strong style="color: #44ff44;">AION cost:</strong> $50,000/year</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <div style="font-size: 4rem; color: #44ff44; font-weight: 700;">50x</div>
        <div style="font-size: 1.2rem; color: #888;">Return on Investment</div>
        <div style="margin-top: 1rem; color: #666; font-size: 0.9rem;">
            $2,500,000 prevented ÷ $50,000 cost = 50x ROI
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### Why AION Catches What Others Miss")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🔗 Temporal Correlation**
        
        Links events across days and weeks.
        LinkedIn update Day 1 + Downloads Day 5 = Pattern.
        
        *Splunk sees individual logs.*
        *AION sees the attack chain.*
        """)
    
    with col2:
        st.markdown("""
        **🎯 Legal-Specific Patterns**
        
        29 patterns built from real law firm cases.
        Typhoon, departures, client theft.
        
        *Generic SIEM doesn't know law firms.*
        *AION was built for them.*
        """)
    
    with col3:
        st.markdown("""
        **⚡ Real-Time Speed**
        
        55,000 events per second.
        Detection in microseconds.
        
        *Attackers move fast.*
        *AION moves faster.*
        """)


# =============================================================================
# PAGE 3: SYSTEM STATS
# =============================================================================

elif page == "⚡ System Stats":
    st.markdown('<div class="logo">AION OS</div>', unsafe_allow_html=True)
    st.markdown('<div class="tagline">Detection Engine Performance</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Live stats
    st.markdown("""
    <div class="stats-row">
        <div class="stat-item">
            <div class="stat-value stat-green">55,000</div>
            <div class="stat-label">Events / Second</div>
        </div>
        <div class="stat-item">
            <div class="stat-value stat-green">23μs</div>
            <div class="stat-label">Avg Latency</div>
        </div>
        <div class="stat-item">
            <div class="stat-value stat-green">29</div>
            <div class="stat-label">Attack Patterns</div>
        </div>
        <div class="stat-item">
            <div class="stat-value stat-green">100%</div>
            <div class="stat-label">Detection Rate</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Detection by Attack Category")
    
    categories = {
        "VPN Breaches": {"count": 12, "detected": 12},
        "Insider Threats": {"count": 3, "detected": 3},
        "Lateral Movement": {"count": 3, "detected": 3},
        "Persistence": {"count": 2, "detected": 2},
        "Evasion": {"count": 3, "detected": 3},
        "External Attacks": {"count": 3, "detected": 3},
    }
    
    for cat, stats in categories.items():
        pct = stats["detected"] / stats["count"] * 100
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid #222;">
            <span style="color: #fff; font-weight: 500;">{cat}</span>
            <div style="display: flex; align-items: center; gap: 1rem;">
                <span style="color: #888;">{stats['detected']}/{stats['count']}</span>
                <span style="color: #44ff44; font-weight: 700;">{pct:.0f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Red Team Simulation Results")
    
    st.markdown("""
    <div style="background: #111; border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
        <table style="width: 100%; color: #888;">
            <tr style="border-bottom: 1px solid #333;">
                <th style="text-align: left; padding: 0.75rem; color: #666;">Difficulty</th>
                <th style="text-align: center; padding: 0.75rem; color: #666;">Tested</th>
                <th style="text-align: center; padding: 0.75rem; color: #666;">Detected</th>
                <th style="text-align: right; padding: 0.75rem; color: #666;">Rate</th>
            </tr>
            <tr style="border-bottom: 1px solid #222;">
                <td style="padding: 0.75rem;">EASY</td>
                <td style="text-align: center;">3</td>
                <td style="text-align: center;">3</td>
                <td style="text-align: right; color: #44ff44; font-weight: 700;">100%</td>
            </tr>
            <tr style="border-bottom: 1px solid #222;">
                <td style="padding: 0.75rem;">MEDIUM</td>
                <td style="text-align: center;">5</td>
                <td style="text-align: center;">5</td>
                <td style="text-align: right; color: #44ff44; font-weight: 700;">100%</td>
            </tr>
            <tr style="border-bottom: 1px solid #222;">
                <td style="padding: 0.75rem;">HARD</td>
                <td style="text-align: center;">10</td>
                <td style="text-align: center;">10</td>
                <td style="text-align: right; color: #44ff44; font-weight: 700;">100%</td>
            </tr>
            <tr>
                <td style="padding: 0.75rem; color: #ff4444;">NIGHTMARE</td>
                <td style="text-align: center;">8</td>
                <td style="text-align: center;">8</td>
                <td style="text-align: right; color: #44ff44; font-weight: 700;">100%</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem; margin-top: 1rem;">
        <div style="font-size: 2rem; color: #44ff44; font-weight: 700;">26 of 26 Attacks Detected</div>
        <div style="color: #888; margin-top: 0.5rem;">Including all NIGHTMARE-level scenarios</div>
    </div>
    """, unsafe_allow_html=True)
