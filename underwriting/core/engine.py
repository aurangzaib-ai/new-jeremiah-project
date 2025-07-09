# Update the underwriting engine to support custom rules files and prompt templates

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

from .models import Applicant, Driver, Vehicle, Violation, Claim, UnderwritingResult, UnderwritingDecision

class UnderwritingEngine:
    """Enhanced underwriting engine with A/B testing support."""
    
    def __init__(self, rules_file: str = "underwriting_rules_standard.json", prompt_template: Optional[PromptTemplate] = None):
        """Initialize the underwriting engine with configurable rules and prompts."""
        
        # Load underwriting rules from specified JSON file
        self.rules_file = ".\\config\\rules\\" + rules_file
        self.rules = self._load_rules()
        #print(f"Loaded underwriting rules from {self.rules_file}")

        # Initialize OpenAI client (lazy initialization to avoid API key issues during config listing)
        self.llm = None
        
        # Set prompt template
        if prompt_template:
            self.prompt_template = prompt_template
        else:
            self.prompt_template = self._create_default_prompt_template()
    
    def _load_rules(self) -> Dict[str, Any]:
        """Load underwriting rules from JSON file."""
        
        try:
            with open(self.rules_file, 'r') as f:
                data = json.load(f)
                return data.get('underwriting_rules', {})
        except FileNotFoundError:
            raise FileNotFoundError(f"Rules file not found: {self.rules_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in rules file {self.rules_file}: {e}")
    
    def _create_default_prompt_template(self) -> PromptTemplate:
        """Create the default balanced prompt template."""
        
        template = """You are an expert automobile insurance underwriter. Your task is to evaluate an insurance applicant based on established underwriting rules and make one of three decisions: ACCEPT, DENY, or ADJUDICATE.

UNDERWRITING RULES:
{rules}

APPLICANT INFORMATION:
{applicant_data}

EVALUATION INSTRUCTIONS:
1. Carefully review the applicant's information against the underwriting rules
2. Check for any HARD STOPS that would result in automatic DENIAL
3. Check for any conditions that require ADJUDICATION (manual review)
4. If no hard stops or adjudication triggers apply, evaluate for ACCEPTANCE
5. Provide your decision with clear reasoning

DECISION CRITERIA:
- DENY: If any hard stop criteria are met (invalid license, multiple DUI, excessive claims, fraud history, extended coverage lapse)
- ADJUDICATE: If moderate risk factors require manual review (moderate violations, single major violation, young driver with violations, high-performance vehicle, poor credit, short coverage lapse)
- ACCEPT: If applicant meets acceptance criteria (clean record, minimal issues within acceptable limits)

RESPONSE FORMAT:
Decision: [ACCEPT/DENY/ADJUDICATE]
Primary Reason: [Brief explanation of the main factor driving the decision]
Triggered Rules: [List specific rule IDs that influenced the decision]
Risk Factors: [List key risk factors identified]
Additional Notes: [Any other relevant observations]

Please evaluate the applicant now:"""

        return PromptTemplate(
            input_variables=["rules", "applicant_data"],
            template=template
        )
    
    def _format_applicant_data(self, applicant: Applicant) -> str:
        """Format applicant data for the prompt."""
        
        # Primary driver info
        driver = applicant.primary_driver
        driver_info = f"""
PRIMARY DRIVER:
- Name: {driver.first_name} {driver.last_name}
- Age: {driver.age}
- License Status: {driver.license_status}
- License State: {driver.license_state}
- Years Licensed: {driver.years_licensed}"""
        
        # Violations
        violations_info = ""
        if driver.violations:
            violations_info = "\nVIOLATIONS:"
            for violation in driver.violations:
                years_ago = (datetime.now().date() - violation.date).days // 365
                violations_info += f"\n- {violation.violation_type} ({years_ago} years ago)"
        else:
            violations_info = "\nVIOLATIONS: None"
        
        # Claims
        claims_info = ""
        if driver.claims:
            claims_info = "\nCLAIMS HISTORY:"
            for claim in driver.claims:
                years_ago = (datetime.now().date() - claim.date).days // 365
                claims_info += f"\n- {claim.claim_type}: ${claim.amount:,} ({years_ago} years ago)"
        else:
            claims_info = "\nCLAIMS HISTORY: None"
        
        # Vehicles
        vehicles_info = "\nVEHICLES:"
        for vehicle in applicant.vehicles:
            vehicles_info += f"\n- {vehicle.year} {vehicle.make} {vehicle.model} ({vehicle.vehicle_type})"
        
        # Other info
        other_info = f"""
CREDIT SCORE: {applicant.credit_score}
COVERAGE LAPSE: {applicant.prior_insurance_lapse_days} days
TERRITORY: {applicant.territory}
REQUESTED COVERAGE: {applicant.coverage_requested}"""
        
        return driver_info + violations_info + claims_info + vehicles_info + other_info
    
    def _format_rules(self) -> str:
        """Format rules for the prompt."""
        
        rules_text = ""
        
        # Hard stops
        if 'hard_stops' in self.rules:
            rules_text += "HARD STOPS (Automatic Denial):\n"
            for rule in self.rules['hard_stops'].get('rules', []):
                rules_text += f"- {rule['rule_id']}: {rule['name']} - {rule['description']}\n"
        
        # Adjudication triggers
        if 'adjudication_triggers' in self.rules:
            rules_text += "\nADJUDICATION TRIGGERS (Manual Review Required):\n"
            for rule in self.rules['adjudication_triggers'].get('rules', []):
                rules_text += f"- {rule['rule_id']}: {rule['name']} - {rule['description']}\n"
        
        # Acceptance criteria
        if 'acceptance_criteria' in self.rules:
            rules_text += "\nACCEPTANCE CRITERIA (Automatic Approval):\n"
            for rule in self.rules['acceptance_criteria'].get('rules', []):
                rules_text += f"- {rule['rule_id']}: {rule['name']} - {rule['description']}\n"
        
        return rules_text
    
    def _parse_llm_response(self, response_text: str, applicant_id: str) -> UnderwritingResult:
        """Parse the LLM response into an UnderwritingResult."""
        
        lines = response_text.strip().split('\n')
        
        # Initialize default values
        decision = UnderwritingDecision.ADJUDICATE
        reason = "Unable to parse LLM response"
        triggered_rules = []
        risk_factors = []
        
        # Parse response
        for line in lines:
            line = line.strip()
            
            if line.startswith('Decision:'):
                decision_text = line.split(':', 1)[1].strip().upper()
                if 'ACCEPT' in decision_text:
                    decision = UnderwritingDecision.ACCEPT
                elif 'DENY' in decision_text:
                    decision = UnderwritingDecision.DENY
                elif 'ADJUDICATE' in decision_text:
                    decision = UnderwritingDecision.ADJUDICATE
            
            elif line.startswith('Primary Reason:'):
                reason = line.split(':', 1)[1].strip()
            
            elif line.startswith('Triggered Rules:'):
                rules_text = line.split(':', 1)[1].strip()
                if rules_text and rules_text != 'None':
                    triggered_rules = [r.strip() for r in rules_text.split(',')]
            
            elif line.startswith('Risk Factors:'):
                factors_text = line.split(':', 1)[1].strip()
                if factors_text and factors_text != 'None':
                    risk_factors = [f.strip() for f in factors_text.split(',')]
        
        return UnderwritingResult(
            applicant_id=applicant_id,
            decision=decision,
            reason=reason,
            triggered_rules=triggered_rules,
            risk_factors=risk_factors,
            timestamp=datetime.now()
        )
    
    def _get_llm(self):
        """Get LLM client with lazy initialization."""
        if self.llm is None:
            self.llm = ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                max_tokens=1000,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
        return self.llm
    
    def evaluate_applicant(self, applicant: Applicant) -> UnderwritingResult:
        """Evaluate an applicant using the LLM and return the result."""
        
        try:
            # Format data for prompt
            rules_text = self._format_rules()
            applicant_data = self._format_applicant_data(applicant)
            
            # Create prompt
            prompt = self.prompt_template.format(
                rules=rules_text,
                applicant_data=applicant_data
            )
            
            # Call LLM
            llm = self._get_llm()
            response = llm.invoke([HumanMessage(content=prompt)])
            response_text = response.content
            
            # Parse response
            result = self._parse_llm_response(response_text, applicant.applicant_id)
            
            return result
            
        except Exception as e:
            # Return error result
            return UnderwritingResult(
                applicant_id=applicant.applicant_id,
                decision=UnderwritingDecision.ADJUDICATE,
                reason=f"System error: {str(e)}",
                triggered_rules=[],
                risk_factors=["System Error"],
                timestamp=datetime.now()
            )

