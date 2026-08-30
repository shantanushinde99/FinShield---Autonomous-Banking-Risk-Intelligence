from finshield.models.domain import InvestigationContext
from finshield.models.agents import CustomerProfileAssessment

class CustomerProfileAgent:
    """
    Deterministically structures the customer's profile and identifies stability indicators.
    """
    
    def analyze(self, context: InvestigationContext) -> CustomerProfileAssessment:
        fc = context.financial_context
        profile = fc.profile
        
        stability_indicators = []
        observations = []
        completeness = "INCOMPLETE"
        
        if profile:
            if profile.employment_years and profile.employment_years > 2.0:
                stability_indicators.append(f"Stable employment history ({profile.employment_years:.1f} years)")
            elif profile.employment_years and profile.employment_years < 0:
                observations.append("Employment data anomaly (negative years)")
                
            if profile.owns_car == 'Y' or profile.owns_realty == 'Y':
                stability_indicators.append("Owns hard assets (car or real estate)")
                
            if profile.total_income and profile.total_income > 0:
                completeness = "HIGH" if profile.employment_years and profile.age else "MEDIUM"
            
            if profile.age and profile.age < 21:
                observations.append("Young demographic (under 21)")
                
        else:
            observations.append("No demographic profile available.")
            completeness = "LOW"
            
        return CustomerProfileAssessment(
            investigation_id=context.investigation_id,
            customer_id=fc.customer_id,
            age=profile.age if profile else None,
            employment_years=profile.employment_years if profile else None,
            total_income=profile.total_income if profile else None,
            occupation=profile.occupation if profile else None,
            financial_stability_indicators=stability_indicators,
            profile_observations=observations,
            data_completeness=completeness
        )
