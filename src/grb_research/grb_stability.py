"""
Created on Mar 17 20:57:08 2026

GRB Spectral Model Comparison
------------------------------
Statistical tests for comparing nested spectral models using your existing
Model dataclass. Requires only cstat, dof, parameters, and covariance_matrix.

Tests implemented
-----------------
  - Likelihood Ratio Test (LRT) via Δcstat ~ χ²(Δk)
  - AIC, AICc, BIC and their deltas
  - AIC model weights
  - BIC Bayes factor approximation
  - BB normalization significance (z-score)
  - Parameter stability (shift in units of combined sigma)
  - Covariance/correlation matrix analysis (condition number, BB correlations)

Usage
-----
    result = ModelComparison(simple_model, complex_model, bb_param_names=["kT", "norm_bb"])
    result.report()
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats

# -----------------------------------------------------------------------------
# Thresholds (edit to match your pipeline conventions)
# -----------------------------------------------------------------------------

DELTA_CSTAT_THRESHOLD = 25.0  # pipeline detection threshold
BB_SIGMA_THRESHOLD = 3.0  # minimum sigma for BB normalization
HIGH_CORR_THRESHOLD = 0.9  # |ρ| above this flags degeneracy


# -----------------------------------------------------------------------------
# Result containers
# -----------------------------------------------------------------------------

@dataclass
class LRTResult:
    delta_cstat: float
    delta_k: int
    p_value: float
    sigma: float
    detected: bool  # True if delta_cstat > threshold


@dataclass
class ICResult:
    aic_simple: float
    aic_complex: float
    aic_c_simple: float
    aic_c_complex: float
    bic_simple: float
    bic_complex: float
    delta_aic: float  # positive → complex is better
    delta_aic_c: float
    delta_bic: float
    w_simple: float  # AIC model weight
    w_complex: float
    bayes_factor: float  # exp(ΔBIC/2) approximation


@dataclass
class BBSignificanceResult:
    param_name: str
    value: float
    error: float
    z_score: float
    significant: bool  # z > BB_SIGMA_THRESHOLD


@dataclass
class ParamShift:
    name: str
    v_simple: float
    v_complex: float
    sigma: float  # shift in units of combined error
    flag: bool  # True if shift > 3σ


@dataclass
class CovarianceAnalysis:
    condition_number: float  # raw — sensitive to parameter scaling
    condition_number_scaled: float  # from correlation matrix — scaling-independent
    is_ill_conditioned: bool  # now based on the scaled version
    correlation_matrix: np.ndarray
    param_names: list
    flagged_pairs: list  # pairs with |ρ| > HIGH_CORR_THRESHOLD
    bb_correlations: Optional[dict]  # {(bb_param, continuum_param): ρ}


# -----------------------------------------------------------------------------
# Main class
# -----------------------------------------------------------------------------


def scaled_condition_number(cov):
    """
    Normalize by parameter scales before computing condition number.
    Equivalent to computing the condition number of the correlation matrix.
    """
    std = np.sqrt(np.diag(cov))
    corr = cov / np.outer(std, std)
    np.fill_diagonal(corr, 1.0)
    # np.nan_to_num(corr, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
    return corr, np.linalg.cond(corr)


class ModelComparison:
    """
    Compare a simple (nested) model against its complex extension.

    Parameters
    ----------
    simple : Model
        The simpler model (fewer parameters), e.g., Band.
    complex_ : Model
        The model with extra components, e.g., Band+BB.
    bb_param_names : list[str], optional
        Parameter names belonging to the extra BB component in complex_.
        Matching is case-insensitive and partial, e.g. "norm_bb" will match
        a parameter named "norm_BB_1".
    """

    def __init__(self, simple, complex_, bb_param_names: Optional[list] = None):
        self.simple = simple
        self.complex = complex_
        self.bb_names = [s.lower() for s in (bb_param_names or [])]

        self._k_simple = len(simple.parameters)
        self._k_complex = len(complex_.parameters)
        self._delta_k = self._k_complex - self._k_simple

        if self._delta_k <= 0:
            raise ValueError(
                f"complex_ must have more parameters than simple. "
                f"Got Δk = {self._delta_k}."
            )

        self._delta_cstat = simple.cstat - complex_.cstat

        # run all tests on construction
        self._lrt = self._run_lrt()
        self._ic = self._run_ic()
        self._bb_sig = self._run_bb_significance()
        self._shifts = self._run_param_stability()
        self._cov = self._run_covariance_analysis()

    # -- public properties ----------------------------------------------------

    @property
    def lrt(self) -> LRTResult:
        return self._lrt

    @property
    def information_criteria(self) -> ICResult:
        return self._ic

    @property
    def bb_significance(self) -> list:
        return self._bb_sig

    @property
    def parameter_stability(self) -> list:
        return self._shifts

    @property
    def covariance_analysis(self) -> Optional[CovarianceAnalysis]:
        return self._cov

    # -- internal helpers -----------------------------------------------------

    def _n(self, model) -> int:
        """Effective sample size for a model."""
        return model.dof + len(model.parameters)

    def _aic(self, model) -> float:
        return model.cstat + 2 * len(model.parameters)

    def _aicc(self, model) -> float:
        k = len(model.parameters)
        n = self._n(model)
        return self._aic(model) + (2 * k * (k + 1)) / (n - k - 1)

    def _bic(self, model) -> float:
        k = len(model.parameters)
        n = self._n(model)
        return model.cstat + k * np.log(n)

    def _is_bb_param(self, name: str) -> bool:
        if not self.bb_names:
            return False
        return any(b in name.lower() for b in self.bb_names)

    # -- test implementations -------------------------------------------------

    def _run_lrt(self) -> LRTResult:
        dc = self._delta_cstat
        dk = self._delta_k
        p = 1.0 - stats.chi2.cdf(dc, df=dk)
        p = max(p, 1e-300)
        sigma = abs(stats.norm.ppf(p / 2.0))
        return LRTResult(
            delta_cstat=dc,
            delta_k=dk,
            p_value=p,
            sigma=sigma,
            detected=dc > DELTA_CSTAT_THRESHOLD,
        )

    def _run_ic(self) -> ICResult:
        aic_s = self._aic(self.simple)
        aic_c = self._aic(self.complex)
        aic_c_s = self._aicc(self.simple)
        aicc_c = self._aicc(self.complex)
        bic_s = self._bic(self.simple)
        bic_c = self._bic(self.complex)

        d_aic = aic_s - aic_c  # positive → complex wins
        d_aic_c = aic_c_s - aicc_c
        d_bic = bic_s - bic_c

        # AIC model weights
        min_aic = min(aic_s, aic_c)
        e_s = np.exp(-0.5 * (aic_s - min_aic))
        e_c = np.exp(-0.5 * (aic_c - min_aic))
        w_s = e_s / (e_s + e_c)
        w_c = e_c / (e_s + e_c)

        # BIC Bayes factor (Kass & Raftery approximation)
        bf = np.exp(d_bic / 2.0)  # > 1 favours complex

        return ICResult(
            aic_simple=aic_s, aic_complex=aic_c,
            aic_c_simple=aic_c_s, aic_c_complex=aicc_c,
            bic_simple=bic_s, bic_complex=bic_c,
            delta_aic=d_aic, delta_aic_c=d_aic_c,
            delta_bic=d_bic,
            w_simple=w_s, w_complex=w_c,
            bayes_factor=bf,
        )

    def _run_bb_significance(self) -> list:
        results = []
        for p in self.complex.parameters:
            if self._is_bb_param(p.name):
                z = (p.value / p.error) if p.error else np.inf
                results.append(BBSignificanceResult(
                    param_name=p.name,
                    value=p.value,
                    error=p.error,
                    z_score=z,
                    significant=abs(z) >= BB_SIGMA_THRESHOLD,
                ))
        return results

    def _run_param_stability(self) -> list:
        """
        For every parameter shared between both models (matched by name,
        case-insensitive), compute the shift in units of combined sigma.
        """
        simple_map = {p.name.lower(): p for p in self.simple.parameters}
        complex_map = {p.name.lower(): p for p in self.complex.parameters}

        shifts = []
        for name_l, ps in simple_map.items():
            if name_l in complex_map:
                pc = complex_map[name_l]
                denom = np.sqrt(ps.error ** 2 + pc.error ** 2)

                # both fixed
                if denom == 0:
                    if ps.value == pc.value:
                        continue  # same fixed value — no shift, skip
                    else:
                        shift = np.inf  # fixed to different values — flag it
                        shifts.append(ParamShift(
                            name=ps.name,
                            v_simple=ps.value,
                            v_complex=pc.value,
                            sigma=shift,
                            flag=True,  # always flag — physically suspicious
                        ))
                        continue

                shift = abs(ps.value - pc.value) / denom
                shifts.append(ParamShift(
                    name=ps.name,
                    v_simple=ps.value,
                    v_complex=pc.value,
                    sigma=shift,
                    flag=shift > 3.0,
                ))

        return shifts

    def _run_covariance_analysis(self) -> Optional[CovarianceAnalysis]:
        """Analyze the covariance matrix of the complex model."""
        if self.complex.covariance_matrix is None:
            return None

        cov = self.complex.covariance_matrix_value  # symmetric ndarray
        names = [p.name for p in self.complex.parameters]
        errors = [p.error for p in self.complex.parameters]

        # ── exclude fixed parameters (σ = 0) ────────────────────────────
        free_idx = [i for i, e in enumerate(errors) if e > 0]

        if len(free_idx) < 2:
            return None  # nothing meaningful to analyze

        cov = cov[np.ix_(free_idx, free_idx)]
        names = [names[i] for i in free_idx]

        n = len(names)

        if cov.shape != (n, n):
            return None

        # condition number — high value signals near-degeneracy
        cond_raw = np.linalg.cond(cov)
        corr, cond_scaled = scaled_condition_number(cov)
        # flag highly correlated off-diagonal pairs

        flagged = []
        for i in range(n):
            for j in range(i + 1, n):
                if abs(corr[i, j]) >= HIGH_CORR_THRESHOLD:
                    flagged.append((names[i], names[j], float(corr[i, j])))

        # BB ↔ continuum correlations
        bb_corr = {}
        if self.bb_names:
            bb_idx = [i for i, nm in enumerate(names) if self._is_bb_param(nm)]
            cont_idx = [i for i, nm in enumerate(names) if not self._is_bb_param(nm)]
            for bi in bb_idx:
                for ci in cont_idx:
                    bb_corr[(names[bi], names[ci])] = float(corr[bi, ci])

        return CovarianceAnalysis(
            condition_number=cond_raw,
            condition_number_scaled=cond_scaled,
            is_ill_conditioned=cond_scaled > 1e4,
            correlation_matrix=corr,
            param_names=names,
            flagged_pairs=flagged,
            bb_correlations=bb_corr if bb_corr else None,
        )

    # -- verdict helpers ------------------------------------------------------

    @staticmethod
    def _aic_label(delta: float) -> str:
        """Burnham & Anderson ΔAIC evidence label (magnitude)."""
        a = abs(delta)
        if a < 2:  return "negligible"
        if a < 6:  return "considerable"
        if a < 10: return "strong"
        return "decisive"

    @staticmethod
    def _bic_label(delta: float) -> str:
        """Kass & Raftery ΔBIC evidence label (magnitude)."""
        a = abs(delta)
        if a < 2:  return "not worth mentioning"
        if a < 6:  return "positive"
        if a < 10: return "strong"
        return "very strong"

    def _overall_verdict(self) -> str:
        votes_c = 0
        votes_s = 0

        # LRT / pipeline threshold
        if self._lrt.detected:
            votes_c += 1
        else:
            votes_s += 1

        # AIC
        if self._ic.delta_aic > 0:
            votes_c += 1
        else:
            votes_s += 1

        # BIC
        if self._ic.delta_bic > 0:
            votes_c += 1
        else:
            votes_s += 1

        # BB significance
        for bb in self._bb_sig:
            if bb.significant:
                votes_c += 1
            else:
                votes_s += 1

        winner = self.complex.name if votes_c > votes_s else self.simple.name
        return f"{winner}  ({votes_c} vs {votes_s} tests favour complex model)"

    # -- public report --------------------------------------------------------

    def report(self, decimals: int = 3) -> None:
        """Print a formatted summary of all statistical tests."""
        sep = "-" * 68
        sep2 = "═" * 68

        def row(label, value, note=""):
            note_str = f"  [{note}]" if note else ""
            print(f"  {label:<34} {value}{note_str}")

        print(sep2)
        print(f"  MODEL COMPARISON")
        print(f"  Simple  :  {self.simple.name}   "
              f"(k={self._k_simple}, cstat={self.simple.cstat:.{decimals}f}, dof={self.simple.dof})")
        print(f"  Complex :  {self.complex.name}  "
              f"(k={self._k_complex}, cstat={self.complex.cstat:.{decimals}f}, dof={self.complex.dof})")
        print(sep2)

        # -- LRT --------------------------------------------------------------
        lrt = self._lrt
        print(f"\n  LIKELIHOOD RATIO TEST")
        print(sep)
        row("Δcstat", f"{lrt.delta_cstat:.{decimals}f}",
            f"threshold = {DELTA_CSTAT_THRESHOLD}")
        row("Δk", str(lrt.delta_k))
        row("p-value", f"{lrt.p_value:.3e}")
        row("Significance", f"{lrt.sigma:.2f}σ")
        row("Pipeline detect?", "YES ✓" if lrt.detected else "NO  ✗")

        # -- IC ---------------------------------------------------------------
        ic = self._ic
        print(f"\n  INFORMATION CRITERIA")
        print(sep)
        print(f"  {'':34} {'Simple':>12}   {'Complex':>12}")
        for label, vs, vc in [
            ("AIC", ic.aic_simple, ic.aic_complex),
            ("AICc", ic.aic_c_simple, ic.aic_c_complex),
            ("BIC", ic.bic_simple, ic.bic_complex),
        ]:
            print(f"  {label:<34} {vs:>12.{decimals}f}   {vc:>12.{decimals}f}")
        print(sep)
        row("ΔAIC  (+ favours complex)", f"{ic.delta_aic:+.{decimals}f}",
            self._aic_label(ic.delta_aic))
        row("ΔAICc (+ favours complex)", f"{ic.delta_aic_c:+.{decimals}f}",
            self._aic_label(ic.delta_aic_c))
        row("ΔBIC  (+ favours complex)", f"{ic.delta_bic:+.{decimals}f}",
            self._bic_label(ic.delta_bic))
        row("AIC weight — simple", f"{ic.w_simple * 100:.1f}%")
        row("AIC weight — complex", f"{ic.w_complex * 100:.1f}%")
        row("BIC Bayes factor (≈)", f"{ic.bayes_factor:.2f}",
            "> 1 favours complex")

        # -- BB significance ---------------------------------------------------
        if self._bb_sig:
            print(f"\n  BB COMPONENT SIGNIFICANCE  (threshold = {BB_SIGMA_THRESHOLD}σ)")
            print(sep)
            for bb in self._bb_sig:
                flag = "✓" if bb.significant else "✗  below threshold"
                row(bb.param_name,
                    f"{bb.value:.3e} ± {bb.error:.3e}",
                    f"{bb.z_score:.2f}σ  {flag}")

        # -- parameter stability -----------------------------------------------
        if self._shifts:
            print(f"\n  PARAMETER STABILITY")
            print(sep)
            print(f"  {'Parameter':<18} {'Simple':>14}  {'Complex':>14}  {'Shift':>8}")
            for s in self._shifts:
                flag = "  ← flag" if s.flag else ""
                print(f"  {s.name:<18} {s.v_simple:>14.4g}  {s.v_complex:>14.4g}  "
                      f"{s.sigma:>6.2f}σ{flag}")

        # -- covariance analysis -----------------------------------------------
        cov_a = self._cov
        if cov_a is not None:
            print(f"\n  COVARIANCE ANALYSIS  (complex model)")
            print(sep)
            row("Condition number (scaled)",
                f"{cov_a.condition_number_scaled:.2e}",
                "ILL-CONDITIONED ✗" if cov_a.is_ill_conditioned else "well-conditioned ✓")

            if cov_a.flagged_pairs:
                print(f"\n  High-correlation pairs  (|ρ| ≥ {HIGH_CORR_THRESHOLD}):")
                for p1, p2, rho in cov_a.flagged_pairs:
                    print(f"    {p1}  ↔  {p2}:  ρ = {rho:+.3f}  ← degeneracy flag")
            else:
                print("  No high-correlation pairs found.")

            if cov_a.bb_correlations:
                print(f"\n  BB ↔ continuum correlations:")
                for (b, c), rho in cov_a.bb_correlations.items():
                    warn = "  ← strong" if abs(rho) >= HIGH_CORR_THRESHOLD else ""
                    print(f"    {b}  ↔  {c}:  ρ = {rho:+.3f}{warn}")

        # -- overall verdict ---------------------------------------------------
        print(f"\n{sep2}")
        print(f"  VERDICT:  {self._overall_verdict()}")
        print(f"{sep2}\n")
