import json
import os
import uuid
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

KB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tax_knowledge_base.json')

def load_knowledge_base():
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_obligation(obligation_id: str) -> dict:
    kb = load_knowledge_base()
    for jur, jur_data in kb.get('jurisdictions', {}).items():
        for ob in jur_data.get('obligations', []):
            if ob['id'] == obligation_id:
                ob['jurisdiction_name'] = jur_data.get('name', jur)
                return ob
    return {}

def calculate_priority(deadline_date: date, ref_date: date) -> str:
    days_until = (deadline_date - ref_date).days
    if days_until < 0:
        return "overdue"
    elif days_until <= 7:
        return "critical"
    elif days_until <= 30:
        return "high"
    elif days_until <= 60:
        return "medium"
    else:
        return "low"

def generate_compliance_plan(company_profile: dict, reference_date: date = None) -> dict:
    if reference_date is None:
        reference_date = datetime.now().date()
        
    kb = load_knowledge_base()
    jurisdictions = company_profile.get('jurisdictions', [])
    entity_types = company_profile.get('entity_types', {})
    
    actions = []
    
    for jur in jurisdictions:
        if jur not in kb['jurisdictions']:
            continue
            
        entity_type = entity_types.get(jur)
        if not entity_type:
            continue
            
        obs = kb['jurisdictions'][jur]['obligations']
        
        for ob in obs:
            if entity_type not in ob['applies_to']:
                continue
                
            freq = ob['frequency']
            deadlines = []
            
            if freq == 'annual':
                due_month = ob['due_month']
                due_day = ob['due_day']
                
                try:
                    target_date = date(reference_date.year, due_month, due_day)
                except ValueError:
                    target_date = date(reference_date.year, due_month, due_day - 1)  # Leap year fallback
                    
                if target_date < reference_date:
                    try:
                        target_date = date(reference_date.year + 1, due_month, due_day)
                    except ValueError:
                        target_date = date(reference_date.year + 1, due_month, due_day - 1)
                        
                deadlines.append(target_date)
                
            elif freq == 'quarterly':
                for q in ob.get('quarterly_dates', []):
                    target_date = date(reference_date.year, q['due_month'], q['due_day'])
                    if target_date < reference_date:
                        target_date = date(reference_date.year + 1, q['due_month'], q['due_day'])
                    deadlines.append(target_date)
                deadlines = sorted([d for d in deadlines if (d - reference_date).days <= 365])
                
            elif freq == 'monthly':
                for i in range(1, 4):
                    next_month = reference_date + relativedelta(months=i)
                    due_day = ob.get('due_day', 15)  # default to 15th if not specified
                    try:
                        target_date = date(next_month.year, next_month.month, due_day)
                    except ValueError:
                        target_date = date(next_month.year, next_month.month, due_day - 1)
                    deadlines.append(target_date)
            
            for d in deadlines:
                act = {
                    "id": str(uuid.uuid4()),
                    "company_id": company_profile.get("id"),
                    "obligation_id": ob['id'],
                    "obligation_name": ob['name'],
                    "jurisdiction": jur,
                    "deadline": d.isoformat(),
                    "prep_start_date": (d - timedelta(days=30)).isoformat(),
                    "status": "upcoming",
                    "priority": calculate_priority(d, reference_date),
                    "action_data": {
                        "form": ob.get("form"),
                        "output_type": ob.get("output_type"),
                        "tax_rate": ob.get("tax_rate")
                    }
                }
                actions.append(act)
                
    actions.sort(key=lambda x: x['deadline'])
    
    priority_counts = {"overdue": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "total": len(actions)}
    for a in actions:
        if a["priority"] in priority_counts:
            priority_counts[a["priority"]] += 1
            
    return {
        "company_name": company_profile.get("name"),
        "generated_at": datetime.now().isoformat(),
        "total_actions": len(actions),
        "summary": priority_counts,
        "actions": actions
    }
