"""Created on Jan 07 15:37:00 2026"""

from dataclasses import dataclass

import numpy as np
from astropy.cosmology import FlatLambdaCDM
from numpy.random import multivariate_normal

from .grb_model import Model
from .grb_sed import SpectralModels
from .grb_time import TimeInterval


@dataclass
class IsotropicEnergy:
    model: Model
    model_interval: TimeInterval
    n_iter: int

    e_low: int = 1
    e_high: int = 7

    redshift: float = 0.0

    h0: float = 67.4
    omega_m: float = 0.315

    def __post_init__(self):
        self.mvd = self.__create_mvd()

    def __create_mvd(self):
        multivariate_dict = {}
        param_names = [param.name for param in self.model.parameters]
        param_values = [param.value for param in self.model.parameters]
        param_covar_ = self.model.covariance_matrix_value
        param_covar_ = 0.5 * (param_covar_ + param_covar_.T)
        mn_distribution = multivariate_normal(param_values, param_covar_, self.n_iter)

        for i, v in enumerate(param_names):
            multivariate_dict[v] = mn_distribution[:, i]

        return multivariate_dict

    def luminosity_distance(self):
        """Calculate luminosity distance in cm."""
        return FlatLambdaCDM(H0=self.h0, Om0=self.omega_m).luminosity_distance(self.redshift).cgs.value

    def calculate(self):
        """Calculate the isotropic energy in ergs."""
        fluence = self.spectral_model(m_type='bolometric')

        # E_iso = (4 * pi * dl^2 * fluence) / (1 + z)
        dl = self.luminosity_distance()
        print(dl)
        e_iso = (4 * np.pi * dl**2 * fluence) / (1 + self.redshift)

        return e_iso

    def spectral_model(self, m_type='integrate'):
        p_name = [i.name for i in self.model.parameters]
        p_values = [i.value for i in self.model.parameters]

        sp_model = SpectralModels.legacy_build(
            m_name=self.model.name,
            interval_instance=self.model_interval,
            p_name=p_name,
            p_vals=p_values,
            cov_=self.model.covariance_matrix_value,
            model_type=m_type,
            redshift=self.redshift,
            h0=self.h0,
            omega_m=self.omega_m,
            e_range=(self.e_low, self.e_high)
        )

        return sp_model.get_values()
