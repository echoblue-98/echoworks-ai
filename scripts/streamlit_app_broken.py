"""
AION OS - Streamlit Web Dashboard

Professional web interface for adversarial analysis.
Quick to build (1 day), good enough for demos and first 50 customers.
"""

import streamlit as st
import sys
from pathlib import Path
import json
from datetime import datetime

# Add aionos to path
sys.path.insert(0, str(Path(__file__).parent))

from aionos.modules.legal_analyzer import LegalAnalyzer
from aionos.modules.security_redteam import SecurityRedTeam
from aionos.modules.attorney_departure import AttorneyDepartureAnalyzer
from aionos.modules.report_generator import (
    generate_legal_report,
    generate_security_report,
    generate_attorney_departure_report
)
from aionos.core.usage_tracker import UsageTracker

# Page config
st.set_page_config(
    page_title="AION OS - Adversarial Intelligence",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Enhanced Visuals
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: white;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    
    /* Header Styles */
    .main-header {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        font-family: 'Inter', sans-serif;
        letter-spacing: -2px;
    }
    
    .sub-header {
        font-size: 1.3rem;
        color: #6c757d;
        text-align: center;
        margin-bottom: 2.5rem;
        font-weight: 300;
        font-family: 'Inter', sans-serif;
    }
    
    /* Card Styles */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    /* Severity Badges */
    .severity-badge {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        margin-right: 0.5rem;
    }
    
    .critical {
        background: linear-gradient(135deg, #eb3941 0%, #f15e64 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(235, 57, 65, 0.4);
    }
    
    .high {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
    }
    
    .medium {
        background: linear-gradient(135deg, #ffa751 0%, #ffe259 100%);
        color: #333;
        box-shadow: 0 4px 15px rgba(255, 167, 81, 0.4);
    }
    
    .low {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        color: #333;
        box-shadow: 0 4px 15px rgba(67, 233, 123, 0.4);
    }
    
    .success {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
    }
    
    /* Button Styles */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
    }
    
    /* Metric Styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 10px;
        padding: 0 2rem;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 10px;
        border-left: 5px solid #667eea;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 10px;
        font-weight: 600;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Text input */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
    }
    
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header"> AION OS</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Adversarial Intelligence & Optimization System</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: white; font-size: 2.5rem; margin-bottom: 0;'></h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: white; font-weight: 700; margin-top: 0;'>AION OS</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.8); font-size: 0.9rem;'>Adversarial Intelligence</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    analysis_type = st.selectbox(
        "🎯 Analysis Type",
        ["Legal Analysis", "Security Red Team", "Attorney Departure Risk"],
        help="Select the type of adversarial analysis"
    )
    
    st.markdown("---")
    
    # Usage statistics
    st.subheader("📊 Usage Statistics")
    try:
        tracker = UsageTracker()
        metrics = tracker.get_metrics()
        
        st.metric("Budget Used", f"\\${metrics['total_cost']:.2f}")
        st.metric("Budget Remaining", f"\\${metrics['budget_remaining']:.2f}")
        st.metric("Analyses Run", metrics['total_calls'])
        
        if metrics['total_cost'] > 0:
            budget_pct = (metrics['total_cost'] / (metrics['total_cost'] + metrics['budget_remaining'])) * 100
            st.progress(budget_pct / 100)
            st.caption(f"{budget_pct:.1f}% of budget used")
    except Exception as e:
        st.error(f"Could not load usage stats: {str(e)}")
    
    st.markdown("---")
    st.caption("v0.1.0 | Powered by Claude Sonnet 4")

