import json
import uuid
from datetime import datetime

def generate_document(action: dict, company_profile: dict, financial_data: dict) -> dict:
    """Generate a draft tax document based on the action and company's financial profile."""
    
    doc_type = action.get("action_data", {}).get("output_type", "unknown")
    tax_rate = action.get("action_data", {}).get("tax_rate", 0.0)
    rev = financial_data.get("annual_revenue", 0.0)
    
    # Scale numbers down if quarterly or monthly
    multiplier = 1.0
    freq_str = action.get("obligation_name", "").lower()
    if "quarterly" in freq_str or "quarter" in freq_str:
        multiplier = 0.25
    elif "monthly" in freq_str:
        multiplier = 1/12.0
        
    revenue_period = rev * multiplier
    
    base_doc = {
        "document_type": doc_type,
        "form": action.get("action_data", {}).get("form", "Unknown Form"),
        "title": f"Draft {action.get('obligation_name')} [{action.get('jurisdiction')}]",
        "warnings": [],
        "required_attachments": [],
        "metadata": {
            "status": "draft",
            "generated_at": datetime.now().isoformat()
        },
        "sections": []
    }
    
    if doc_type == "tax_return":
        cogs = revenue_period * 0.4
        opex = revenue_period * 0.3
        taxable_income = revenue_period - cogs - opex
        tax_due = taxable_income * tax_rate
        
        base_doc["sections"] = [
            {
                "name": "Income Statement",
                "fields": {
                    "Gross Revenue": round(revenue_period, 2),
                    "Cost of Goods Sold": round(cogs, 2),
                    "Operating Expenses": round(opex, 2),
                    "Net Taxable Income": round(taxable_income, 2)
                }
            },
            {
                "name": "Tax Computation",
                "fields": {
                    "Taxable Income": round(taxable_income, 2),
                    "Applicable Tax Rate": f"{tax_rate * 100}%",
                    "Total Tax Due": round(tax_due, 2)
                }
            }
        ]
        base_doc["warnings"].append("Confirm all deductions with your tax advisor.")
        base_doc["required_attachments"].append("Trial Balance")
        
    elif doc_type == "vat_return" or doc_type == "sales_tax_return":
        output_vat = revenue_period * tax_rate
        input_vat = (revenue_period * 0.4) * tax_rate
        net_payable = output_vat - input_vat
        
        base_doc["sections"] = [
            {
                "name": "Sales & VAT OUT",
                "fields": {
                    "Total Sales (Excl VAT)": round(revenue_period, 2),
                    "Output VAT Collected": round(output_vat, 2)
                }
            },
            {
                "name": "Purchases & VAT IN",
                "fields": {
                    "Total Purchases (Excl VAT)": round(revenue_period * 0.4, 2),
                    "Input VAT Paid": round(input_vat, 2)
                }
            },
            {
                "name": "Net Position",
                "fields": {
                    "Net VAT Payable/(Refundable)": round(net_payable, 2)
                }
            }
        ]
        base_doc["required_attachments"].append("Sales Register")
        
    elif doc_type == "payroll_return":
        wages = revenue_period * 0.15
        ss_tax = wages * tax_rate
        
        base_doc["sections"] = [
            {
                "name": "Payroll Details",
                "fields": {
                    "Employee Count": company_profile.get("employee_count", 0),
                    "Total Gross Wages": round(wages, 2)
                }
            },
            {
                "name": "Tax Withholdings",
                "fields": {
                    "Employer/Employee Taxes": round(ss_tax, 2),
                    "Total Payroll Tax Due": round(ss_tax, 2)
                }
            }
        ]
        
    elif doc_type == "activity_statement":
        # GST + PAYG combo basically
        gst_out = revenue_period * 0.10
        gst_in = (revenue_period * 0.4) * 0.10
        payg = revenue_period * 0.15 * 0.20 # 20% avg withholding on 15% revenue wages
        
        base_doc["sections"] = [
            {
                "name": "Goods and Services Tax (GST)",
                "fields": {
                    "Total Sales": round(revenue_period, 2),
                    "GST on Sales (1A)": round(gst_out, 2),
                    "GST on Purchases (1B)": round(gst_in, 2),
                    "Net GST": round(gst_out - gst_in, 2)
                }
            },
            {
                "name": "PAYG Tax Withheld",
                "fields": {
                    "Total Salary/Wages (W1)": round(revenue_period * 0.15, 2),
                    "Amount Withheld (W2)": round(payg, 2)
                }
            },
            {
                "name": "Total Payment",
                "fields": {
                    "Total Amount Payable": round((gst_out - gst_in) + payg, 2)
                }
            }
        ]
        
    else:
        # Default payment voucher
        base_doc["sections"] = [
            {
                "name": "Payment Details",
                "fields": {
                    "Estimated Amount Due": round(revenue_period * tax_rate * 0.1, 2)
                }
            }
        ]
        
    return base_doc
