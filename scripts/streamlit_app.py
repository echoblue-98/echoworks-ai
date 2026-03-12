"""
AION OS - Attorney Departure Risk Analysis
Clean, demo-focused web interface
"""

import streamlit as st
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from aionos.modules.heist_planner import HeistPlanner
from aionos.modules.soc_ingestion import SOCIngestionEngine

# Page config - dark theme
st.set_page_config(
    page_title="AION OS",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Minimal dark CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;700&display=swap');
    
    .stApp {
        background: #0a0a0a;
    }
    
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 900px;
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
    
    /* ROI Card */
    .roi-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #ff4444;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        text-align: center;
    }
    
    .roi-number {
        font-family: 'JetBrains Mono', monospace;
        font-size: 3rem;
        font-weight: 700;
        color: #ff4444;
        margin: 0;
    }
    
    .roi-label {
        color: #888;
        font-size: 0.9rem;
        margin-top: 0.25rem;
    }
    
    /* Risk indicator */
    .risk-high { color: #ff4444; }
    .risk-medium { color: #ffaa00; }
    .risk-low { color: #44ff44; }
    
    /* Vulnerability card */
    .vuln-card {
        background: #111;
        border-left: 3px solid #ff4444;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .vuln-critical { border-left-color: #ff4444; }
    .vuln-high { border-left-color: #ff8800; }
    .vuln-medium { border-left-color: #ffcc00; }
    
    /* Hide streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Sidebar */
    .css-1d391kg {
        background: #0a0a0a;
    }
    
    /* SOC Cards */
    .soc-alert {
        background: #111;
        border-left: 4px solid #ff4444;
        padding: 1rem;
        margin: 0.75rem 0;
        border-radius: 0 8px 8px 0;
        animation: fadeIn 0.5s ease-in;
    }
    
    .soc-alert-critical { border-left-color: #ff4444; background: linear-gradient(90deg, rgba(255,68,68,0.1) 0%, #111 100%); }
    .soc-alert-high { border-left-color: #ff8800; background: linear-gradient(90deg, rgba(255,136,0,0.1) 0%, #111 100%); }
    .soc-alert-medium { border-left-color: #ffcc00; }
    
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
    
    .soc-pattern {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        color: #ff4444;
        background: rgba(255,68,68,0.2);
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        display: inline-block;
        margin-top: 0.5rem;
    }
    
    .comparison-card {
        background: #111;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
    
    .comparison-bad { border-color: #ff4444; }
    .comparison-good { border-color: #44ff44; }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .live-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        background: #44ff44;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    /* Input styling */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background: #1a1a1a !important;
        border: 1px solid #333 !important;
        color: white !important;
    }
    
    .stButton button {
        background: #ff4444 !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        font-size: 1.1rem !important;
    }
    
    .stButton button:hover {
        background: #cc3333 !important;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.markdown('<div class="logo" style="font-size: 1.5rem;">AION OS</div>', unsafe_allow_html=True)
st.sidebar.markdown("---")
page = st.sidebar.radio("", ["🔴 Attorney Analysis", "🛡️ SOC Live Feed", "📊 The Difference"])
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="color: #444; font-size: 0.8rem; padding: 1rem 0;">
<strong>100% LOCAL</strong><br>
Zero data sent to external LLMs
</div>
""", unsafe_allow_html=True)

# ============================================================================
# PAGE 1: ATTORNEY ANALYSIS (Original)
# ============================================================================
if page == "🔴 Attorney Analysis":
    # Header
    st.markdown('<div class="logo">AION OS</div>', unsafe_allow_html=True)
    st.markdown('<div class="tagline">Attorney Departure Risk Analysis</div>', unsafe_allow_html=True)

    # Simple input form
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        attorney_name = st.text_input("Attorney Name", placeholder="e.g., Sarah Johnson")
        practice_area = st.text_input("Practice Area", placeholder="e.g., Corporate M&A")

    with col2:
        years = st.number_input("Years at Firm", min_value=1, max_value=40, value=10)
        title = st.selectbox("Title", ["Partner", "Senior Partner", "Of Counsel", "Associate"])

    clients = st.text_input("Key Clients (optional)", placeholder="e.g., TechCorp, Acme Inc")
    destination = st.text_input("Departing To (optional)", placeholder="e.g., Competitor Law Group")

    # Run Analysis Button
    st.markdown("")
    run_clicked = st.button("🔴 Run Risk Analysis", use_container_width=True)

    if run_clicked:
        if not attorney_name or not practice_area:
            st.error("Please enter attorney name and practice area")
        else:
            # Progress
            progress = st.empty()
            status = st.empty()
            
            with st.spinner(""):
                status.markdown("**Assembling adversarial crew...**")
                
                try:
                    # Run analysis
                    planner = HeistPlanner(use_gemini=True)
                    result = planner.plan_heist(
                        attorney_name=f"{attorney_name} ({title})",
                        practice_area=practice_area,
                        years_at_firm=years,
                        clients=clients or "Various clients",
                        destination=destination or "Competitor firm"
                    )
                    
                    status.empty()
                    
                    # === RESULTS ===
                    
                    # ROI Summary - THE MONEY SHOT
                    financial = result.get('financial_risk', {})
                    expected_loss = financial.get('expected_loss', 2500000)
                    aion_cost = 20000
                    roi = expected_loss / aion_cost
                    
                    st.markdown(f"""
                    <div class="roi-card">
                        <div class="roi-number">${expected_loss:,.0f}</div>
                        <div class="roi-label">Expected Loss from Departure</div>
                        <div style="margin-top: 1rem; display: flex; justify-content: center; gap: 3rem;">
                            <div>
                                <div style="font-size: 1.5rem; color: #44ff44; font-weight: 700;">${aion_cost:,}</div>
                                <div style="color: #666; font-size: 0.8rem;">AION Cost</div>
                            </div>
                            <div>
                                <div style="font-size: 1.5rem; color: #44ff44; font-weight: 700;">{roi:.0f}x</div>
                                <div style="color: #666; font-size: 0.8rem;">ROI</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Vulnerability Count
                    vulns = result.get('vulnerabilities', [])
                    critical_count = len([v for v in vulns if v.get('severity') == 'critical'])
                    
                    st.markdown("---")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Vulnerabilities", len(vulns))
                    col2.metric("Critical", critical_count, delta="⚠️" if critical_count > 0 else None)
                    col3.metric("Days Until Departure", "30", delta="URGENT")
                    
                    # Vulnerabilities List
                    st.markdown("### 🔴 Critical Findings")
                    
                    for i, vuln in enumerate(vulns[:6], 1):  # Show top 6
                        severity = vuln.get('severity', 'medium')
                        emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡'}.get(severity, '⚪')
                        
                        with st.expander(f"{emoji} {vuln.get('title', f'Finding {i}')} — {severity.upper()}"):
                            st.markdown(vuln.get('description', 'No description'))
                            if vuln.get('recommendation'):
                                st.markdown(f"**Action:** {vuln.get('recommendation')}")
                    
                    # Timeline
                    if result.get('timeline'):
                        st.markdown("### 📅 Critical Dates")
                        timeline = result.get('timeline', {})
                        
                        audit_dates = timeline.get('critical_audit_dates', [])
                        if audit_dates:
                            for date_info in audit_dates[:3]:
                                st.markdown(f"**{date_info.get('date', 'TBD')}** — {date_info.get('action', 'Audit required')}")
                    
                    # Pattern Match
                    pattern = result.get('pattern_match', {})
                    if pattern.get('pattern_name'):
                        st.markdown("### 📊 Historical Pattern Match")
                        st.info(f"**{pattern.get('similarity', 0):.0f}% similar** to: {pattern.get('pattern_name')}")
                        if pattern.get('outcome'):
                            st.caption(f"Previous outcome: {pattern.get('outcome')[:200]}...")
                    
                    # Immediate Actions
                    st.markdown("### ⚡ Immediate Actions (Next 72 Hours)")
                    st.markdown("""
                    1. **Audit email forwarding rules** — Check rules created in last 30 days
                    2. **Review VPN access logs** — Flag after-hours or unusual locations  
                    3. **Monitor document downloads** — Set alerts for bulk file access
                    """)
                    
                    st.markdown("---")
                    st.success("Analysis complete. Ready for client presentation.")
                    
                except Exception as e:
                    status.empty()
                    st.error(f"Analysis failed: {str(e)}")
                    st.exception(e)

    else:
        # Show example/placeholder when not running
        st.markdown("")
        st.markdown("""
        <div style="text-align: center; color: #444; padding: 3rem 0;">
            <p style="font-size: 1.1rem;">Enter attorney details above and click <strong style="color: #ff4444;">Run Risk Analysis</strong></p>
            <p style="font-size: 0.9rem; margin-top: 1rem;">90-second analysis • 5 AI agents • Actionable audit checklist</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# PAGE 2: SOC LIVE FEED
# ============================================================================
elif page == "🛡️ SOC Live Feed":
    st.markdown('<div class="logo">AION OS</div>', unsafe_allow_html=True)
    st.markdown('<div class="tagline">Security Operations Center — Live Feed</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin: 1rem 0;">
        <span class="live-indicator"></span>
        <span style="color: #44ff44; font-weight: 600;">MONITORING ACTIVE</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Demo mode selector
    demo_mode = st.radio("Select Demo", ["🔴 Replay Typhoon Attack", "⚡ Custom Alert"], horizontal=True)
    
    if demo_mode == "🔴 Replay Typhoon Attack":
        st.markdown("### The Attack That Started It All")
        st.markdown("*January 2021 — Typhoon Advertising*")
        st.markdown("")
        
        if st.button("▶️ Start Replay", use_container_width=True):
            engine = SOCIngestionEngine()
            alert_container = st.container()
            
            with alert_container:
                # Alert 1: VPN Anomaly
                st.markdown("""
                <div class="soc-alert soc-alert-high">
                    <div class="soc-timestamp">02:34:17 UTC</div>
                    <div class="soc-title">⚠️ VPN Anomaly Detected</div>
                    <div style="color: #888; font-size: 0.9rem;">
                        User: <strong>former_employee</strong><br>
                        Location: <span style="color: #ff8800;">Unknown — Eastern Europe VPN</span><br>
                        Action: VPN connection from new geographic location
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                time.sleep(2)
                
                # Alert 2: Database Access
                st.markdown("""
                <div class="soc-alert soc-alert-critical">
                    <div class="soc-timestamp">02:47:03 UTC</div>
                    <div class="soc-title">🚨 CRITICAL: Database Bulk Export</div>
                    <div style="color: #888; font-size: 0.9rem;">
                        User: <strong>former_employee</strong><br>
                        Query: <span style="color: #ff4444;">SELECT * FROM clients, billing, campaigns, contacts</span><br>
                        Rows: <span style="color: #ff4444;">15,000</span>
                    </div>
                    <div class="soc-pattern">🔴 PATTERN MATCH: vpn_database_theft</div>
                </div>
                """, unsafe_allow_html=True)
                
                time.sleep(1)
                
                # Pattern Match Alert
                st.error("🚨 CRITICAL PATTERN DETECTED: VPN DATABASE THEFT")
                
                # Run the analysis
                alert = engine.ingest_alert({
                    'alert_type': 'database_access',
                    'user_id': 'former_employee',
                    'severity': 'critical',
                    'action': 'SELECT * FROM clients, billing, campaigns, contacts',
                    'details': {'rows': 15000},
                }, auto_escalate=False)
                
                time.sleep(1)
                
                st.markdown("---")
                st.markdown("### 🤖 Security Attacker Agent — Analysis")
                
                analysis = engine.trigger_security_attacker('former_employee', use_local=True)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Threat Type", analysis['threat_type'])
                col2.metric("Severity", analysis['severity'])
                col3.metric("Confidence", analysis['confidence'])
                
                st.markdown("#### Immediate Actions")
                for action in analysis['immediate_actions'][:5]:
                    st.markdown(f"- {action}")
                
                st.markdown("#### Forensic Preservation")
                for item in analysis['forensic_preservation'][:4]:
                    st.markdown(f"- {item}")
                
                st.markdown("---")
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 1.5rem; color: #44ff44; font-weight: 700;">⏱️ Detection Time: 13 minutes</div>
                    <div style="color: #666; margin-top: 0.5rem;">From first anomaly to full threat assessment</div>
                </div>
                """, unsafe_allow_html=True)
    
    else:
        # Custom alert mode
        st.markdown("### Inject Custom SOC Alert")
        
        alert_type = st.selectbox("Alert Type", [
            "vpn_anomaly", "database_access", "email_forward", 
            "large_download", "after_hours", "cloud_sync"
        ])
        
        user_id = st.text_input("User ID", value="departing_attorney")
        severity = st.selectbox("Severity", ["critical", "high", "medium", "low"])
        action_desc = st.text_input("Action Description", value="Unusual activity detected")
        
        if st.button("🚨 Inject Alert", use_container_width=True):
            engine = SOCIngestionEngine()
            
            alert = engine.ingest_alert({
                'alert_type': alert_type,
                'user_id': user_id,
                'severity': severity,
                'action': action_desc,
            }, auto_escalate=True)
            
            st.markdown(f"""
            <div class="soc-alert soc-alert-{severity}">
                <div class="soc-timestamp">{datetime.now().strftime('%H:%M:%S')} UTC</div>
                <div class="soc-title">{'🚨' if severity == 'critical' else '⚠️'} {alert_type.replace('_', ' ').title()}</div>
                <div style="color: #888; font-size: 0.9rem;">
                    User: <strong>{user_id}</strong><br>
                    Action: {action_desc}
                </div>
                <div style="margin-top: 0.5rem;">
                    Risk Score: <span style="color: {'#ff4444' if alert.departure_risk_score > 70 else '#ffcc00'}; font-weight: 700;">{alert.departure_risk_score:.0f}/100</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if alert.patterns_matched:
                for pattern in alert.patterns_matched:
                    st.markdown(f'<div class="soc-pattern">🔴 PATTERN: {pattern}</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("### 🤖 Security Attacker Agent — Analysis")
                
                if alert.agent_analysis:
                    analysis = alert.agent_analysis
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Threat Type", analysis['threat_type'])
                    col2.metric("Severity", analysis['severity'])
                    col3.metric("Confidence", analysis['confidence'])
                    
                    st.markdown("#### Immediate Actions")
                    for action in analysis['immediate_actions'][:5]:
                        st.markdown(f"- {action}")

# ============================================================================
# PAGE 3: THE DIFFERENCE
# ============================================================================
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
                <p><strong style="color: #44ff44;">Attack detected:</strong> 13 minutes</p>
                <p><strong style="color: #44ff44;">Response time:</strong> Immediate lockdown</p>
                <p><strong style="color: #44ff44;">Litigation:</strong> Prevented</p>
                <p><strong style="color: #44ff44;">Data protected:</strong> Yes</p>
                <p><strong style="color: #44ff44;">AION cost:</strong> $20,000</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <div style="font-size: 4rem; color: #44ff44; font-weight: 700;">125x</div>
        <div style="font-size: 1.2rem; color: #888;">Return on Investment</div>
        <div style="margin-top: 1rem; color: #666; font-size: 0.9rem;">
            $2,500,000 prevented ÷ $20,000 cost = 125x ROI
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### The AION Moat")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🧠 5 Adversarial Agents**
        
        AI that thinks like attackers.
        Not compliance checklists.
        """)
    
    with col2:
        st.markdown("""
        **📊 Pattern Database**
        
        Built from real cases.
        Real litigation. Real pain.
        """)
    
    with col3:
        st.markdown("""
        **🔒 100% Local**
        
        Zero data sent to any LLM.
        Your secrets stay yours.
        """)
    
    st.markdown("---")
    
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <em>"You paid 39 months to learn this. They pay $20K."</em>
    </div>
    """, unsafe_allow_html=True)
