# Draft Plan for GRB Time-Resolved Analysis

### Scatter Plots

- [ ] Produce scatter plots of key spectral parameters across the time-resolved intervals of each GRB to visualize overall temporal trends. 
- [ ] Generate comparison scatter plots showing how the inclusion of additional spectral components (e.g., a power-law [PL] or blackbody [BB]) affects the base model parameters. In particular, compare $E_\text{peak}$, $\alpha$, and $\beta$ before and after adding the extra PL/BB component.
- [ ] Create scatter plots of energy fluence versus the same parameters to investigate possible correlations between spectral evolution and total emitted energy.
- [ ] Because this work focuses on the additional BB component, examine the relationship between $\text{BB}_\text{AMP}$ and $\text{BB}_\text{kT}$ over the time-resolved intervals to look for systematic trends. Similar checks can be performed for other parameter pairs if warranted by the data.

### Additional Correlation Studies

- [ ] **Hardness–intensity/flux correlations:** Track $E_\text{peak}$ or $\text{kT}$ versus flux to search for classic “hard-to-soft” or “tracking” behaviors.
- [ ] **Isotropic energy vs. BB temperature:** Test theoretical scaling relations predicted by photospheric models.
- [ ] **Redshift dependence:** For GRBs with unknown redshift, explore how inferred physical parameters (e.g., $E_\text{iso}$, photospheric radius) vary across a plausible redshift range.

### Butterfly (Spectral-Model) Plots

- [ ] Produce model spectra with full error propagation (**butterfly plots**) for both **SAFE** and **UNSAFE** fits to illustrate the statistical range of each model.
- [ ] For joint time-integrated (TI) and time-resolved (TR) analyses, overplot butterflies from different model quality categories (e.g., SAFE, GOOD, BEST) on the same figure to enable direct visual comparison.

### Blackbody Component Diagnostics

- [ ] **Photospheric radius & Lorentz factor:** Use BB temperature and flux to estimate the emitting radius and bulk Lorentz factor (e.g., Pe'er 2007 method).
- [ ] **Multi-component decomposition:** Quantify the fractional BB contribution to total energy flux and track its evolution throughout the burst.
- [ ] **Fireball parameter estimation:** From $kT$ and flux, estimate additional fireball parameters such as baryon loading, initial radius, and possible jet magnetization.
- [ ] **Lorentz factor lower limits:** Use opacity arguments (e.g., $\gamma\gamma$ pair production) to constrain the minimum bulk Lorentz factor.

### Model Robustness and Alternatives

- [ ] **Alternative models:** Fit synchrotron, Comptonized, or two-BB models to test whether the BB signature is genuine or an artifact of model choice.
- [ ] Compare fit statistics (likelihood ratio, AIC/BIC) across all tested models to establish the significance of the BB component.

### GRB Characterization

- [ ] Test each burst against well-known empirical relations such as the **Amati** and **Yonetoku** correlations.
- [ ] Derive physical parameters such as isotropic energy ($E_\text{iso}$), peak luminosity, and, where feasible, constraints on jet overflow or jet-break signatures.

### Population Context and Comparative Analysis

- [ ] **Comparative plots:** Place the four BB-dominated GRBs within the context of a larger GRB population (e.g., the Fermi-GBM catalog) to determine whether they occupy distinct regions in $E_\text{peak}$–$E_\text{iso}$ space or in $kT$ distributions.
- [ ] Examine whether BB-dominated bursts differ systematically in duration, fluence, or spectral hardness compared with the general GRB sample.

### Literature Context

- [ ] Survey recent GRB spectral and temporal studies to identify comparable analyses and benchmark results.
- [ ] Highlight key findings from the literature that can guide the physical interpretation of trends observed in the current dataset.

