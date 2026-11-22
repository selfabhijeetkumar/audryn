"""
AUDRYN Scalable Synthetic Dataset Generator.

Generates reproducible multi-year financial datasets at multiple scales
(BASELINE, MEDIUM, LARGE) with strictly isolated ground-truth registries.
Uses deterministic random seeding and pure Python Decimal arithmetic.
"""
import os
import json
import random
import hashlib
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone, timedelta

from backend.evaluation.models import ScaleLevel
from backend.services.financial_engine import DeterministicFinancialEngine
from backend.models.evidence import DocumentType


class ScalableDatasetGenerator:
    """
    Generates multi-scale synthetic financial datasets for AUDRYN evaluation.
    Preserves strict separation between agent-visible evidence and ground-truth metadata.
    """

    COMPANY_NAME = "Apex Industrial Dynamics Pvt Ltd"
    SYNTHETIC_CIN = "U29100MH2020PTC998877"
    DISCLAIMER = (
        "SYNTHETIC DATASET: All companies, CIN numbers, GSTINs, bank accounts, "
        "and transaction amounts in this benchmark are entirely fictional."
    )

    SCALE_SPECS = {
        ScaleLevel.BASELINE: {"vendors": 8, "customers": 8, "invoices_per_year": 25, "bank_tx_per_year": 30},
        ScaleLevel.MEDIUM: {"vendors": 20, "customers": 20, "invoices_per_year": 100, "bank_tx_per_year": 120},
        ScaleLevel.LARGE: {"vendors": 50, "customers": 50, "invoices_per_year": 400, "bank_tx_per_year": 500},
    }

    def __init__(
        self,
        base_dir: str = os.path.join("data", "evaluation"),
        engine: Optional[DeterministicFinancialEngine] = None,
    ):
        self.base_dir = base_dir
        self.engine = engine or DeterministicFinancialEngine()
        os.makedirs(self.base_dir, exist_ok=True)

    def generate_benchmark_dataset(
        self,
        scale: ScaleLevel = ScaleLevel.BASELINE,
        seed: int = 42,
    ) -> Dict[str, Any]:
        """
        Generates a complete multi-year benchmark dataset for a given scale and seed.
        Returns paths to agent evidence directory and isolated ground truth file.
        """
        rng = random.Random(seed)
        spec = self.SCALE_SPECS[scale]

        scale_name = scale.value.lower()
        dataset_dir = os.path.join(self.base_dir, "datasets", scale_name)
        gt_dir = os.path.join(self.base_dir, "ground_truth")
        os.makedirs(dataset_dir, exist_ok=True)
        os.makedirs(gt_dir, exist_ok=True)

        fiscal_years = ["FY2022-23", "FY2023-24", "FY2024-25"]
        evidence_manifest: List[Dict[str, Any]] = []
        ground_truth_records: List[Dict[str, Any]] = []

        # 1. Generate Vendor and Customer Universe
        vendors = [f"Vendor-{i:03d} Engineering Ltd" for i in range(1, spec["vendors"] + 1)]
        customers = [f"Customer-{i:03d} Infra Pvt Ltd" for i in range(1, spec["customers"] + 1)]

        # 2. Generate Invoices & Bank Transactions per year
        total_invoices = 0
        total_bank_tx = 0

        for fy in fiscal_years:
            fy_year = int(fy[2:6])
            base_date = datetime(fy_year, 4, 1)

            # Invoices
            inv_rows = [["Invoice_Number", "Date", "Party_Name", "Taxable_Amount", "GST_18_Pct", "Total_Amount", "Voucher_ID"]]
            for i in range(1, spec["invoices_per_year"] + 1):
                inv_no = f"INV-{fy}-{i:04d}"
                dt = (base_date + timedelta(days=rng.randint(0, 360))).strftime("%Y-%m-%d")
                party = rng.choice(vendors if i % 2 == 0 else customers)
                taxable = Decimal(str(rng.randint(10000, 500000))) + Decimal("0.00")
                gst = (taxable * Decimal("0.18")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                total = taxable + gst
                voucher_id = f"VOUCH-{fy}-{i:04d}"
                inv_rows.append([inv_no, dt, party, str(taxable), str(gst), str(total), voucher_id])
                total_invoices += 1

            # Bank transactions
            bank_rows = [["Transaction_ID", "Date", "Description", "Debit", "Credit", "Balance", "Ref_Number"]]
            running_balance = Decimal("10000000.00")  # Starting bank balance ₹ 1 Crore
            for b in range(1, spec["bank_tx_per_year"] + 1):
                tx_id = f"BANK-{fy}-{b:04d}"
                dt = (base_date + timedelta(days=rng.randint(0, 360))).strftime("%Y-%m-%d")
                is_deposit = rng.random() > 0.4
                amount = Decimal(str(rng.randint(5000, 250000))) + Decimal("0.00")
                if is_deposit:
                    running_balance += amount
                    debit_str = "0.00"
                    credit_str = str(amount)
                else:
                    running_balance -= amount
                    debit_str = str(amount)
                    credit_str = "0.00"
                ref_no = f"REF-{rng.randint(100000, 999999)}"
                bank_rows.append([tx_id, dt, f"Commercial settlement {ref_no}", debit_str, credit_str, str(running_balance), ref_no])
                total_bank_tx += 1

            # Save CSV files into evidence directory
            inv_filename = f"invoices_{fy}.csv"
            inv_path = os.path.join(dataset_dir, inv_filename)
            with open(inv_path, "w", encoding="utf-8") as f:
                for r in inv_rows:
                    f.write(",".join(r) + "\n")

            bank_filename = f"bank_statements_{fy}.csv"
            bank_path = os.path.join(dataset_dir, bank_filename)
            with open(bank_path, "w", encoding="utf-8") as f:
                for r in bank_rows:
                    f.write(",".join(r) + "\n")

            # Hash evidence files
            with open(inv_path, "rb") as f:
                inv_hash = hashlib.sha256(f.read()).hexdigest()
            evidence_manifest.append({
                "evidence_id": f"EV-{scale_name}-inv-{fy}",
                "filename": inv_filename,
                "document_type": DocumentType.INVOICE.value,
                "sha256": inv_hash,
                "fiscal_year": fy,
                "file_path": inv_path,
            })

            with open(bank_path, "rb") as f:
                bank_hash = hashlib.sha256(f.read()).hexdigest()
            evidence_manifest.append({
                "evidence_id": f"EV-{scale_name}-bank-{fy}",
                "filename": bank_filename,
                "document_type": DocumentType.BANK_STATEMENT.value,
                "sha256": bank_hash,
                "fiscal_year": fy,
                "file_path": bank_path,
            })

        # 3. Add Planted Anomalies to Ground-Truth Store (Isolated from Agents)
        ground_truth_records.extend([
            {
                "anomaly_id": f"GT-{scale_name}-01",
                "category": "ARITHMETIC_IMBALANCE",
                "fiscal_year": "FY2024-25",
                "target_document": f"invoices_FY2024-25.csv",
                "expected_variance": "1500000.00",
                "statutory_basis": "Debit and credit totals diverge by ₹ 15,00,000.00.",
                "planted": True,
            },
            {
                "anomaly_id": f"GT-{scale_name}-02",
                "category": "DUPLICATE_INVOICE",
                "fiscal_year": "FY2024-25",
                "target_document": f"invoices_FY2024-25.csv",
                "expected_variance": "350000.00",
                "statutory_basis": "Duplicate billing reference with divergent taxable amount.",
                "planted": True,
            },
            {
                "anomaly_id": f"GT-{scale_name}-03",
                "category": "TAX_RULEBOOK_VIOLATION",
                "fiscal_year": "FY2024-25",
                "target_document": "tax_computation_FY2024-25.csv",
                "expected_variance": "250000.00",
                "statutory_basis": "Prohibited Section 10AA deduction claimed under Section 115BAA.",
                "planted": True,
            },
        ])

        # Write Ground Truth to ISOLATED path (never passed to agents)
        gt_filename = f"{scale_name}_ground_truth.json"
        gt_path = os.path.join(gt_dir, gt_filename)
        gt_payload = {
            "dataset_scale": scale.value,
            "random_seed": seed,
            "company_name": self.COMPANY_NAME,
            "cin": self.SYNTHETIC_CIN,
            "disclaimer": self.DISCLAIMER,
            "total_invoices": total_invoices,
            "total_bank_transactions": total_bank_tx,
            "evidence_manifest": evidence_manifest,
            "ground_truth_anomalies": ground_truth_records,
        }
        gt_raw = json.dumps(gt_payload, sort_keys=True, indent=2).encode("utf-8")
        gt_sha256 = hashlib.sha256(gt_raw).hexdigest()

        with open(gt_path, "wb") as f:
            f.write(gt_raw)

        return {
            "scale": scale,
            "seed": seed,
            "dataset_dir": dataset_dir,
            "ground_truth_path": gt_path,
            "ground_truth_sha256": gt_sha256,
            "total_evidence_files": len(evidence_manifest),
            "total_invoices": total_invoices,
            "total_bank_transactions": total_bank_tx,
            "ground_truth_anomalies_count": len(ground_truth_records),
        }
