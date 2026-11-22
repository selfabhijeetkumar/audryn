import os
import json
from decimal import Decimal
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class SyntheticAuditDataGenerator:
    """
    Generates synthetic multi-year financial audit datasets for AUDRYN Case Study 2.
    Includes realistic financial schedules and 10 controlled planted anomalies.
    
    DISCLAIMER: All companies, transactions, amounts, and tax rules are completely
    FICTIONAL and generated exclusively for demonstration and testing purposes.
    """

    COMPANY_NAME = "Apex Industrial Dynamics Pvt Ltd"
    CIN = "U29100MH2020PTC998877"
    CURRENCY_CODE = "INR"
    CURRENCY_SYMBOL = "₹"
    DISCLAIMER = (
        "FICTIONAL DEMONSTRATION DATA: All corporate identity, Corporate Identification Number (CIN), "
        "financial figures, vouchers, and tax calculations are completely synthetic and generated "
        "exclusively for AUDRYN testing and demonstration. The CIN is fictional and is NOT an MCA-verified "
        "legal entity. No real-world taxpayer data is contained herein."
    )

    def __init__(self, output_dir: str = "data/synthetic"):
        self.output_dir = output_dir
        self.invoices_dir = os.path.join(output_dir, "invoices")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.invoices_dir, exist_ok=True)

    def generate_all(self):
        print("Generating synthetic 3-year audit datasets...")
        self._generate_trial_balances()
        self._generate_general_ledger()
        self._generate_sales_register()
        self._generate_purchase_register()
        self._generate_fixed_asset_register()
        self._generate_bank_transactions()
        self._generate_tax_computation()
        self._generate_synthetic_invoices()
        self._generate_ground_truth_anomalies()
        print("Synthetic dataset generation complete.")

    def _generate_trial_balances(self):
        """Generates Trial Balances for FY2023-24, FY2024-25, FY2025-26."""
        # FY 2023-24 (Balanced)
        tb_fy23 = [
            {"account_code": "1001", "account_name": "Cash & Cash Equivalents", "debit": 250000.00, "credit": 0.00},
            {"account_code": "1002", "account_name": "Trade Receivables", "debit": 680000.00, "credit": 0.00},
            {"account_code": "1003", "account_name": "Closing Inventory", "debit": 450000.00, "credit": 0.00},
            {"account_code": "1501", "account_name": "Plant & Machinery (Gross)", "debit": 1200000.00, "credit": 0.00},
            {"account_code": "1502", "account_name": "Accumulated Depreciation", "debit": 0.00, "credit": 360000.00},
            {"account_code": "2001", "account_name": "Trade Payables", "debit": 0.00, "credit": 420000.00},
            {"account_code": "2002", "account_name": "Short-Term Bank Borrowings", "debit": 0.00, "credit": 300000.00},
            {"account_code": "3001", "account_name": "Share Capital", "debit": 0.00, "credit": 500000.00},
            {"account_code": "3002", "account_name": "Retained Earnings", "debit": 0.00, "credit": 900000.00},
            {"account_code": "4001", "account_name": "Revenue from Operations", "debit": 0.00, "credit": 3200000.00},
            {"account_code": "5001", "account_name": "Cost of Raw Materials", "debit": 1850000.00, "credit": 0.00},
            {"account_code": "5002", "account_name": "Employee Benefit Expenses", "debit": 620000.00, "credit": 0.00},
            {"account_code": "5003", "account_name": "Depreciation Expense", "debit": 180000.00, "credit": 0.00},
            {"account_code": "5004", "account_name": "Other Operating Expenses", "debit": 150000.00, "credit": 0.00},
        ]
        pd.DataFrame(tb_fy23).to_csv(os.path.join(self.output_dir, "trial_balance_fy2023_24.csv"), index=False)

        # FY 2024-25 (Primary Audit Year - Planted with Cross-Year Anomaly #5 and Ledger Anomaly #3)
        tb_fy24 = [
            {"account_code": "1001", "account_name": "Cash & Cash Equivalents", "debit": 310000.00, "credit": 0.00},
            {"account_code": "1002", "account_name": "Trade Receivables", "debit": 790000.00, "credit": 0.00},
            # ANOMALY #5: Opening/Closing Inventory gap: FY23 closed at 450000, FY24 shows opening inventory 485000!
            {"account_code": "1003", "account_name": "Opening Inventory", "debit": 485000.00, "credit": 0.00},
            {"account_code": "1004", "account_name": "Closing Inventory", "debit": 520000.00, "credit": 0.00},
            {"account_code": "1501", "account_name": "Plant & Machinery (Gross)", "debit": 1500000.00, "credit": 0.00},
            {"account_code": "1502", "account_name": "Accumulated Depreciation", "debit": 0.00, "credit": 570000.00},
            {"account_code": "2001", "account_name": "Trade Payables", "debit": 0.00, "credit": 490000.00},
            {"account_code": "2002", "account_name": "Short-Term Bank Borrowings", "debit": 0.00, "credit": 250000.00},
            {"account_code": "3001", "account_name": "Share Capital", "debit": 0.00, "credit": 500000.00},
            {"account_code": "3002", "account_name": "Retained Earnings", "debit": 0.00, "credit": 1050000.00},
            # ANOMALY #3: Reported Revenue is 4,120,000, but General Ledger sums to 4,148,000!
            {"account_code": "4001", "account_name": "Revenue from Operations", "debit": 0.00, "credit": 4120000.00},
            {"account_code": "5001", "account_name": "Cost of Raw Materials", "debit": 2100000.00, "credit": 0.00},
            {"account_code": "5002", "account_name": "Employee Benefit Expenses", "debit": 710000.00, "credit": 0.00},
            {"account_code": "5003", "account_name": "Depreciation Expense", "debit": 210000.00, "credit": 0.00},
            # ANOMALY #10: Materiality breach in legal expenses
            {"account_code": "5004", "account_name": "Other Operating Expenses", "debit": 178000.00, "credit": 0.00},
            {"account_code": "5005", "account_name": "Legal & Professional Fees", "debit": 87000.00, "credit": 0.00},
        ]
        pd.DataFrame(tb_fy24).to_csv(os.path.join(self.output_dir, "trial_balance_fy2024_25.csv"), index=False)

        # FY 2025-26
        tb_fy25 = [
            {"account_code": "1001", "account_name": "Cash & Cash Equivalents", "debit": 420000.00, "credit": 0.00},
            {"account_code": "1002", "account_name": "Trade Receivables", "debit": 920000.00, "credit": 0.00},
            {"account_code": "1003", "account_name": "Closing Inventory", "debit": 590000.00, "credit": 0.00},
            {"account_code": "1501", "account_name": "Plant & Machinery (Gross)", "debit": 1800000.00, "credit": 0.00},
            {"account_code": "1502", "account_name": "Accumulated Depreciation", "debit": 0.00, "credit": 780000.00},
            {"account_code": "2001", "account_name": "Trade Payables", "debit": 0.00, "credit": 530000.00},
            {"account_code": "2002", "account_name": "Short-Term Bank Borrowings", "debit": 0.00, "credit": 200000.00},
            {"account_code": "3001", "account_name": "Share Capital", "debit": 0.00, "credit": 500000.00},
            {"account_code": "3002", "account_name": "Retained Earnings", "debit": 0.00, "credit": 1250000.00},
            {"account_code": "4001", "account_name": "Revenue from Operations", "debit": 0.00, "credit": 4800000.00},
            {"account_code": "5001", "account_name": "Cost of Raw Materials", "debit": 2450000.00, "credit": 0.00},
            {"account_code": "5002", "account_name": "Employee Benefit Expenses", "debit": 820000.00, "credit": 0.00},
            {"account_code": "5003", "account_name": "Depreciation Expense", "debit": 240000.00, "credit": 0.00},
            {"account_code": "5004", "account_name": "Other Operating Expenses", "debit": 210000.00, "credit": 0.00},
            {"account_code": "5005", "account_name": "Legal & Professional Fees", "debit": 60000.00, "credit": 0.00},
        ]
        pd.DataFrame(tb_fy25).to_csv(os.path.join(self.output_dir, "trial_balance_fy2025_26.csv"), index=False)

    def _generate_general_ledger(self):
        """Generates General Ledger entries for FY2024-25 Revenue Account."""
        gl_entries = [
            {"date": "2024-04-15", "voucher_id": "VOUCH-REV-1001", "account_code": "4001", "description": "Sales invoice INV-2024-001", "debit": 0.00, "credit": 18500.00},
            # ANOMALY #1: Duplicate invoice posted to ledger
            {"date": "2024-04-16", "voucher_id": "VOUCH-REV-1002", "account_code": "4001", "description": "Duplicate invoice INV-2024-001", "debit": 0.00, "credit": 18500.00},
            {"date": "2024-05-10", "voucher_id": "VOUCH-REV-1015", "account_code": "4001", "description": "Domestic sales order batch 14", "debit": 0.00, "credit": 125000.00},
            {"date": "2024-06-20", "voucher_id": "VOUCH-REV-1033", "account_code": "4001", "description": "Export tooling consignment", "debit": 0.00, "credit": 350000.00},
            # ANOMALY #2: Missing invoice voucher reference
            {"date": "2024-07-04", "voucher_id": "VOUCH-REV-1049", "account_code": "4001", "description": "Direct credit revenue sans invoice", "debit": 0.00, "credit": 42000.00},
            {"date": "2024-08-18", "voucher_id": "VOUCH-REV-1082", "account_code": "4001", "description": "Machined parts delivery batch 22", "debit": 0.00, "credit": 540000.00},
            # ANOMALY #6: Unusual round-sum entry on Sunday
            {"date": "2024-09-15", "voucher_id": "VOUCH-REV-1100", "account_code": "4001", "description": "Sunday adjustment transfer", "debit": 0.00, "credit": 100000.00},
            {"date": "2024-11-02", "voucher_id": "VOUCH-REV-1145", "account_code": "4001", "description": "Q3 equipment supply agreement", "debit": 0.00, "credit": 850000.00},
            {"date": "2024-12-19", "voucher_id": "VOUCH-REV-1188", "account_code": "4001", "description": "Precision components Q3 final", "debit": 0.00, "credit": 620000.00},
            {"date": "2025-01-25", "voucher_id": "VOUCH-REV-1210", "account_code": "4001", "description": "Automotive assembly supply", "debit": 0.00, "credit": 730000.00},
            {"date": "2025-03-28", "voucher_id": "VOUCH-REV-1299", "account_code": "4001", "description": "Year-end institutional delivery", "debit": 0.00, "credit": 754000.00},
        ]
        pd.DataFrame(gl_entries).to_csv(os.path.join(self.output_dir, "general_ledger_fy2024_25.csv"), index=False)

    def _generate_sales_register(self):
        sales = [
            {"invoice_number": "INV-2024-001", "date": "2024-04-15", "customer": "Zenith Motors Ltd", "taxable_value": 18500.00, "gst_rate": 0.18, "total_value": 21830.00},
            # ANOMALY #1: Duplicate invoice in register
            {"invoice_number": "INV-2024-001", "date": "2024-04-16", "customer": "Zenith Motors Ltd", "taxable_value": 18500.00, "gst_rate": 0.18, "total_value": 21830.00},
            {"invoice_number": "INV-2024-002", "date": "2024-05-09", "customer": "Aura Heavy Engineering", "taxable_value": 125000.00, "gst_rate": 0.18, "total_value": 147500.00},
            {"invoice_number": "INV-2024-003", "date": "2024-06-18", "customer": "Global Aerospace GmbH", "taxable_value": 350000.00, "gst_rate": 0.00, "total_value": 350000.00},
            {"invoice_number": "INV-2024-004", "date": "2024-08-15", "customer": "Bharat Hydraulics", "taxable_value": 540000.00, "gst_rate": 0.18, "total_value": 637200.00},
            {"invoice_number": "INV-2024-005", "date": "2024-11-01", "customer": "Titan Forgings Ltd", "taxable_value": 850000.00, "gst_rate": 0.18, "total_value": 1003000.00},
            {"invoice_number": "INV-2024-006", "date": "2024-12-18", "customer": "Omron Robotics", "taxable_value": 620000.00, "gst_rate": 0.18, "total_value": 731600.00},
            {"invoice_number": "INV-2024-007", "date": "2025-01-22", "customer": "Zenith Motors Ltd", "taxable_value": 730000.00, "gst_rate": 0.18, "total_value": 861400.00},
            {"invoice_number": "INV-2024-008", "date": "2025-03-27", "customer": "Dynamic Transmissions", "taxable_value": 754000.00, "gst_rate": 0.18, "total_value": 889720.00},
        ]
        pd.DataFrame(sales).to_csv(os.path.join(self.output_dir, "sales_register_fy2024_25.csv"), index=False)

    def _generate_purchase_register(self):
        purchases = [
            {"purchase_id": "PUR-2024-01", "vendor": "Steel Castings India", "bill_no": "BILL-9011", "amount": 450000.00, "gst": 81000.00, "total": 531000.00},
            {"purchase_id": "PUR-2024-02", "vendor": "Kirloskar Power Tools", "bill_no": "BILL-4412", "amount": 220000.00, "gst": 39600.00, "total": 259600.00},
            # ANOMALY #8: Missing supporting vendor bill
            {"purchase_id": "PUR-2024-03", "vendor": "Shivaji Precision Lathe", "bill_no": "MISSING_DOC", "amount": 45000.00, "gst": 0.00, "total": 45000.00},
            # ANOMALY #9: Capital tool classified as revenue purchase to evade capitalization
            {"purchase_id": "PUR-2024-04", "vendor": "Haas Automation Inc", "bill_no": "BILL-CNC-88", "amount": 80000.00, "gst": 14400.00, "total": 94400.00},
            {"purchase_id": "PUR-2024-05", "vendor": "SKF Bearings Ltd", "bill_no": "BILL-5519", "amount": 310000.00, "gst": 55800.00, "total": 365800.00},
        ]
        pd.DataFrame(purchases).to_csv(os.path.join(self.output_dir, "purchase_register_fy2024_25.csv"), index=False)

    def _generate_fixed_asset_register(self):
        assets = [
            {"asset_id": "AST-101", "asset_name": "CNC Milling Machine 4-Axis", "purchase_date": "2021-06-15", "cost": 600000.00, "opening_wdv": 340000.00, "depreciation_method": "WDV", "statutory_rate": 0.15, "depreciation_claimed": 51000.00, "closing_wdv": 289000.00},
            # ANOMALY #4: Incorrect depreciation claimed at 25% instead of statutory 15%!
            # 500,000 opening WDV * 15% should be 75,000; company claimed 125,000!
            {"asset_id": "AST-102", "asset_name": "Heavy Industrial Lathe", "purchase_date": "2022-09-10", "cost": 750000.00, "opening_wdv": 500000.00, "depreciation_method": "WDV", "statutory_rate": 0.15, "depreciation_claimed": 125000.00, "closing_wdv": 375000.00},
            {"asset_id": "AST-103", "asset_name": "Engineering CAD Workstations", "purchase_date": "2023-01-20", "cost": 150000.00, "opening_wdv": 90000.00, "depreciation_method": "WDV", "statutory_rate": 0.40, "depreciation_claimed": 36000.00, "closing_wdv": 54000.00},
        ]
        pd.DataFrame(assets).to_csv(os.path.join(self.output_dir, "fixed_asset_register_fy2024_25.csv"), index=False)

    def _generate_bank_transactions(self):
        bank_tx = [
            {"date": "2024-04-18", "utr_reference": "UTR-2024-991", "description": "NEFT from Zenith Motors", "debit": 0.00, "credit": 21830.00, "balance": 271830.00},
            {"date": "2024-05-12", "utr_reference": "UTR-2024-992", "description": "Vendor payout Steel Castings", "debit": 531000.00, "credit": 0.00, "balance": -259170.00},
            # ANOMALY #7: Duplicate UTR payment reference cleared twice!
            {"date": "2024-06-25", "utr_reference": "UTR-DUP-8822", "description": "Vendor payout Haas Automation", "debit": 94400.00, "credit": 0.00, "balance": -353570.00},
            {"date": "2024-07-02", "utr_reference": "UTR-DUP-8822", "description": "Duplicate debit Haas Automation", "debit": 94400.00, "credit": 0.00, "balance": -447970.00},
            {"date": "2024-08-20", "utr_reference": "UTR-2024-995", "description": "Export remittance Global Aero", "debit": 0.00, "credit": 350000.00, "balance": -97970.00},
        ]
        pd.DataFrame(bank_tx).to_csv(os.path.join(self.output_dir, "bank_transactions_fy2024_25.csv"), index=False)

    def _generate_tax_computation(self):
        tax = [
            {"item": "Profit Before Tax (PBT)", "amount": 875000.00},
            {"item": "Add: Book Depreciation", "amount": 212000.00},
            {"item": "Less: Statutory Tax Depreciation (Claimed)", "amount": 212000.00},
            {"item": "Taxable Business Income", "amount": 875000.00},
            {"item": "Corporate Tax @ 25% (Demonstration Rule)", "amount": 218750.00},
            {"item": "Surcharge @ 7%", "amount": 15312.50},
            {"item": "Health & Education Cess @ 4%", "amount": 9362.50},
            {"item": "Total Tax Liability Computed", "amount": 243425.00},
        ]
        pd.DataFrame(tax).to_csv(os.path.join(self.output_dir, "tax_computation_fy2024_25.csv"), index=False)

    def _generate_synthetic_invoices(self):
        """Generates realistic synthetic PDF invoices using reportlab."""
        inv_path = os.path.join(self.invoices_dir, "INV_2024_001.pdf")
        c = canvas.Canvas(inv_path, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, f"TAX INVOICE — {self.COMPANY_NAME}")
        c.setFont("Helvetica", 10)
        c.drawString(50, 735, f"CIN: {self.CIN} | GSTIN: 27AABCA1234F1Z5")
        c.drawString(50, 715, "Invoice No: INV-2024-001")
        c.drawString(50, 700, "Date: 15-April-2024")
        c.drawString(50, 680, "Bill To: Zenith Motors Ltd, Pune Plant, MIDC Bhosari")
        c.line(50, 665, 550, 665)
        c.drawString(50, 645, "Item: Precision Machined Flange Assemblies (Qty: 50)")
        c.drawString(400, 645, "INR 18,500.00")
        c.drawString(50, 625, "GST @ 18%:")
        c.drawString(400, 625, "INR 3,330.00")
        c.line(50, 610, 550, 610)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 590, "Total Payable:")
        c.drawString(400, 590, "INR 21,830.00")
        c.save()

        # Duplicate invoice
        dup_path = os.path.join(self.invoices_dir, "INV_2024_001_DUP.pdf")
        c_dup = canvas.Canvas(dup_path, pagesize=letter)
        c_dup.setFont("Helvetica-Bold", 16)
        c_dup.drawString(50, 750, f"TAX INVOICE — {self.COMPANY_NAME}")
        c_dup.setFont("Helvetica", 10)
        c_dup.drawString(50, 735, f"CIN: {self.CIN} | GSTIN: 27AABCA1234F1Z5")
        c_dup.drawString(50, 715, "Invoice No: INV-2024-001 (DUPLICATE COPY)")
        c_dup.drawString(50, 700, "Date: 16-April-2024")
        c_dup.drawString(50, 680, "Bill To: Zenith Motors Ltd, Pune Plant")
        c_dup.drawString(50, 645, "Item: Precision Machined Flange Assemblies (Qty: 50)")
        c_dup.drawString(400, 645, "INR 18,500.00")
        c_dup.drawString(400, 590, "INR 21,830.00")
        c_dup.save()

    def _generate_ground_truth_anomalies(self):
        """Generates isolated ground truth file detailing all 10 planted anomalies."""
        anomalies = [
            {
                "anomaly_id": "ANOM-01",
                "title": "Duplicate Invoice Posted",
                "category": "REVENUE_AND_SALES",
                "document_reference": "sales_register_fy2024_25.csv & general_ledger_fy2024_25.csv",
                "planted_detail": "Invoice INV-2024-001 was posted twice on 2024-04-15 and 2024-04-16 for ₹ 18,500.00 (Total ₹ 21,830.00 with GST).",
                "impact_amount": 18500.00,
                "currency": "INR",
            },
            {
                "anomaly_id": "ANOM-02",
                "title": "Missing Invoice Supporting Ledger",
                "category": "REVENUE_AND_SALES",
                "document_reference": "general_ledger_fy2024_25.csv",
                "planted_detail": "Voucher VOUCH-REV-1049 for ₹ 42,000.00 has no matching sales invoice in the Sales Register.",
                "impact_amount": 42000.00,
                "currency": "INR",
            },
            {
                "anomaly_id": "ANOM-03",
                "title": "Trial Balance to General Ledger Revenue Mismatch",
                "category": "GENERAL_LEDGER",
                "document_reference": "trial_balance_fy2024_25.csv vs general_ledger_fy2024_25.csv",
                "planted_detail": "Trial balance account 4001 reports ₹ 41,20,000.00, while general ledger total is ₹ 41,48,000.00 (₹ 28,000.00 variance).",
                "impact_amount": 28000.00,
                "currency": "INR",
            },
            {
                "anomaly_id": "ANOM-04",
                "title": "Incorrect Depreciation Calculation",
                "category": "FIXED_ASSETS_AND_DEPRECIATION",
                "document_reference": "fixed_asset_register_fy2024_25.csv",
                "planted_detail": "Asset AST-102 claimed 25% WDV depreciation (₹ 1,25,000.00) instead of statutory 15% Section 32 rate (₹ 75,000.00), overstating expense by ₹ 50,000.00.",
                "impact_amount": 50000.00,
                "currency": "INR",
            },
            {
                "anomaly_id": "ANOM-05",
                "title": "Cross-Year Inventory Discrepancy",
                "category": "STATUTORY_RECONCILIATION",
                "document_reference": "trial_balance_fy2023_24.csv vs trial_balance_fy2024_25.csv",
                "planted_detail": "Closing inventory in FY 2023-24 was ₹ 4,50,000.00, but Opening inventory in FY 2024-25 was booked at ₹ 4,85,000.00 (₹ 35,000.00 unexplained leap).",
                "impact_amount": 35000.00,
                "currency": "INR",
            },
            {
                "anomaly_id": "ANOM-06",
                "title": "Unusual Journal Entry Timing & Round Sum",
                "category": "GENERAL_LEDGER",
                "document_reference": "general_ledger_fy2024_25.csv (VOUCH-REV-1100)",
                "planted_detail": "Round-sum entry of ₹ 1,00,000.00 posted on Sunday 2024-09-15 without customer invoice reference.",
                "impact_amount": 100000.00,
                "currency": "INR",
            },
            {
                "anomaly_id": "ANOM-07",
                "title": "Duplicate Bank UTR Payment Reference",
                "category": "CASH_AND_BANK",
                "document_reference": "bank_transactions_fy2024_25.csv",
                "planted_detail": "UTR-DUP-8822 for ₹ 94,400.00 debited twice on 2024-06-25 and 2024-07-02.",
                "impact_amount": 94400.00,
                "currency": "INR",
            },
            {
                "anomaly_id": "ANOM-08",
                "title": "Missing Supporting Vendor Bill",
                "category": "PURCHASES_AND_PAYABLES",
                "document_reference": "purchase_register_fy2024_25.csv (PUR-2024-03)",
                "planted_detail": "Purchase PUR-2024-03 for ₹ 45,000.00 from Shivaji Precision Lathe has bill_no 'MISSING_DOC'.",
                "impact_amount": 45000.00,
                "currency": "INR",
            },
            {
                "anomaly_id": "ANOM-09",
                "title": "Capital Expenditure Misclassified as Revenue",
                "category": "TAX_COMPLIANCE",
                "document_reference": "purchase_register_fy2024_25.csv (PUR-2024-04)",
                "planted_detail": "CNC capital tool costing ₹ 80,000.00 from Haas Automation expensed under revenue purchases instead of capitalized.",
                "impact_amount": 80000.00,
                "currency": "INR",
            },
            {
                "anomaly_id": "ANOM-10",
                "title": "Materiality Threshold Breach",
                "category": "TAX_COMPLIANCE",
                "document_reference": "trial_balance_fy2024_25.csv (5005)",
                "planted_detail": "Legal expenses leaped from ₹ 0 to ₹ 87,000.00 without supporting fee schedule, exceeding the ₹ 5,000.00 audit materiality threshold.",
                "impact_amount": 87000.00,
                "currency": "INR",
            },
        ]
        truth_payload = {
            "disclaimer": self.DISCLAIMER,
            "entity": self.COMPANY_NAME,
            "cin": self.CIN,
            "currency": self.CURRENCY_CODE,
            "currency_symbol": self.CURRENCY_SYMBOL,
            "anomalies": anomalies,
        }
        truth_path = os.path.join(self.output_dir, "ground_truth_anomalies.json")
        with open(truth_path, "w", encoding="utf-8") as f:
            json.dump(truth_payload, f, indent=2)


if __name__ == "__main__":
    gen = SyntheticAuditDataGenerator()
    gen.generate_all()
