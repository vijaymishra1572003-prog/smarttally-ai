import os
import logging
import xml.etree.ElementTree as ET
from xml.dom import minidom

import requests

logger = logging.getLogger(__name__)


class TallyService:
    """Tally Prime XML API integration service."""

    def __init__(self):
        self.tally_url = os.environ.get("TALLY_URL", "http://localhost:9000")

    def check_connection(self):
        try:
            xml_req = """<ENVELOPE>
<HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Data</TYPE><ID>List of Companies</ID></HEADER>
<BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES></DESC></BODY>
</ENVELOPE>"""
            resp = requests.post(self.tally_url, data=xml_req, headers={"Content-Type": "application/xml"}, timeout=5)
            if resp.status_code == 200:
                return {"connected": True, "message": "Tally Prime is connected", "url": self.tally_url}
            return {"connected": False, "message": f"Tally returned status {resp.status_code}"}
        except requests.exceptions.ConnectionError:
            return {"connected": False, "message": "Cannot connect to Tally. Ensure Tally Prime is running.", "url": self.tally_url}
        except Exception as e:
            return {"connected": False, "message": str(e)}

    def generate_ledger_xml(self, ledger):
        envelope = ET.Element("ENVELOPE")
        header = ET.SubElement(envelope, "HEADER")
        ET.SubElement(header, "TALLYREQUEST").text = "Import Data"

        body = ET.SubElement(envelope, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        request_desc = ET.SubElement(import_data, "REQUESTDESC")
        ET.SubElement(request_desc, "REPORTNAME").text = "All Masters"

        static_vars = ET.SubElement(request_desc, "STATICVARIABLES")
        ET.SubElement(static_vars, "SVCURRENTCOMPANY").text = getattr(ledger, "tally_company", "SmartTally AI")

        request_data = ET.SubElement(import_data, "REQUESTDATA")
        tallymsg = ET.SubElement(request_data, "TALLYMESSAGE", xmlns_UDF="TallyUDF")

        ledger_elem = ET.SubElement(tallymsg, "LEDGER", NAME=ledger.name, ACTION="Create")
        ET.SubElement(ledger_elem, "NAME").text = ledger.name
        ET.SubElement(ledger_elem, "PARENT").text = ledger.group_name
        if ledger.gstin:
            ET.SubElement(ledger_elem, "PARTYGSTIN").text = ledger.gstin
        ET.SubElement(ledger_elem, "OPENINGBALANCE").text = str(ledger.opening_balance)
        ET.SubElement(ledger_elem, "ISDEEMEDPOSITIVE").text = "Yes" if ledger.is_deemed_positive else "No"
        ET.SubElement(ledger_elem, "ISREVENUE").text = "Yes" if ledger.is_revenue else "No"

        xml_str = ET.tostring(envelope, encoding="unicode")
        return minidom.parseString(xml_str).toprettyxml(indent="  ")

    def generate_voucher_xml(self, voucher, invoice=None):
        envelope = ET.Element("ENVELOPE")
        header = ET.SubElement(envelope, "HEADER")
        ET.SubElement(header, "TALLYREQUEST").text = "Import Data"

        body = ET.SubElement(envelope, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        request_desc = ET.SubElement(import_data, "REQUESTDESC")
        ET.SubElement(request_desc, "REPORTNAME").text = "Vouchers"

        static_vars = ET.SubElement(request_desc, "STATICVARIABLES")
        ET.SubElement(static_vars, "SVCURRENTCOMPANY").text = "SmartTally AI"

        request_data = ET.SubElement(import_data, "REQUESTDATA")
        tallymsg = ET.SubElement(request_data, "TALLYMESSAGE", xmlns_UDF="TallyUDF")

        vtype = voucher.voucher_type.value if hasattr(voucher.voucher_type, "value") else str(voucher.voucher_type)
        voucher_elem = ET.SubElement(tallymsg, "VOUCHER", VCHTYPE=vtype, ACTION="Create")

        ET.SubElement(voucher_elem, "DATE").text = voucher.voucher_date.strftime("%Y%m%d") if voucher.voucher_date else ""
        ET.SubElement(voucher_elem, "VOUCHERTYPENAME").text = vtype
        ET.SubElement(voucher_elem, "NARRATION").text = voucher.narration or ""

        if voucher.party_name:
            ET.SubElement(voucher_elem, "PARTYLEDGERNAME").text = voucher.party_name
        if voucher.voucher_number:
            ET.SubElement(voucher_elem, "VOUCHERNUMBER").text = voucher.voucher_number
        if invoice and invoice.invoice_number:
            ET.SubElement(voucher_elem, "REFERENCE").text = invoice.invoice_number

        if voucher.gstin:
            ET.SubElement(voucher_elem, "PARTYGSTIN").text = voucher.gstin

        base_amount = voucher.amount - (voucher.cgst + voucher.sgst + voucher.igst)
        if base_amount <= 0:
            base_amount = voucher.amount

        # Debit entry
        debit_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(debit_entry, "LEDGERNAME").text = voucher.debit_ledger or "Purchase Account"
        ET.SubElement(debit_entry, "ISDEEMEDPOSITIVE").text = "Yes"
        ET.SubElement(debit_entry, "AMOUNT").text = f"-{base_amount:.2f}"

        # CGST entry
        if voucher.cgst > 0:
            cgst_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
            ET.SubElement(cgst_entry, "LEDGERNAME").text = "Input CGST"
            ET.SubElement(cgst_entry, "ISDEEMEDPOSITIVE").text = "Yes"
            ET.SubElement(cgst_entry, "AMOUNT").text = f"-{voucher.cgst:.2f}"

        # SGST entry
        if voucher.sgst > 0:
            sgst_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
            ET.SubElement(sgst_entry, "LEDGERNAME").text = "Input SGST"
            ET.SubElement(sgst_entry, "ISDEEMEDPOSITIVE").text = "Yes"
            ET.SubElement(sgst_entry, "AMOUNT").text = f"-{voucher.sgst:.2f}"

        # IGST entry
        if voucher.igst > 0:
            igst_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
            ET.SubElement(igst_entry, "LEDGERNAME").text = "Input IGST"
            ET.SubElement(igst_entry, "ISDEEMEDPOSITIVE").text = "Yes"
            ET.SubElement(igst_entry, "AMOUNT").text = f"-{voucher.igst:.2f}"

        # Credit entry
        credit_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(credit_entry, "LEDGERNAME").text = voucher.credit_ledger or "Sundry Creditors"
        ET.SubElement(credit_entry, "ISDEEMEDPOSITIVE").text = "No"
        ET.SubElement(credit_entry, "AMOUNT").text = f"{voucher.amount:.2f}"

        # GST details
        if invoice and (invoice.cgst or invoice.sgst or invoice.igst):
            gst_class = ET.SubElement(voucher_elem, "GSTCLASS")
            if invoice.hsn_code:
                ET.SubElement(gst_class, "HSNCODE").text = invoice.hsn_code
            ET.SubElement(gst_class, "TAXABLEAMOUNT").text = str(invoice.subtotal)

        xml_str = ET.tostring(envelope, encoding="unicode")
        return minidom.parseString(xml_str).toprettyxml(indent="  ")

    def generate_gst_voucher_xml(self, invoice):
        """Generate GST-specific voucher XML."""
        envelope = ET.Element("ENVELOPE")
        header = ET.SubElement(envelope, "HEADER")
        ET.SubElement(header, "TALLYREQUEST").text = "Import Data"

        body = ET.SubElement(envelope, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        request_desc = ET.SubElement(import_data, "REQUESTDESC")
        ET.SubElement(request_desc, "REPORTNAME").text = "Vouchers"

        request_data = ET.SubElement(import_data, "REQUESTDATA")
        tallymsg = ET.SubElement(request_data, "TALLYMESSAGE")

        voucher_elem = ET.SubElement(tallymsg, "VOUCHER", VCHTYPE="Purchase", ACTION="Create")
        ET.SubElement(voucher_elem, "DATE").text = invoice.invoice_date.strftime("%Y%m%d") if invoice.invoice_date else ""
        ET.SubElement(voucher_elem, "VOUCHERTYPENAME").text = "Purchase"
        ET.SubElement(voucher_elem, "PARTYLEDGERNAME").text = invoice.vendor_name or "Unknown"
        ET.SubElement(voucher_elem, "NARRATION").text = f"GST Purchase - {invoice.invoice_number}"

        if invoice.vendor_gstin:
            ET.SubElement(voucher_elem, "PARTYGSTIN").text = invoice.vendor_gstin

        inv_entry = ET.SubElement(voucher_elem, "INVENTORYENTRIESIN.LIST")
        ET.SubElement(inv_entry, "STOCKITEMNAME").text = invoice.description or "Purchase Item"

        rate_entry = ET.SubElement(inv_entry, "RATE")
        ET.SubElement(rate_entry, "RATEPERUNIT").text = str(invoice.subtotal)

        amount_entry = ET.SubElement(inv_entry, "AMOUNT")
        amount_entry.text = str(invoice.subtotal)

        if invoice.hsn_code:
            ET.SubElement(inv_entry, "HSNCODE").text = invoice.hsn_code

        xml_str = ET.tostring(envelope, encoding="unicode")
        return minidom.parseString(xml_str).toprettyxml(indent="  ")

    def push_voucher(self, xml_data):
        try:
            resp = requests.post(
                self.tally_url,
                data=xml_data,
                headers={"Content-Type": "application/xml"},
                timeout=10,
            )
            if resp.status_code == 200:
                response_text = resp.text
                if "CREATED" in response_text.upper():
                    return {"success": True, "response": response_text, "message": "Voucher created in Tally"}
                if "ERROR" in response_text.upper():
                    return {"success": False, "response": response_text, "error": "Tally returned an error"}
                return {"success": True, "response": response_text, "message": "Voucher sent to Tally"}
            return {"success": False, "error": f"HTTP {resp.status_code}", "response": resp.text}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Cannot connect to Tally Prime", "xml_generated": xml_data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def push_ledger(self, xml_data):
        try:
            resp = requests.post(
                self.tally_url,
                data=xml_data,
                headers={"Content-Type": "application/xml"},
                timeout=10,
            )
            if resp.status_code == 200:
                return {"success": True, "response": resp.text, "message": "Ledger created in Tally"}
            return {"success": False, "error": f"HTTP {resp.status_code}"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Cannot connect to Tally Prime", "xml_generated": xml_data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def fetch_companies(self):
        xml_req = """<ENVELOPE>
<HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Data</TYPE><ID>List of Companies</ID></HEADER>
<BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES></DESC></BODY>
</ENVELOPE>"""
        try:
            resp = requests.post(self.tally_url, data=xml_req, headers={"Content-Type": "application/xml"}, timeout=5)
            if resp.status_code == 200:
                return {"success": True, "data": resp.text}
            return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def fetch_ledgers(self, company_name=""):
        xml_req = f"""<ENVELOPE>
<HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Data</TYPE><ID>List of Ledgers</ID></HEADER>
<BODY><DESC><STATICVARIABLES>
<SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
<SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
</STATICVARIABLES></DESC></BODY>
</ENVELOPE>"""
        try:
            resp = requests.post(self.tally_url, data=xml_req, headers={"Content-Type": "application/xml"}, timeout=5)
            if resp.status_code == 200:
                return {"success": True, "data": resp.text}
            return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
