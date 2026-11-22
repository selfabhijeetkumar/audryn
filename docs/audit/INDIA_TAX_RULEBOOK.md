# AUDRYN — Versioned Indian Tax Rulebook Engine

> **Document Type:** Statutory Tax Rulebook Technical Specification  
> **Status:** ACTIVE & PRODUCTION-GRADE  
> **Jurisdiction:** Republic of India (Central Board of Direct Taxes — CBDT)  
> **Primary Statutes:** Income-tax Act, 1961 (Applicable for FY 2023-24, FY 2024-25, FY 2025-26)  
> **Forward Transition Statute:** Income-tax Act, 2025 (Enacted for FY 2026-27 / AY 2027-28 onwards)  
> **Implementation Engine:** Python `Decimal` (`ROUND_HALF_UP`, 2 decimal places) — Strictly Zero LLM Arithmetic.

---

## 1. Statutory Scope & Legislative Framework

The AUDRYN Indian Tax Rulebook provides a deterministic, versioned, and legally audited calculation engine for corporate tax assessment, statutory depreciation blocks, book-versus-tax reconciliation (Form 3CD), and jurisdiction-specific compliance gates.

### 1.1 Supported Assessment Years and Governing Enactments

| Financial Year (FY) | Assessment Year (AY) | Governing Statute | Status in AUDRYN |
|---|---|---|---|
| **FY 2023-24** (01/04/2023 – 31/03/2024) | AY 2024-25 | Income-tax Act, 1961 | Fully Active & Validated |
| **FY 2024-25** (01/04/2024 – 31/03/2025) | AY 2025-26 | Income-tax Act, 1961 | Fully Active & Validated |
| **FY 2025-26** (01/04/2025 – 31/03/2026) | AY 2026-27 | Income-tax Act, 1961 | Fully Active & Validated |
| **FY 2026-27** (01/04/2026 – 31/03/2027) | AY 2027-28 | Income-tax Act, 2025 | **Guarded / Blocked** until statutory rules and schedules are gazetted |

### 1.2 Forward-Compatibility Guard for Income-tax Act, 2025

The Parliament of India passed the **Income-tax Act, 2025** to replace the six-decade-old Income-tax Act, 1961 with effect from 1 April 2026. 

AUDRYN explicitly implements an architectural forward-compatibility guard:
- **No Automatic Carryover:** Rules, sections, thresholds, and case law under the 1961 Act are strictly prohibited from silent carryover into FY 2026-27.
- **Fail-Safe Exception:** Invocations targeting FY 2026-27 or later automatically raise `ValueError("Tax rules for FY2026-27 under Income-tax Act, 2025 are pending statutory rule gazettal...")`.
- **Audit Defensibility:** Prevents unauthorized extrapolation of tax liabilities across historical regime boundaries.

---

## 2. Section 115BAA — Concessional Corporate Tax Regime

Section 115BAA was inserted by the Taxation Laws (Amendment) Act, 2019 to provide a simplified, lower corporate tax rate for domestic companies.

### 2.1 Statutory Rate Computation

Under Section 115BAA, corporate tax is computed with mandatory surcharges and cess:
1. **Base Corporate Tax Rate:** `22.00%` (`0.22`)
2. **Mandatory Surcharge:** Flat `10.00%` on base tax (`0.10 * 22% = 2.20%`), irrespective of the level of total income.
3. **Subtotal Rate:** `24.20%` (`0.242`)
4. **Health & Education Cess:** Flat `4.00%` on the aggregate of base tax and surcharge (`0.04 * 24.20% = 0.968%`).
5. **Effective Statutory Tax Rate:** Exactly **`25.168%`** (`0.25168`).

```python
# Exact deterministic calculation in AUDRYN:
base_tax = (taxable_income * Decimal("0.22")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
surcharge = (base_tax * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
cess = ((base_tax + surcharge) * Decimal("0.04")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
total_tax_payable = base_tax + surcharge + cess
```

### 2.2 Mandatory Eligibility Conditions & Prohibitions

To exercise the option under Section 115BAA, a corporate assessee must fulfill strict statutory requirements:

1. **Domestic Company Status:** The entity must be incorporated in India under the Companies Act, 2013 or previous company laws. Foreign corporate entities (`is_domestic_company=False`) are disqualified.
2. **Timely Filing of Form 10-IC:** The option must be exercised in Form 10-IC electronically on or before the due date specified under Section 139(1) for furnishing the return of income. Failure to file Form 10-IC invalidates Section 115BAA eligibility.
3. **Non-Revocable Election:** Once exercised, the option cannot be subsequently withdrawn for the same or any other previous year.
4. **Strictly Prohibited Deductions & Exemptions:**
   - **Section 10AA:** Deductions for newly established units in Special Economic Zones (SEZ).
   - **Section 32(1)(iia):** Additional depreciation on new machinery or plant (typically 20%).
   - **Section 32AD:** Investment in new plant or machinery in notified backward areas.
   - **Section 33AB / 33ABA:** Tea, coffee, rubber development / Site restoration accounts.
   - **Section 35(1)(ii)/(iia)/(iii), 35(2AA), 35(2AB):** Weighted deductions for scientific research.
   - **Section 35CCC / 35CCD:** Agricultural extension / skill development projects.
   - **Chapter VI-A (Part C deductions):** All incentives under heading "C.—Deductions in respect of certain incomes" (e.g., Section 80-IA, 80-IB, 80-IC, 80JJA) **except Section 80JJAA** (employment generation) and **Section 80M** (inter-corporate dividends).