# Main content area
if analysis_type == "Legal Analysis":
    st.header("⚖️ Legal Analysis")
    st.markdown("Upload a legal brief, contract, or argument for adversarial analysis.")
    
    tab1, tab2, tab3 = st.tabs(["📄 Brief Analysis", "📋 Contract Review", "🎯 Quick Analysis"])
    
    with tab1:
        st.subheader("Analyze Legal Brief")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Upload legal brief (TXT, DOC, DOCX, PDF)",
                type=["txt", "doc", "docx", "pdf"],
                key="brief_upload"
            )
            
            brief_text = st.text_area(
                "Or paste brief text here:",
                height=300,
                placeholder="Paste your legal brief, motion, or argument here...",
                key="brief_text"
            )
        
        with col2:
            st.markdown("**Context (Optional)**")
            jurisdiction = st.text_input("Jurisdiction", placeholder="e.g., 9th Circuit")
            case_type = st.text_input("Case Type", placeholder="e.g., Civil Rights")
            
            intensity = st.slider("Adversarial Intensity", 1, 5, 3,
                                help="Higher = more aggressive attack")
        
        if st.button("🚀 Analyze Brief", type="primary", use_container_width=True):
            content = brief_text
            if uploaded_file:
                content = uploaded_file.read().decode("utf-8")
            
            if not content:
                st.error("Please provide brief text or upload a file.")
            else:
                with st.spinner("Running adversarial analysis... (5 agents attacking your brief)"):
                    try:
                        analyzer = LegalAnalyzer()
                        result = analyzer.analyze_brief(
                            content,
                            case_context={
                                "jurisdiction": jurisdiction,
                                "case_type": case_type
                            }
                        )
                        
                        st.success("✅ Analysis Complete!")
                        
                        # Display results with enhanced styling
                        st.markdown("<br>", unsafe_allow_html=True)
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f"""
                            <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);'>
                                <h3 style='color: white; margin: 0; font-size: 2.5rem;'>{len(result.get('agents_used', []))}</h3>
                                <p style='color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;'>Agents Used</p>
                            </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            vuln_count = len(result.get('vulnerabilities', []))
                            st.markdown(f"""
                            <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 15px; box-shadow: 0 10px 30px rgba(245, 87, 108, 0.3);'>
                                <h3 style='color: white; margin: 0; font-size: 2.5rem;'>{vuln_count}</h3>
                                <p style='color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;'>Vulnerabilities Found</p>
                            </div>
                            """, unsafe_allow_html=True)
                        with col3:
                            cost = result.get('cost', 0)
                            cost_display = f"${cost:.4f}"
                            st.markdown(f"""
                            <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); border-radius: 15px; box-shadow: 0 10px 30px rgba(17, 153, 142, 0.3);'>
                                <h3 style='color: white; margin: 0; font-size: 2.5rem;'>{cost_display}</h3>
                                <p style='color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;'>Analysis Cost</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("### 🔍 Findings")
                        
                        for vuln in result['vulnerabilities']:
                            severity = vuln.get('severity', 'medium').lower()
                            severity_emoji = {
                                'critical': '🔴',
                                'high': '🟠',
                                'medium': '🟡',
                                'low': '🟢'
                            }.get(severity, '⚪')
                            
                            with st.expander(f"{severity_emoji} {vuln.get('title', 'Finding')} ({severity.upper()})"):
                                st.markdown(f"**Description:** {vuln.get('description', 'N/A')}")
                                if 'impact' in vuln:
                                    st.markdown(f"**Impact:** {vuln['impact']}")
                                if 'remediation' in vuln:
                                    st.markdown(f"**Remediation:** {vuln['remediation']}")
                        
                        # Generate PDF
                        st.markdown("---")
                        if st.button("📄 Generate PDF Report", use_container_width=True):
                            with st.spinner("Generating professional PDF report..."):
                                report_path = generate_legal_report(
                                    result,
                                    output_path=f"reports/legal_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                    customer_name="Demo Customer",
                                    project_name="Legal Brief Analysis"
                                )
                                
                                with open(report_path, "rb") as f:
                                    st.download_button(
                                        "⬇️ Download PDF Report",
                                        data=f,
                                        file_name=Path(report_path).name,
                                        mime="application/pdf",
                                        use_container_width=True
                                    )
                    
                    except Exception as e:
                        st.error(f"❌ Analysis failed: {str(e)}")
                        st.exception(e)
    
    with tab2:
        st.subheader("Contract Vulnerability Analysis")
        st.info("Upload a contract to identify hidden vulnerabilities and one-sided terms.")
        
        contract_text = st.text_area(
            "Paste contract text:",
            height=300,
            placeholder="Paste contract text here...",
            key="contract_text"
        )
        
        party = st.selectbox("Your Position", ["buyer", "seller", "licensor", "licensee"])
        
        if st.button("🔍 Analyze Contract", type="primary"):
            if contract_text:
                with st.spinner("Analyzing contract for vulnerabilities..."):
                    analyzer = LegalAnalyzer()
                    result = analyzer.analyze_contract(contract_text, party_position=party)
                    
                    st.json(result)
    
    with tab3:
        st.subheader("Quick Argument Analysis")
        st.info("Test a legal argument or reasoning chain for logical flaws.")
        
        argument = st.text_area(
            "Enter your argument:",
            height=200,
            placeholder="Enter the legal argument or reasoning you want to test...",
            key="argument_text"
        )
        
        if st.button(" Quick Analysis", type="primary"):
            if argument:
                with st.spinner("Analyzing argument..."):
                    analyzer = LegalAnalyzer()
                    result = analyzer.analyze_argument_chain(argument)
                    st.json(result)

