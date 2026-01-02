"""Created on Dec 31 16:27:26 2025"""

from dataclasses import dataclass, field
from typing import Callable, Tuple

import numpy as np
from uncertainties import ufloat

from src.grb_research import model_n_pars
from src.grb_research.grb_model import Model
from src.grb_research.grb_time import TimeInterval
from src.grb_research.seds import band_function, black_body, cutoff_powerlaw, powerlaw, smoothly_broken_power_law


class GRBExceptions(Exception):
    """Base exception class for GRB-related errors."""


class ModelNotFoundInDataError(GRBExceptions):
    """Custom exception for handling missing models in SpectralModels."""

    def __init__(self):
        super().__init__(f"Model not found in the data.")


@dataclass
class SpectralModels:
    """Class to handle spectral models for GRB analysis."""

    _SINGLE_COMPONENTS = {
        'pl': ('_powerlaw', model_n_pars['pl']),
        'bb': ('_black_body', model_n_pars['bb']),
        'cpl': ('_cutoff_powerlaw', model_n_pars['cpl']),
        'band': ('_band_grb_function', model_n_pars['band']),
        'sbpl': ('_smoothly_broken_power_law', model_n_pars['sbpl']),
    }

    _MODEL_MAP = {
        "pl_bb": ("pl", "bb"),
        "cpl_pl": ("pl", "cpl"),
        "cpl_bb": ("cpl", "bb"),
        "cpl_pl_bb": ("pl", "cpl", "bb"),
        "band_pl": ("pl", "band"),
        "band_bb": ("band", "bb"),
        "band_pl_bb": ("pl", "band", "bb"),
        "sbpl_pl": ("pl", "sbpl"),
        "sbpl_bb": ("sbpl", "bb"),
        "sbpl_pl_bb": ("pl", "sbpl", "bb"),
    }

    energy: np.ndarray
    model: Model
    interval: TimeInterval
    model_type: str = 'counts'

    flux_energy: Tuple[float, float] = field(default_factory=lambda: (10, 1e7))
    isotropic_energy: Tuple[float, float] = field(default_factory=lambda: (1, 1e4))
    redshift: float = 0.0
    h0: float = 67.4
    omega_m: float = 0.315

    keVtoErg: float = 1.6021766208e-09

    def __post_init__(self):
        self.t_start = self.interval.start
        self.t_stop = self.interval.end

    def _evaluate_components(self, components, with_errors=False):
        values = [p.value for p in self.model.parameters]
        spectra = []

        idx = 0
        for name in components:
            func_name, n_pars = self._SINGLE_COMPONENTS[name]
            pars = values[idx: idx + n_pars]
            if with_errors:
                errors = np.sqrt(np.diag(self.model.covariance_matrix_value[idx: idx + n_pars, idx: idx + n_pars]))
            idx += n_pars

            func = getattr(self, func_name)
            pars = [ufloat(v, e) for v, e in zip(pars, errors)]
            spectra.append(func(pars, with_errors=with_errors))

        total = np.sum(spectra, axis=0)

        if with_errors:
            return spectra, total, errors
        else:
            return spectra, total

    @property
    def _model_params(self):
        """Cache model parameters - only changes when model changes."""
        return self.model.get_parameter_values()

    @property
    def _time_diff(self):
        """Cache time difference."""
        return self.t_stop - self.t_start

    @property
    def _bol_range(self):
        """Precompute bolometric range."""
        return (self.isotropic_energy[0] / (1 + self.redshift),
                self.isotropic_energy[1] / (1 + self.redshift))

    def _compute_model(self, spectral_func: Callable, joint_pars=None, with_errors=False):
        energy = self.energy
        pars = joint_pars if joint_pars is not None else self._model_params

        spectrum = spectral_func(energy, *pars)

        # Dispatch based on model_type
        if self.model_type == 'counts':
            return spectrum

        elif self.model_type == 'energy':
            return energy * spectrum

        elif self.model_type in ['nuFnu', 'nfn']:
            return energy**2 * spectrum

        elif self.model_type in ['integrate', 'bolometric']:
            range_ = self.flux_energy if self.model_type == 'integrate' else self._bol_range
            mask = np.logical_and(energy >= range_[0], energy <= range_[1])
            if not np.any(mask):
                return 0.0
            norm = 1.0 if self.model_type == 'integrate' else self._time_diff
            return np.trapz(y=energy[mask] * spectrum[mask],
                            x=energy[mask]) * self.keVtoErg * norm

        raise ValueError(f"Unknown model_type: {self.model_type}")

    def _powerlaw(self, joint_pars=None, with_errors=False):
        return self._compute_model(spectral_func=powerlaw, joint_pars=joint_pars, with_errors=with_errors)

    def _black_body(self, joint_pars=None, with_errors=False):
        return self._compute_model(spectral_func=black_body, joint_pars=joint_pars, with_errors=with_errors)

    def _cutoff_powerlaw(self, joint_pars=None, with_errors=False):
        return self._compute_model(spectral_func=cutoff_powerlaw, joint_pars=joint_pars, with_errors=with_errors)

    def _smoothly_broken_power_law(self, joint_pars=None, with_errors=False):
        return self._compute_model(spectral_func=smoothly_broken_power_law, joint_pars=joint_pars, with_errors=with_errors)

    def _band_grb_function(self, joint_pars=None, with_errors=False):
        return self._compute_model(spectral_func=band_function, joint_pars=joint_pars, with_errors=with_errors)

    def evaluate_model(self, model_key, with_errors=False):
        """Evaluate a composite model based on the model key."""
        return self._evaluate_components(components=self._MODEL_MAP[model_key], with_errors=with_errors)

    def get_values(self, with_errors=False):
        """Get the spectral model values based on the model type."""
        if self.model is None:
            raise ModelNotFoundInDataError()

        m_name = self.model.name.lower()

        singular_models = ['pl', 'cpl', 'band', 'sbpl']
        model_functions = {'pl': self._powerlaw,
                           'cpl': self._cutoff_powerlaw,
                           'band': self._band_grb_function,
                           'sbpl': self._smoothly_broken_power_law}

        if m_name in singular_models:
            return model_functions[m_name](with_errors=with_errors)
        else:

            return self.evaluate_model(model_key=m_name, with_errors=with_errors)
