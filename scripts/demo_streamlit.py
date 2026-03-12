"""
AION OS - Dynamic Attorney Departure Analysis
A visually striking demo interface for law firm pitches
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import time

# Add aionos to path
sys.path.insert(0, str(Path(__file__).parent))

from aionos.modules.heist_planner import HeistPlanner

# Page config - Dark theme for impact
st.set_page_config(
    page_title="AION OS",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Aggressive CSS for visual impact
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap');
    
    /* Dark theme override */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    .main .block-container {
        padding-top: 1rem;
        max-width: 1400px;
    }
    
    /* Glowing header */
    .hero-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 4.5rem;
        font-weight: 800;
        text-align: center;
        color: #ff4444;
        text-shadow: 0 0 20px rgba(255,68,68,0.5), 0 0 40px rgba(255,68,68,0.3);
        letter-spacing: -3px;
        margin-bottom: 0;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { text-shadow: 0 0 20px rgba(255,68,68,0.5), 0 0 40px rgba(255,68,68,0.3); }
        50% { text-shadow: 0 0 30px rgba(255,68,68,0.8), 0 0 60px rgba(255,68,68,0.5); }
    }
    
    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        color: #888;
        text-align: center;
        margin-top: 0;
        letter-spacing: 8px;
        text-transform: uppercase;
    }
    
    /* Threat level indicator */
    .threat-level {
        background: linear-gradient(90deg, #ff4444, #ff6b6b);
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 25px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 0.9rem;
        display: inline-block;
        animation: threat-pulse 1.5s infinite;
    }
    
    @keyframes threat-pulse {
        0%, 100% { box-shadow: 0 0 10px rgba(255,68,68,0.5); }
        50% { box-shadow: 0 0 25px rgba(255,68,68,0.8); }
    }
    
    /* Stats cards */
    .stat-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,68,68,0.2);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        border-color: rgba(255,68,68,0.5);
        box-shadow: 0 0 30px rgba(255,68,68,0.1);
        transform: translateY(-2px);
    }
    
    .stat-number {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.5rem;
        font-weight: 700;
        color: #ff4444;
        margin: 0;
    }
    
    .stat-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 0.5rem;
    }
    
    /* Vulnerability cards */
    .vuln-critical {
        background: linear-gradient(135deg, rgba(255,68,68,0.15), rgba(255,68,68,0.05));
        border-left: 4px solid #ff4444;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .vuln-high {
        background: linear-gradient(135deg, rgba(255,165,0,0.15), rgba(255,165,0,0.05));
        border-left: 4px solid #ffa500;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    /* Terminal style text */
    .terminal-text {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
        color: #00ff00;
        background: rgba(0,0,0,0.5);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid rgba(0,255,0,0.2);
    }
    
    /* Money highlight */
    .money-big {
        font-family: 'JetBrains Mono', monospace;
        font-size: 3rem;
        font-weight: 800;
        color: #ff4444;
        text-shadow: 0 0 20px rgba(255,68,68,0.3);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: white !important;
    }
    
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.05) !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom button */
    .stButton > button {
        background: linear-gradient(90deg, #ff4444, #ff6b6b) !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 0.75rem 2rem !important;
        border-radius: 8px !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        box-shadow: 0 0 30px rgba(255,68,68,0.5) !important;
        transform: scale(1.02) !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #ff4444, #ff6b6b) !important;
    }
    
    /* Section headers */
    .section-header {
        font-family: 'Inter', sans-serif;
        font-size: 1.5rem;
        font-weight: 600;
        color: #fff;
        border-bottom: 2px solid rgba(255,68,68,0.3);
        padding-bottom: 0.5rem;
        margin: 2rem 0 1rem 0;
    }
    
    /* Timeline */
    .timeline-item {
        background: rgba(255,255,255,0.02);
        border-left: 3px solid #ff4444;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
        position: relative;
    }
    
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -8px;
        top: 50%;
        transform: translateY(-50%);
        width: 12px;
        height: 12px;
        background: #ff4444;
        border-radius: 50%;
        box-shadow: 0 0 10px rgba(255,68,68,0.5);
    }
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown('<h1 class="hero-title">AION OS</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Adversarial Intelligence System</p>', unsafe_allow_html=True)

# Threat level banner
st.markdown("""
<div style="text-align: center; margin: 1.5rem 0;">
    <span class="threat-level">🔴 ATTORNEY DEPARTURE THREAT ANALYSIS</span>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Compact input form
