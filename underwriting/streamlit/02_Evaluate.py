
"""
Applicant evaluation page for the Streamlit underwriting application.

This page provides an interactive form for evaluating insurance applicants
with real-time feedback and AI-powered decision making.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Optional
import json
import random

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from underwriting.core.models import (
    Applicant, Driver, Vehicle, Violation, Claim,
    LicenseStatus, ViolationType, ClaimType, VehicleCategory,
    UnderwritingDecision
)
from underwriting.core.engine import UnderwritingEngine
from underwriting.data.sample_generator import create_sample_applicants
from underwriting.utils.env_loader import load_environment_variables

def configure_page():
    """Configure the page settings."""
    st.set_page_config(
        page_title="Evaluate Applicant - Underwriting System",
        page_icon="",
        layout="wide"
    )

def load_custom_css():
    """Load custom CSS for the evaluation page."""
    st.markdown("""
    <style>
    .evaluation-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .form-section {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
        border-left: 4px solid #1f77b4;
    }
    
    .result-card {
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 600;
        font-size: 1.2rem;
    }
    
    .result-accept {
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        color: #155724;
        border: 2px solid #28a745;
    }
    
    .result-deny {
        background: linear-gradient(135deg, #f8d7da, #f5c6cb);
        color: #721c24;
        border: 2px solid #dc3545;
    }
    
    .result-adjudicate {
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        color: #856404;
        border: 2px solid #ffc107;
    }
    
    .risk-indicator {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        margin: 0.25rem;
    }
    
    .risk-low { background-color: #d4edda; color: #155724; }
    .risk-medium { background-color: #fff3cd; color: #856404; }
    .risk-high { background-color: #f8d7da; color: #721c24; }
    </style>
    """, unsafe_allow_html=True)


def generate_random_id():
    """Generate a random 5-digit numerical ID as a string."""
    return f"{random.randint(10000, 99999)}"

def create_applicant_form():
    """Create the interactive applicant evaluation form."""
    st.markdown("""
    <div class="evaluation-header">
        <h1> Applicant Evaluation</h1>
        <p>AI-Powered Insurance Underwriting Assessment</p>
        <p>(WIP) Portfolio Project managed by <a href="https://jeremiahconnelly.dev" target="_blank">Jeremiah Connelly</a></p>   
    </div>
    """, unsafe_allow_html=True)
    
    # Sample applicant selector
    st.markdown("###  Quick Start Options")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        sample_option = st.selectbox(
            "Load Sample Applicant",
            ["Create New Application", 
             "Sample 1: Clean Record (Accept)", 
             "Sample 2: Good Driver (Accept)", 
             "Sample 3: Multiple DUIs (Deny)",
             "Sample 4: Coverage Lapse (Deny)", 
             "Sample 5: Young Driver (Adjudicate)",
             "Sample 6: Single Violation (Adjudicate)"
             ],
            help="Select a pre-configured applicant for testing"
        )
    
    with col2:
        if st.button(" Load Sample", use_container_width=True):
            if sample_option != "Create New Application":
                sampleOptionData = sample_option.split()[1]
                sampleOptionData = sampleOptionData.replace(":", "")
                sample_idx = int(sampleOptionData) - 1
                samples = create_sample_applicants()
                if sample_idx < len(samples):
                    print("Loading sample applicant: ", samples[sample_idx].primary_driver.first_name)
                    st.session_state.sample_applicant = samples[sample_idx]
                    st.rerun()
    
    # Main form
    with st.form("applicant_form"):
        # Personal Information Section
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown("#### 👤 Personal Information")
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        if 'sample_applicant' in st.session_state:
            sample_applicant = st.session_state.sample_applicant
            first_name = sample_applicant.primary_driver.first_name
            last_name = sample_applicant.primary_driver.last_name
            age = sample_applicant.primary_driver.age
            license_status = sample_applicant.primary_driver.license_status.value
            years_licensed = sample_applicant.primary_driver.years_licensed
            email = sample_applicant.primary_driver.email
            driver_id = sample_applicant.primary_driver.id
            date_of_birth = sample_applicant.primary_driver.date_of_birth
            license_number = sample_applicant.primary_driver.license_number
            license_state = sample_applicant.primary_driver.license_state
            license_issue_date = sample_applicant.primary_driver.license_issue_date
            license_expiration_date = sample_applicant.primary_driver.license_expiration_date
        else:
            first_name = "John"
            last_name = "Doe"
            age = 35
            license_status = LicenseStatus.VALID.value
            years_licensed = 15
            email = "john.doe@email.com"
            driver_id = "DRIVER_12345"
            date_of_birth = date(1988, 1, 1)
            license_number = "LIC_123456789"
            license_state = "CA"
            license_issue_date = date(2010, 1, 1)
            license_expiration_date = date(2025, 1, 1)

        with col1:

            first_name = st.text_input("First Name", value=first_name)
            age = st.number_input("Age", min_value=16, max_value=100, value=age)
        
        with col2:
            last_name = st.text_input("Last Name", value=last_name)
            license_status = st.selectbox("License Status", 
                                        [status.value for status in LicenseStatus],
                                        index=0)
        
        with col3:
            email = st.text_input("Email", value=email)
            years_licensed = st.number_input("Years Licensed", min_value=0, max_value=50, value=years_licensed)
        
        with col4:
            driver_id = st.text_input("ID", value=driver_id)
            date_of_birth = st.date_input("Date of Birth", value=date_of_birth)

        with col5:
            license_number = st.text_input("License Number", value=license_number)
            license_state = st.text_input("License State", value=license_state)

        with col6:
            license_issue_date = st.date_input("License Issue Date", value=license_issue_date)
            license_expiration_date = st.date_input("License Expiration Date", value=license_expiration_date)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Financial Information Section
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown("####  Financial Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            credit_score = st.slider("Credit Score", min_value=300, max_value=850, value=720,
                                    help="Credit score range: 300-850")
            
            # Credit score indicator
            if credit_score >= 750:
                st.success(" Excellent Credit")
            elif credit_score >= 700:
                st.info(" Good Credit")
            elif credit_score >= 650:
                st.warning(" Fair Credit")
            else:
                st.error(" Poor Credit")
        
        with col2:
            annual_income = st.number_input("Annual Income ($)", min_value=0, value=75000, step=1000)
            employment_status = st.selectbox("Employment Status", 
                                           ["Employed", "Self-Employed", "Unemployed", "Retired", "Student"])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Coverage Information Section
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown("####  Coverage Information")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            coverage_requested = st.multiselect("Coverage Types",
                                              ["Liability", "Collision", "Comprehensive", "Uninsured Motorist"],
                                              default=["Liability", "Collision"])
        
        with col2:
            previous_coverage = st.checkbox("Had Previous Coverage", value=True)
            if previous_coverage:
                prior_insurance_lapse_days = st.number_input("Days Since Last Coverage", min_value=0, value=0)
            else:
                prior_insurance_lapse_days = 365  # Assume 1 year lapse if no previous coverage
        
        with col3:
            policy_term = st.selectbox("Policy Term", ["6 months", "12 months"], index=1)
            payment_method = st.selectbox("Payment Method", ["Monthly", "Quarterly", "Semi-Annual", "Annual"])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Vehicle Information Section
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown("####  Vehicle Information")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            vehicle_year = st.number_input("Year", min_value=1990, max_value=2025, value=2020)
            vehicle_make = st.text_input("Make", value="Toyota")
        
        with col2:
            vehicle_model = st.text_input("Model", value="Camry")
            vehicle_value = st.number_input("Vehicle Value ($)", min_value=0, value=25000, step=1000)
        
        with col3:
            vehicle_category = st.selectbox("Category", 
                                          [cat.value for cat in VehicleCategory],
                                          index=0)
            annual_mileage = st.number_input("Annual Mileage", min_value=0, value=12000, step=1000)
        
        with col4:
            vehicle_use = st.selectbox("Primary Use", ["Personal", "Business", "Commuting", "Pleasure"])
            garage_type = st.selectbox("Garage Type", ["Garage", "Carport", "Street", "Driveway"])
        
        with col5:
            vin = st.text_input("VIN", value="1HGBH41JXMN109186")

        st.markdown('</div>', unsafe_allow_html=True)
        
        # Driving History Section
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown("####  Driving History")
        
        # Violations
        st.markdown("**Traffic Violations (Last 5 Years)**")
        num_violations = st.number_input("Number of Violations", min_value=0, max_value=10, value=0)
        
        violations = []
        if num_violations > 0:
            for i in range(num_violations):
                col1, col2, col3 = st.columns(3)
                with col1:
                    violation_type = st.selectbox(f"Violation {i+1} Type", 
                                                [vtype.value for vtype in ViolationType],
                                                key=f"violation_type_{i}")
                with col2:
                    violation_date = st.date_input(f"Violation {i+1} Date", 
                                                 value=date.today() - timedelta(days=365),
                                                 key=f"violation_date_{i}")
                with col3:
                    violation_fine = st.number_input(f"Fine Amount ($)", min_value=0, value=150,
                                                   key=f"violation_fine_{i}")
                
                violations.append(Violation(
                    type=ViolationType(violation_type),
                    date=violation_date,
                    description=f"{violation_type} violation",
                    fine_amount=violation_fine
                ))
        
        # Claims
        st.markdown("**Insurance Claims (Last 5 Years)**")
        num_claims = st.number_input("Number of Claims", min_value=0, max_value=10, value=0)
        
        claims = []
        if num_claims > 0:
            for i in range(num_claims):
                col1, col2, col3 = st.columns(3)
                with col1:
                    claim_type = st.selectbox(f"Claim {i+1} Type",
                                            [ctype.value for ctype in ClaimType],
                                            key=f"claim_type_{i}")
                with col2:
                    claim_date = st.date_input(f"Claim {i+1} Date",
                                             value=date.today() - timedelta(days=365),
                                             key=f"claim_date_{i}")
                with col3:
                    claim_amount = st.number_input(f"Claim Amount ($)", min_value=0, value=5000,
                                                 key=f"claim_amount_{i}")
                
                claims.append(Claim(
                    type=ClaimType(claim_type),
                    date=claim_date,
                    amount=claim_amount,
                    description=f"{claim_type} claim"
                ))
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Submit button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(" Evaluate Applicant", 
                                            use_container_width=True, 
                                            type="primary")
        
        if submitted:
            # Create applicant object
            driver = Driver(
                first_name=first_name,
                last_name=last_name,
                age=age,
                license_status=LicenseStatus(license_status),
                years_licensed=years_licensed,
                violations=violations,
                driver_id=driver_id,
                date_of_birth=date_of_birth,
                license_number=license_number,
                license_state=license_state,
                license_issue_date=license_issue_date,
                license_expiration_date=license_expiration_date,
                claims=claims
            )
            
            vehicle = Vehicle(
                year=vehicle_year,
                make=vehicle_make,
                model=vehicle_model,
                category=VehicleCategory(vehicle_category),
                vehicle_type=VehicleCategory(vehicle_category),
                value=vehicle_value,
                annual_mileage=annual_mileage,
                vin = vin
            )
            
            applicant = Applicant(
                applicant_id="APP_" + generate_random_id(),
                primary_driver=driver,
                vehicles=[vehicle], 
                credit_score=credit_score,
                coverage_requested=coverage_requested,
                prior_insurance_lapse_days=prior_insurance_lapse_days,
                territory="Urban"
            )
            # Store in session state for evaluation
            st.session_state.current_applicant = applicant
            st.session_state.show_results = True
            st.rerun()

def show_evaluation_results():
    """Display the evaluation results."""
    if 'current_applicant' not in st.session_state:
        return
    
    applicant = st.session_state.current_applicant
    
    st.markdown("##  Evaluation Results")
    
    # Check for OpenAI API key
    import os
    import random
    if not os.environ.get('OPENAI_API_KEY'):
        st.error(" OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
        st.info("For testing purposes, showing mock evaluation results.")
        
        # Mock results for demonstration
        mock_decision = UnderwritingDecision.ACCEPT if applicant.credit_score > 700 else UnderwritingDecision.ADJUDICATE
        
        if mock_decision == UnderwritingDecision.ACCEPT:
            st.markdown("""
            <div class="result-card result-accept">
                APPLICATION ACCEPTED
            </div>
            """, unsafe_allow_html=True)
            st.success(" Congratulations! The application has been approved for coverage.")
        elif mock_decision == UnderwritingDecision.DENY:
            st.markdown("""
            <div class="result-card result-deny">
                 APPLICATION DENIED
            </div>
            """, unsafe_allow_html=True)
            st.error(" The application has been declined for coverage.")
        else:
            st.markdown("""
            <div class="result-card result-adjudicate">
                ⚖️ MANUAL REVIEW REQUIRED
            </div>
            """, unsafe_allow_html=True)
            st.warning("⚖️ The application requires manual underwriter review.")
        
        return
    
    # Real evaluation with AI
    try:
        with st.spinner(" AI is evaluating the application..."):
            engine = UnderwritingEngine()
            result = engine.evaluate_applicant(applicant)
        
        # Display results
        if result.decision == UnderwritingDecision.ACCEPT:
            st.markdown("""
            <div class="result-card result-accept">
                 APPLICATION ACCEPTED
            </div>
            """, unsafe_allow_html=True)
            st.success(" Congratulations! The application has been approved for coverage.")
        elif result.decision == UnderwritingDecision.DENY:
            st.markdown("""
            <div class="result-card result-deny">
                 APPLICATION DENIED
            </div>
            """, unsafe_allow_html=True)
            st.error(" The application has been declined for coverage.")
        else:
            st.markdown("""
            <div class="result-card result-adjudicate">
                 MANUAL REVIEW REQUIRED
            </div>
            """, unsafe_allow_html=True)
            st.warning(" The application requires manual underwriter review.")
        
        # Detailed analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("###  Application Summary")
            st.write(f"**Applicant:** {applicant.primary_driver.first_name} {applicant.primary_driver.last_name}")
            st.write(f"**Age:** {applicant.primary_driver.age}")
            st.write(f"**Credit Score:** {applicant.credit_score}")
            for idx, Vehicle in enumerate(applicant.vehicles):
                st.write(f"**Vehicle {idx+1}:** {Vehicle.year} {Vehicle.make} {Vehicle.model}")
            st.write(f"**Coverage Lapse:** {applicant.prior_insurance_lapse_days} days")
            st.write(f"**Violations:** {len(applicant.primary_driver.violations)}")
            st.write(f"**Claims:** {len(applicant.primary_driver.claims)}")
        
        with col2:
            st.markdown("###  AI Analysis")
            if result.reason:
                st.write(result.reason)
            else:
                st.write("Detailed AI analysis completed based on underwriting criteria.")
            
            # Risk indicators
            st.markdown("###  Risk Factors")
            
            # Credit score risk
            if applicant.credit_score >= 750:
                st.markdown('<span class="risk-indicator risk-low"> Excellent Credit</span>', unsafe_allow_html=True)
            elif applicant.credit_score >= 700:
                st.markdown('<span class="risk-indicator risk-medium"> Good Credit</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="risk-indicator risk-high"> Poor Credit</span>', unsafe_allow_html=True)
            
            # Coverage lapse risk
            if applicant.prior_insurance_lapse_days == 0:
                st.markdown('<span class="risk-indicator risk-low"> Continuous Coverage</span>', unsafe_allow_html=True)
            elif applicant.prior_insurance_lapse_days <= 30:
                st.markdown('<span class="risk-indicator risk-medium"> Short Lapse</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="risk-indicator risk-high"> Extended Lapse</span>', unsafe_allow_html=True)
            
            # Violations risk
            violation_count = len(applicant.primary_driver.violations)
            if violation_count == 0:
                st.markdown('<span class="risk-indicator risk-low"> Clean Record</span>', unsafe_allow_html=True)
            elif violation_count <= 2:
                st.markdown('<span class="risk-indicator risk-medium"> Minor Violations</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="risk-indicator risk-high"> Multiple Violations</span>', unsafe_allow_html=True)
        
        # Export results
        st.markdown("###  Export Results")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(" Copy to Clipboard", use_container_width=True):
                result_text = f"""
                    Underwriting Decision: {result.decision.value}
                    Applicant: {applicant.primary_driver.first_name} {applicant.primary_driver.last_name}
                    Credit Score: {applicant.credit_score}
                    Decision: {result.decision.value}
                    Reason: {result.reason or 'Standard underwriting evaluation'}
                """
                st.code(result_text)
        
        with col2:
            result_json = {
                "applicant_id": applicant.applicant_id,
                "decision": result.decision.value,
                "applicant_name": f"{applicant.primary_driver.first_name} {applicant.primary_driver.last_name}",
                "credit_score": applicant.credit_score,
                "reason": result.reason,
                "timestamp": datetime.now().isoformat()
            }
            
            st.download_button(
                " Download JSON",
                data=json.dumps(result_json, indent=2),
                file_name=f"underwriting_result_{applicant.applicant_id}.json",
                mime="application/json",
                use_container_width=True
            )
    
    except Exception as e:
        st.error(f" Error during evaluation: {str(e)}")
        st.info("Please check your OpenAI API key and try again.")

def main():
    """Main function for the evaluation page."""
    load_environment_variables()
    configure_page()
    load_custom_css()
    
    # Load sample applicant if requested
    if 'sample_applicant' in st.session_state:
        st.session_state.current_applicant = st.session_state.sample_applicant
        st.session_state.show_results = True
        del st.session_state.sample_applicant
    
    # Create the form
    create_applicant_form()
    
    # Show results if available
    if st.session_state.get('show_results', False):
        show_evaluation_results()
        
        # Reset button
        if st.button(" Evaluate Another Applicant", use_container_width=True):
            st.session_state.show_results = False
            if 'current_applicant' in st.session_state:
                del st.session_state.current_applicant
            st.rerun()

if __name__ == "__main__":
    main()