5. **No Set-off of Unabsorbed Depreciation or Carried Forward Loss:** Any brought-forward loss or unabsorbed depreciation attributable to any of the prohibited deductions cannot be set off.

---

## 3. Section 32 — Depreciation Rules & Asset Block Schedule

Depreciation for income tax purposes is allowed on the **Written Down Value (WDV)** of "blocks of assets" under Section 32 read with Rule 5 of the Income-tax Rules, 1962.

### 3.1 Standard Statutory Blocks

AUDRYN configures the standard statutory depreciation blocks:

| Asset Block Category | Statutory WDV Rate | Description & Scope |
|---|---|---|
| **PLANT_MACHINERY** | `15.00%` | General industrial plant, machinery, motor cars, office equipment. |
| **COMPUTERS_SOFTWARE** | `40.00%` | Computers, laptops, servers, peripherals, and system/application software. |
| **BUILDINGS_OFFICE** | `10.00%` | Non-residential buildings, factory buildings, administrative offices. |
| **BUILDINGS_RESIDENTIAL**| `5.00%` | Residential buildings for company accommodation/staff quarters. |
| **FURNITURE_FIXTURES** | `10.00%` | Furniture, electrical fittings, partitions, office furnishings. |
| **INTANGIBLES** | `25.00%` | Patents, copyrights, trademarks, licenses, franchises. |

### 3.2 The 180-Day "Put to Use" Half-Rate Rule (Second Proviso to Section 32(1))

Under the second proviso to Section 32(1):
- Where an asset is acquired by the assessee during the previous year and is **put to use for less than 180 days** in that financial year, the depreciation allowable on that addition is restricted to **50% of the prescribed block rate**.
- Where the addition is put to use for **180 days or more**, the **full prescribed block rate (100%)** applies.

```python
# Deterministic Half-Rate Application:
if days_put_to_use < 180:
    effective_rate = block_rate / Decimal("2.0")
else:
    effective_rate = block_rate
```

### 3.3 Block Mechanics and Capital Gains (Section 50)

AUDRYN evaluates statutory block depreciation using the standard schedule:
$$\text{Base for Depreciation} = \text{Opening WDV} + \text{Additions (Cost)} - \text{Realization from Disposals/Sale proceeds}$$

1. **Pool Depletion (Excess Realization):** If realization from disposals exceeds $(\text{Opening WDV} + \text{Additions})$, the allowable depreciation is **`₹ 0.00`**, closing WDV becomes **`₹ 0.00`**, and the excess is recognized as Short-Term Capital Gain under Section 50.
2. **Block Extinction:** If all physical assets in the block are sold during the year, even if net value remains positive, allowable depreciation is **`₹ 0.00`** and the residual value is treated as Short-Term Capital Loss under Section 50.

---

## 4. Book vs. Tax Depreciation Reconciliation (Form 3CD Clause 17/18)

Tax Audit under Section 44AB requires reporting the statutory reconciliation between **Accounting Depreciation (Companies Act, 2013)** and **Tax Depreciation (Section 32, Income-tax Act, 1961)**.

### 4.1 Reconciliation Architecture

The reconciliation follows standard direct tax tie-out rules:

```
Net Profit as per Profit & Loss Account (Ind AS / AS)
  (+) Book Depreciation debited to P&L (Form 3CD Clause 17)
  (-) Statutory Tax Depreciation allowable (Form 3CD Clause 18)
  (=) Net Adjusted Profit subject to other Chapter IV adjustments
```

### 4.2 AUDRYN Reconciliation Record Schema

```json
{
  "fiscal_year": "FY2024-25",
  "book_depreciation_inr": "1850000.00",
  "tax_depreciation_inr": "1425000.00",
  "net_timing_difference_inr": "425000.00",
  "direction": "ADD_BACK_TO_BOOK_PROFIT",
  "form_3cd_clause_17_reference": "Depreciation debited to P&L Account: ₹ 18,50,000.00",
  "form_3cd_clause_18_reference": "Depreciation allowable under Section 32: ₹ 14,25,000.00",
  "deferred_tax_impact": "Generates Deferred Tax Liability (DTL) / Reverses Deferred Tax Asset (DTA)"
}
```

---

## 5. Summary of Compliance Checks

Every company evaluated through AUDRYN is subjected to automated validation gates:
1. `validate_section_115baa_eligibility()` — enforces Form 10-IC verification and prohibited deduction scans.
2. `compute_corporate_tax()` — computes exact `25.168%` tax liability or falls back to normal provisions (MAT under Section 115JB).
3. `compute_block_depreciation()` — calculates asset-by-asset 180-day half-rate WDV depreciation.
4. `reconcile_book_vs_tax_depreciation()` — generates Form 3CD tie-out records.
5. `verify_statutory_act_boundary()` — enforces legal boundary between 1961 Act and 2025 Act.