st.markdown('<div class="section-header">📋 Target Profile</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    attorney_name = st.text_input("Name", value="Sarah Chen")
    
with col2:
    title = st.selectbox("Title", ["Associate", "Senior Associate", "Partner", "Senior Partner"], index=3)
    
with col3:
    years_at_firm = st.number_input("Tenure (Years)", min_value=1, max_value=50, value=15)
    
with col4:
    practice_area = st.text_input("Practice Area", value="Corporate M&A")

col1, col2 = st.columns(2)

with col1:
    destination = st.text_input("Destination", value="Wilson & Associates (Competitor)")
    
with col2:
    access_level = st.selectbox(
        "System Access",
        ["Basic", "Standard", "Full Access", "Full + Client Portal"],
        index=3
    )

active_cases = st.text_input("Active Matters", value="TechCorp Merger ($2.5B), StartupCo Acquisition, 3 active M&A deals")

# Use Gemini toggle
use_gemini = st.checkbox("Free Analysis Mode", value=True, help="Uses Gemini 2.5 Flash")

st.markdown("")

# Launch Button
if st.button("🚨 EXECUTE THREAT ANALYSIS", use_container_width=True):
    if not attorney_name:
        st.error("Target name required")
    else:
        # Dramatic progress display
        progress_container = st.container()
        
        with progress_container:
            st.markdown("""
            <div class="terminal-text">
            <span style="color: #888;">$</span> Initializing AION adversarial engine...<br>
            <span style="color: #888;">$</span> Loading Heist Crew modules...<br>
            </div>
            """, unsafe_allow_html=True)
            
            progress_bar = st.progress(0)
            status = st.empty()
            
            agents = [
                ("👤 SOCIAL ENGINEER", "Mapping trust relationships and social vectors...", 20),
                ("💻 TECH INFILTRATOR", "Analyzing digital access patterns...", 40),
                ("🔍 INTEL GATHERER", "Extracting client relationship data...", 60),
                ("⚖️ LEGAL MANIPULATOR", "Identifying contract vulnerabilities...", 80),
                ("🎯 EXIT STRATEGIST", "Calculating optimal exfiltration timeline...", 95),
            ]
            
            for agent_name, agent_status, progress in agents:
                status.markdown(f"""
                <div class="terminal-text">
                <span style="color: #ff4444;">[ACTIVE]</span> {agent_name}<br>
                <span style="color: #666;">{agent_status}</span>
                </div>
                """, unsafe_allow_html=True)
                progress_bar.progress(progress)
                time.sleep(0.5)
            
            try:
                planner = HeistPlanner(use_gemini=use_gemini)
                
                attorney_profile = {
                    "name": attorney_name,
                    "title": title,
                    "practice_area": practice_area,
                    "years_at_firm": years_at_firm,
                    "active_cases": active_cases,
                    "system_access": access_level,
                    "destination": destination
                }
                
                result = planner.analyze_departure_risk(attorney_profile)
                
                progress_bar.progress(100)
                status.markdown("""
                <div class="terminal-text">
                <span style="color: #00ff00;">[COMPLETE]</span> Threat analysis finished.<br>
                <span style="color: #666;">Rendering results...</span>
                </div>
                """, unsafe_allow_html=True)
                
                time.sleep(0.5)
                progress_bar.empty()
                status.empty()
                
                # Results
                vulnerabilities = result.get('vulnerabilities', [])
                financial = result.get('financial_analysis', {})
                timeline = result.get('timeline_analysis', {})
                pattern_match = result.get('pattern_match', {})
                
                # Key metrics row
                st.markdown('<div class="section-header">⚡ Threat Assessment</div>', unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="stat-card">
                        <p class="stat-number">{len(vulnerabilities)}</p>
                        <p class="stat-label">Attack Vectors</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    critical = len([v for v in vulnerabilities if v.get('severity') == 'CRITICAL'])
                    st.markdown(f"""
                    <div class="stat-card">
                        <p class="stat-number" style="color: #ff4444;">{critical}</p>
                        <p class="stat-label">Critical Threats</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    expected_loss = financial.get('expected_loss', 0)
                    st.markdown(f"""
                    <div class="stat-card">
                        <p class="stat-number">${expected_loss/1000000:.1f}M</p>
                        <p class="stat-label">At Risk</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    roi = financial.get('roi_multiple', 0)
                    st.markdown(f"""
                    <div class="stat-card">
                        <p class="stat-number" style="color: #00ff00;">{roi:.0f}x</p>
                        <p class="stat-label">ROI</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Big money callout
                st.markdown(f"""
                <div style="text-align: center; margin: 2rem 0; padding: 2rem; background: rgba(255,68,68,0.05); border-radius: 12px; border: 1px solid rgba(255,68,68,0.2);">
                    <p style="color: #888; font-size: 1rem; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 3px;">Expected Financial Impact</p>
                    <p class="money-big">${expected_loss:,.0f}</p>
                    <p style="color: #666; font-size: 0.9rem; margin-top: 0.5rem;">Prevention cost: $20,000 | Net savings: ${expected_loss - 20000:,.0f}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Vulnerabilities
                st.markdown('<div class="section-header">🎯 Identified Attack Vectors</div>', unsafe_allow_html=True)
                
                critical_vulns = [v for v in vulnerabilities if v.get('severity') == 'CRITICAL']
                high_vulns = [v for v in vulnerabilities if v.get('severity') == 'HIGH']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🔴 CRITICAL**")
                    for vuln in critical_vulns[:4]:
                        st.markdown(f"""
                        <div class="vuln-critical">
                            <strong style="color: #fff;">{vuln.get('title', 'Unknown')}</strong><br>
                            <span style="color: #aaa; font-size: 0.85rem;">{vuln.get('description', 'N/A')[:150]}...</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**🟠 HIGH PRIORITY**")
                    for vuln in high_vulns[:4]:
                        st.markdown(f"""
                        <div class="vuln-high">
                            <strong style="color: #fff;">{vuln.get('title', 'Unknown')}</strong><br>
                            <span style="color: #aaa; font-size: 0.85rem;">{vuln.get('description', 'N/A')[:150]}...</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Timeline
                if timeline:
                    st.markdown('<div class="section-header">📅 Critical Timeline</div>', unsafe_allow_html=True)
                    
                    departure_date = datetime.now() + timedelta(days=30)
                    days_remaining = 30
                    
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-around; text-align: center; margin: 1rem 0;">
                        <div>
                            <p style="color: #ff4444; font-family: 'JetBrains Mono'; font-size: 2rem; margin: 0;">{days_remaining}</p>
                            <p style="color: #666; font-size: 0.8rem; text-transform: uppercase;">Days Until Departure</p>
                        </div>
                        <div>
                            <p style="color: #ffa500; font-family: 'JetBrains Mono'; font-size: 2rem; margin: 0;">7</p>
                            <p style="color: #666; font-size: 0.8rem; text-transform: uppercase;">Critical Audit Days</p>
                        </div>
                        <div>
                            <p style="color: #00ff00; font-family: 'JetBrains Mono'; font-size: 2rem; margin: 0;">47</p>
                            <p style="color: #666; font-size: 0.8rem; text-transform: uppercase;">Forensic Tasks</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Critical dates
                    critical_dates = timeline.get('critical_dates', [])
                    if critical_dates:
                        for date_item in critical_dates[:4]:
                            st.markdown(f"""
                            <div class="timeline-item">
                                <strong style="color: #ff4444;">{date_item.get('date', 'TBD')}</strong>
                                <span style="color: #aaa; margin-left: 1rem;">{date_item.get('action', 'N/A')}</span>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Pattern match (if exists)
                matched_patterns = pattern_match.get('matched_patterns', []) if pattern_match else []
                if matched_patterns:
                    pattern = matched_patterns[0]
                    st.markdown(f"""
                    <div style="margin-top: 2rem; padding: 1.5rem; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px;">
                        <p style="color: #888; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 0.5rem;">📊 Historical Pattern Match</p>
                        <p style="color: #fff; font-size: 1.1rem; margin: 0;">
                            <strong>{pattern.get('similarity_score', 0):.0%}</strong> similar to <strong style="color: #ff4444;">{pattern.get('case_name', 'Unknown Case')}</strong>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                st.exception(e)

# Minimal footer
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding: 1rem; color: #333;">
    <p style="font-family: 'JetBrains Mono'; font-size: 0.7rem; letter-spacing: 2px;">AION OS v1.0</p>
</div>
""", unsafe_allow_html=True)