elif analysis_type == "Security Red Team":
    st.header("🛡️ Security Red Team")
    st.markdown("Adversarial security assessment of infrastructure, systems, and defenses.")
    
    tab1, tab2 = st.tabs(["🌐 Infrastructure Scan", "🎯 Attack Simulation"])
    
    with tab1:
        st.subheader("Infrastructure Security Assessment")
        
        infra_text = st.text_area(
            "Describe your infrastructure:",
            height=300,
            placeholder="""Example:
- AWS cloud environment
- 50 EC2 instances running web apps
- RDS PostgreSQL databases
- S3 buckets for file storage
- VPN access for remote workers
- No WAF currently deployed
            """,
            key="infra_text"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            scope = st.multiselect(
                "Assessment Scope",
                ["Network", "Applications", "Data", "Access Control", "Cloud Config"],
                default=["Network", "Applications"]
            )
        with col2: with enhanced cards
                        st.markdown("<br>", unsafe_allow_html=True)
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            vuln_count = len(result.get('vulnerabilities', []))
                            st.markdown(f"""
                            <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);'>
                                <h3 style='color: white; margin: 0; font-size: 2.5rem;'>{vuln_count}</h3>
                                <p style='color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;'>Vulnerabilities</p>
                            </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            critical = len([v for v in result.get('vulnerabilities', []) 
                                          if v.get('severity') == 'critical'])
                            st.markdown(f"""
                            <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #eb3941 0%, #f15e64 100%); border-radius: 15px; box-shadow: 0 10px 30px rgba(235, 57, 65, 0.3);'>
                                <h3 style='color: white; margin: 0; font-size: 2.5rem;'>{critical}</h3>
                                <p style='color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;'>Critical Issues</p>
                            </div>
                            """, unsafe_allow_html=True)
                        with col3:
                            cost = result.get('cost', 0)
                            cost_display = f"\\${cost:.4f}"
                            st.markdown(f"""
                            <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); border-radius: 15px; box-shadow: 0 10px 30px rgba(17, 153, 142, 0.3);'>
                                <h3 style='color: white; margin: 0; font-size: 2.5rem;'>{cost_display}</h3>
                                <p style='color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;'>Assessment Cost</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Display vulnerabilities
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("### 🔍 Security Findings")
                        
                        for vuln in result['vulnerabilities']:
                            severity = vuln.get('severity', 'medium')
                            severity_emoji = {
                                'critical': '🔴',
                                'high': '🟠',
                                'medium': '🟡',
                                'low': '🟢'
                            }.get(severity, '⚪')
                            
                            with st.expander(f"{severity_emoji} {vuln.get('title', 'Finding')} ({severity.upper()})"):
                                st.markdown(f"**Description:** {vuln.get('description', 'N/A')}")
                                if 'impact' in vuln:
                                    st.markdown(f"**Impact:** {vuln['impact']}")
                                if 'remediation' in vuln:
                                    st.markdown(f"**Remediation:** {vuln['remediation']}")
                        
                        # PDF generation
                            st.markdown(f"""
                            <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); border-radius: 15px; box-shadow: 0 10px 30px rgba(17, 153, 142, 0.3);'>
                                <h3 style='color: white; margin: 0; font-size: 2.5rem;'>{cost_display}</h3>
                                <p style='color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;'>Assessment Cost</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Display vulnerabilities
                        if result.get('vulnerabilities'):
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown("### 🔍 Security Findings")
                            
                            for vuln in result['vulnerabilities']:
                                severity = vuln.get('severity', 'medium')
                                emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(severity, '⚪')
                                
                                with st.expander(f"{emoji} {vuln.get('title', 'Finding')} ({severity.upper()})"):
                                    st.markdown(f"**Description:** {vuln.get('description', 'N/A')}")
                                    if 'impact' in vuln:
                                        st.markdown(f"**Impact:** {vuln['impact']}")
                                    if 'remediation' in vuln:
                                        st.markdown(f"**Remediation:** {vuln['remediation']}")
                        
                        # PDF generation
                        st.markdown("---")
                        if st.button("📄 Generate Security Report", use_container_width=True):
                            with st.spinner("Generating report..."):
                                report_path = generate_security_report(
                                    result,
                                    output_path=f"reports/security_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                )
                                with open(report_path, "rb") as f:
                                    st.download_button(
                                        "⬇️ Download Security Report",
                                        data=f,
                                        file_name=Path(report_path).name,
                                        mime="application/pdf"
                                    )
                    
                    except Exception as e:
                        st.error(f"❌ Assessment failed: {str(e)}")
            if target:
                st.warning("Simulating attack chain...")
                redteam = SecurityRedTeam()
                result = redteam.simulate_attack_chain(f"Target: {target}, Initial: {attack_vector}")
            st.subheader("Attack Chain Simulation")
        st.info("Simulate how an attacker would chain vulnerabilities together.")
        
        target = st.text_input("Target Description", placeholder="e.g., Corporate network")
        attack_vector = st.selectbox("Initial Access Vector", 
                                     ["Phishing", "Exposed Service", "Supply Chain", "Insider"])
        
        if st.button(" Simulate Attack", type="primary"):
            st.warning("Simulating attack chain...")
            redteam = SecurityRedTeam()
            result = redteam.simulate_attack_chain(f"Target: {target}, Initial: {attack_vector}")
            st.json(result)

else:  # Attorney Departure Risk
    st.header("👔 Attorney Departure Risk Analysis")
    st.markdown("Analyze vulnerabilities when a key attorney leaves the firm.")
    
    st.subheader("Attorney Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        attorney_name = st.text_input("Attorney Name", placeholder="John Doe")
        practice_area = st.text_input("Practice Area", placeholder="Corporate M&A")
        years_at_firm = st.number_input("Years at Firm", min_value=0, max_value=50, value=5)
    
    with col2:
        title = st.selectbox("Title", ["Associate", "Senior Associate", "Partner", "Senior Partner"])
        departure_date = st.date_input("Departure Date")
        is_voluntary = st.checkbox("Voluntary Departure", value=True)
    
    st.subheader("Active Matters")
    active_cases = st.text_area(
        "List active cases/matters:",
        height=150,
        placeholder="Example:\n- Acme Corp Acquisition (50M deal, closing in 30 days)\n- Smith v. Jones litigation (trial in 60 days)\n- Tech Startup Series B (in negotiation)",
        key="cases_text"
    )
    
    client_relationships = st.text_area(
        "Key client relationships:",
        height=100,
        placeholder="List key clients this attorney brought in or manages...",
        key="clients_text"
    )
    
    if st.button("🚀 Analyze Departure Risk", type="primary", use_container_width=True):
        if not attorney_name:
            s
            with st.spinner("Analyzing departure risk..."):
                try:
                    analyzer = AttorneyDepartureAnalyzer()
                    result = analyzer.analyze_departure(
                        attorney_name=attorney_name,
                        practice_area=practice_area,
                        active_cases=active_cases,
                        client_relationships=client_relationships,
                        years_at_firm=years_at_firm,
                        departure_context={
                            "title": title,
                            "departure_date": str(departure_date),
                            "is_voluntary": is_voluntary
                        }
                    )
                    
                    # Display resultst.error("Please provide attorney name")
        else: with enhanced cards
                    risk_score = result.get('overall_risk_score', 0)
                    st.markdown("<br>", unsafe_allow_html=True)
                    col1, col2, col3 = st.columns(3)
                    with col3:
                        cost = result.get('cost', 0)
                        cost_display = f"${cost:.4f}"
                        st.markdown(f"""
                        <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); border-radius: 15px; box-shadow: 0 10px 30px rgba(17, 153, 142, 0.3);'>
                            <h3 style='color: white; margin: 0; font-size: 2.5rem;'>{cost_display}</h3>
                            <p style='color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;'>Analysis Cost</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("### 🔍 Identified Vulnerabilities")
                    
                    if result.get('vulnerabilities'):
core > 40 else 'Low'} Risk")
                    with col2:
                        st.metric("Active Cases at Risk", len(result.get('cases_at_risk', [])))
                    with col3:
                        st.metric("Critical Actions", len([a for a in result.get('action_items', []) 
                                                          if a.get('priority') == 'P0']))
                    
                    # Risk categories
                    st.markdown("---")
                    st.subheader("📊 Risk Breakdown")
                    
                    risk_categories = result.get('risk_categories', {})
                    for category, score in risk_categories.items():
                        st.progress(score / 100)
                        st.caption(f"{category.replace('_', ' ').title()}: {score}/100")
                    
                    # Vulnerabilities
                    if result.get('vulnerabilities'):
                        st.markdown("---")
                        st.subheader("🔍 Identified Vulnerabilities")
                        
                        for vuln in result['vulnerabilities']:
                            severity = vuln.get('severity', 'P3')
                            emoji = {'P0': '🔴', 'P1': '🟠', 'P2': '🟡', 'P3': '🟢', 'P4': '⚪'}.get(severity, '⚪')
                            
                            with st.expander(f"{emoji} {vuln.get('title', 'Vulnerability')} ({severity})"):
                                st.markdown(vuln.get('description', ''))
                                if 'remediation' in vuln:
                                    st.markdown(f"**Remediation:** {vuln['remediation']}")
                    
                    # PDF Report
                    st.markdown("---")
                    if st.button("📄 Generate Departure Report", use_container_width=True):
                        with st.spinner("Generating report..."):
                            report_path = generate_attorney_departure_report(
                                result,
                                output_path=f"reports/departure_{attorney_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                customer_name="Demo Law Firm",
                                project_name=f"Departure Risk: {attorney_name}"
                            )
                            with open(report_path, "rb") as f:
                                st.download_button(
                                    "⬇️ Download Report",
                                    data=f,
                                    file_name=Path(report_path).name,
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                
                except Exception as e:
                    st.error(f"❌ Analysis failed: {str(e)}")
                    st.exception(e)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; color: #6c757d; font-size: 0.9rem;'>
    <p style='margin: 0;'><strong>AION OS</strong> v0.1.0 | Powered by Claude Sonnet 4</p>
    <p style='margin: 0.5rem 0 0 0; font-size: 0.8rem;'>&copy; 2025 All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🔴 AION OS v0.1.0")
with col2:
    st.caption("Powered by Claude Sonnet 4")
with col3:
    st.caption("&copy; 2025 All Rights Reserved")


