"""GST calculation engine for Indian tax compliance."""

GST_RATES = {
    "0": 0,
    "0.25": 0.25,
    "3": 3,
    "5": 5,
    "12": 12,
    "18": 18,
    "28": 28,
}

HSN_GST_MAP = {
    "0401": 5,   # Milk
    "0402": 5,   # Cream, milk powder
    "0901": 5,   # Coffee
    "0902": 5,   # Tea
    "1001": 5,   # Wheat
    "1006": 5,   # Rice
    "1701": 5,   # Sugar
    "2201": 18,  # Water
    "2202": 28,  # Aerated water
    "3004": 12,  # Medicines
    "3401": 18,  # Soap
    "3926": 18,  # Plastic goods
    "4202": 18,  # Bags
    "4901": 0,   # Books
    "6109": 5,   # T-shirts
    "6203": 12,  # Men's suits
    "6403": 18,  # Footwear
    "7113": 3,   # Gold jewellery
    "8471": 18,  # Computers
    "8517": 18,  # Mobile phones
    "8528": 28,  # TV
    "8703": 28,  # Cars
    "8711": 28,  # Motorcycles
    "9401": 18,  # Furniture
    "9403": 18,  # Other furniture
    "9503": 18,  # Toys
    "9954": 18,  # Construction services
    "9971": 18,  # Financial services
    "9973": 18,  # Leasing services
    "9983": 18,  # Professional services
    "9984": 18,  # Telecom services
    "9987": 18,  # Maintenance services
    "9988": 18,  # Manufacturing services
    "9991": 18,  # Government services
    "9992": 18,  # Education
    "9993": 0,   # Healthcare
    "9996": 18,  # Transport
    "9997": 18,  # Financial services
}

INDIAN_STATES = {
    "01": "Jammu & Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "25": "Daman & Diu",
    "26": "Dadra & Nagar Haveli",
    "27": "Maharashtra",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman & Nicobar",
    "36": "Telangana",
    "37": "Andhra Pradesh",
}


class GSTCalculator:
    """Calculate GST breakup based on Indian GST rules."""

    def calculate(self, amount, gst_rate, seller_state_code=None, buyer_state_code=None):
        gst_rate = float(gst_rate)
        amount = float(amount)

        is_igst = False
        if seller_state_code and buyer_state_code:
            is_igst = seller_state_code != buyer_state_code

        gst_amount = amount * gst_rate / 100

        if is_igst:
            return {
                "taxable_value": round(amount, 2),
                "cgst_rate": 0,
                "sgst_rate": 0,
                "igst_rate": gst_rate,
                "cgst": 0,
                "sgst": 0,
                "igst": round(gst_amount, 2),
                "total_gst": round(gst_amount, 2),
                "total_amount": round(amount + gst_amount, 2),
                "supply_type": "Inter-State",
            }

        half_rate = gst_rate / 2
        half_gst = gst_amount / 2
        return {
            "taxable_value": round(amount, 2),
            "cgst_rate": half_rate,
            "sgst_rate": half_rate,
            "igst_rate": 0,
            "cgst": round(half_gst, 2),
            "sgst": round(half_gst, 2),
            "igst": 0,
            "total_gst": round(gst_amount, 2),
            "total_amount": round(amount + gst_amount, 2),
            "supply_type": "Intra-State",
        }

    def get_gst_rate_for_hsn(self, hsn_code):
        if not hsn_code:
            return 18
        prefix = hsn_code[:4]
        return HSN_GST_MAP.get(prefix, 18)

    def get_state_from_gstin(self, gstin):
        if not gstin or len(gstin) < 2:
            return None, None
        state_code = gstin[:2]
        state_name = INDIAN_STATES.get(state_code)
        return state_code, state_name

    def reverse_calculate(self, total_inclusive, gst_rate):
        gst_rate = float(gst_rate)
        taxable_value = total_inclusive * 100 / (100 + gst_rate)
        gst_amount = total_inclusive - taxable_value
        return {
            "taxable_value": round(taxable_value, 2),
            "gst_amount": round(gst_amount, 2),
            "total": round(total_inclusive, 2),
        }
