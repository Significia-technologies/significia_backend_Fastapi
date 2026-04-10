# Financial Analysis Formulas - Documentation

This document explains the mathematical formulas and logic implemented in `financial_calculator.py` for generating comprehensive financial reports, supplemented with practical examples.

---

## 1. Core Financial Math

The foundation of all projections relies on standard time-value-of-money formulas.

### Future Value (FV)
Calculates the value of an asset at a specific date in the future.
$$FV = PV \times (1 + \frac{r}{100})^n$$

> **Example**: 
> - **PV**: ₹1,00,000 (Investment today)
> - **r**: 12% (Expected annual return)
> - **n**: 10 years
> - **Calculation**: $1,00,000 \times (1.12)^{10} \approx \mathbf{₹3,10,585}$

### Present Value (PV)
Calculates the current worth of a future sum of money.
$$PV = \frac{FV}{(1 + \frac{r}{100})^n}$$

---

## 2. Human Life Value (HLV)

Total life insurance cover needed to protect the family's lifestyle.

### Income Replacement Method
Calculates the PV of future income lost until retirement.
- **Formula**: `calculate_annuity_pv(Future Income, Pre-Retirement Rate, Years)`

> **Example**:
> - **Annual Income**: ₹12,00,000
> - **SOL %**: 80% (Replacement needed: ₹9,60,000/year)
> - **Current Age**: 35 | **Retirement Age**: 60 (Years: 25)
> - **Return Rate**: 12%
> - **Result**: $\mathbf{₹75,29,401}$ (Gross HLV)

### Net HLV (Gap Analysis)
$$ \text{Net HLV} = \max(0, \text{Gross HLV} - \text{Existing Financial Assets} + \text{Current Liabilities} - \text{Existing Life Cover}) $$

---

## 3. Medical Corpus Requirements

### Future Corpus Needed
$$ \text{Medical Corpus at Milestone} = \text{Current Medical Cover} \times (1 + \text{Medical Inflation})^n $$

> **Example**:
> - **Current Cover**: ₹5,00,000
> - **Medical Inflation**: 10%
> - **Years to Retirement**: 20
> - **Calculation**: $5,00,000 \times (1.10)^{20} \approx \mathbf{₹33,63,750}$
> - *If the user has ₹10,00,000 cover today, they still need to plan for a ~₹23L gap at retirement.*

---

## 4. Retirement Planning (Deep Dive)

Determines the corpus required to maintain the desired standard of living post-retirement using a **Growing Annuity**.

### Corpus Needed at Retirement
$$ \text{Corpus} = E_{retirement} \times \frac{1 - (\frac{1+i}{1+r})^n}{r-i} $$

> **Example**:
> - **Annual Expenses Today**: ₹6,00,000
> - **Years to Retirement**: 25 (Inflation 6%)
> - **$E_{retirement}$**: $6,00,000 \times (1.06)^{25} \approx ₹25,75,123$ (First year expense at age 60)
> - **Post-Retirement Return (r)**: 8%
> - **Post-Retirement Inflation (i)**: 6%
> - **Years in Retirement (n)**: 25 (Age 60 to 85)
> - **Calculation Factor**: $\frac{1 - (\frac{1.06}{1.08})^{25}}{0.08 - 0.06} \approx 18.66$
> - **Total Corpus Needed**: $25,75,123 \times 18.66 \approx \mathbf{₹4,80,51,795}$

---

## 5. Child Goals (Education & Marriage)

### Future Cost & Monthly Investment
$$ \text{Monthly SIP} = \frac{\text{Net Future Cost}}{\text{FV Factor}} $$

> **Example (Higher Education)**:
> - **Current Cost**: ₹10,00,000
> - **Inflation**: 10% | **Years to Goal**: 15
> - **Future Cost**: ₹41,77,248
> - **Target Monthly Saving (at 12%)**: $\approx \mathbf{₹8,350/\text{month}}$

---

## 6. Financial Health Score (Evaluation Logic)

| Pillar | Example Scenario | Pts Earned |
| :--- | :--- | :--- |
| **Savings Rate** | Client saves ₹30k out of ₹1L income (30%) | **30/30** |
| **Net Worth** | Client has ₹60L assets vs ₹12L income (5x) | **30/30** |
| **Insurance** | Client needs ₹1Cr, has ₹50L (Partial) | **10/20** |
| **Retirement** | Savings on track for 40% of target corpus | **10/20** |
| **Emergency Fund** | Has ₹2L in bank, 6 months expenses = ₹3L | **0/10** |
| **TOTAL SCORE** | | **80/100** |

---
