import re

KNOWN_REGIONS = ["Kampala", "Mbarara", "Entebbe", "Gulu", "Jinja"]
KNOWN_TAX_TYPES = ["VAT", "PAYE", "Corporate Tax", "Income Tax", "Customs", "Excise"]

def parse_query(query: str):
    """
    Parses a natural language query for governance reporting.
    Identifies regions, tax types, and performance intent.
    """
    if not query:
        return {
            "region": None,
            "tax_type": None,
            "wants_underperforming": False,
            "interpreted_as": "",
            "original_query": query
        }

    lower = query.lower()
    
    region = next((r for r in KNOWN_REGIONS if r.lower() in lower), None)
    tax_type = next((t for t in KNOWN_TAX_TYPES if t.lower() in lower), None)
    wants_underperforming = bool(re.search(r"underperform|below target|declin", lower))
    
    interpreted_parts = []
    if region:
        interpreted_parts.append(f"Region = {region}")
    if tax_type:
        interpreted_parts.append(f"Tax Type = {tax_type}")
    if wants_underperforming:
        interpreted_parts.append("sorted by underperformance")
        
    interpreted_as = ", ".join(interpreted_parts) if interpreted_parts else "no specific filters recognized"
    
    return {
        "region": region,
        "tax_type": tax_type,
        "wants_underperforming": wants_underperforming,
        "interpreted_as": interpreted_as,
        "original_query": query
    }
