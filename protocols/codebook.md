# Charting codebook

Code every field from the study text supplied (full text when given, otherwise title and abstract). Code only what the study reports. Use "NR" (not reported) when the study is silent on a field that applies to it, and "NA" (not applicable) when the field cannot apply (for example, deployment tier for a purely offline simulation study with no software system). Multi-valued fields take a list. Quote no more than 25 words in any evidence field.

## A. Study

- `study_type` (one): `field_experiment_with_model` (measurements on a real installation plus a model or data-driven method), `simulation_modeling` (model or simulation without new field measurements), `data_driven_model` (ML or statistical model trained or fitted on existing data), `system_development` (sensing, IoT, monitoring, control, or digital twin system built and tested), `mixed`.
- `av_configuration` (list): `elevated`, `interspace_ground_mounted`, `vertical_bifacial`, `tracking_or_dynamic` (single-axis, dual-axis, or dynamic panels), `pv_greenhouse`, `grazing`, `semi_transparent_or_spectral` (semi-transparent, spectrally selective, or wavelength-selective modules), `generic_or_unspecified`.
- `crop_or_livestock` (free text, short; "NR" if not stated).

## B. Context (RQ1)

- `country` (list of study-site countries; "none" if the study is not site-specific, for example a generic simulation).
- `koppen_main` (list, from the site location or as stated): `A` tropical, `B` arid or semi-arid (BWh, BWk, BSh, BSk), `C` temperate, `D` continental, `E` polar, `NR`. Assign from the named site using standard Köppen-Geiger knowledge; if unsure, use `NR`.
- `arid_focus` (one): `explicit` (the site is in a Köppen B climate or the study explicitly targets arid, semi-arid, desert, or dryland conditions), `motivation_only` (aridity, water scarcity, or desert conditions are mentioned as motivation but the site or analysis is not arid), `none`.
- `mena` (yes/no): at least one study site in the Middle East and North Africa as defined by the World Bank: Algeria, Bahrain, Djibouti, Egypt, Iran, Iraq, Israel, Jordan, Kuwait, Lebanon, Libya, Malta, Morocco, Oman, Palestine (West Bank and Gaza), Qatar, Saudi Arabia, Syria, Tunisia, United Arab Emirates, Yemen. Turkey is not included.
- `arid_constraints` (list): `water_scarcity_irrigation`, `heat_or_high_temperature`, `dust_soiling`, `high_irradiance`, `salinity`, `none`.

## C. Digital twin framing (cross-cutting)

- `dt_term_used` (yes/no): the authors describe their work as a digital twin (or digital shadow).
- `dt_maturity` (one, following Kritzinger et al. 2018): `digital_model` (virtual model with no automated data link to the physical system), `digital_shadow` (automated one-way data flow from the physical installation to the model), `digital_twin` (automated two-way flow: the model also feeds decisions or commands back to the installation), `NA` (no virtual representation of a system, for example a pure sensing system).
- `dt_functions` (list): `monitoring_state_estimation` (reconstructs or estimates current states, including unmeasured variables, from sensors or models), `prediction` (forecasts or predicts future or unobserved outcomes such as energy, yield, light, microclimate, water use), `optimization_control` (optimizes design or operation, or controls actuators such as trackers or irrigation).
- `decision_stage` (list): `design` (layout, height, density, spacing, module choice), `operation` (tracking, irrigation, scheduling, fault detection, during operation).

## D. Modeled subsystems

- `subsystems` (list): `light_shading` (irradiance, PAR, shading distribution under or between panels), `pv_energy` (PV yield, electrical output, module temperature), `crop` (growth, yield, physiology, quality), `microclimate` (air temperature, humidity, wind, soil temperature under the array), `water` (soil moisture, irrigation, evapotranspiration, water use), `soiling` (dust or soiling on modules), `economics` (only when combined with a physical model).

## E. Methods (RQ2)

- `method_families` (list): `physics_based` (ray tracing, view-factor, radiative transfer, crop simulation models such as STICS, APSIM, DSSAT, AquaCrop, CFD, thermal or electrical PV models), `statistical` (regression, ANOVA-based models, time-series statistics), `classical_ml` (random forest, SVM, gradient boosting, k-NN, decision trees, Gaussian processes), `deep_learning` (ANN/MLP, CNN, LSTM/GRU, transformers), `reinforcement_learning`, `metaheuristic_optimization` (GA, PSO, NSGA-II, other evolutionary or swarm methods), `mathematical_programming` (LP, MILP, NLP, dynamic programming), `model_predictive_control`, `hybrid_physics_ml` (ML combined with a physics-based model, including surrogates trained on simulations and physics-informed networks), `rule_based_control`, `none`.
- `ai_used` (yes/no): any of `classical_ml`, `deep_learning`, `reinforcement_learning`, or `hybrid_physics_ml`.
- `ai_methods_detail` (free text, short: named algorithms).
- `ai_role` (list, only if ai_used): `surrogate_of_simulation`, `forecasting`, `estimation_or_soft_sensing`, `classification_or_detection`, `control_or_decision`, `design_optimization`.

## F. Data and sensing (RQ3)

- `data_types` (list): `meteorological_irradiance` (weather station, irradiance, typical meteorological year), `pv_electrical`, `crop_plant_measurements`, `soil`, `microclimate_under_array`, `remote_sensing` (satellite or UAV imagery), `simulated_synthetic`, `public_dataset_or_database` (named public dataset, reanalysis, PVGIS, NASA POWER, Meteonorm), `NR`.
- `sensing_modalities` (list): `in_situ_environmental_sensors` (pyranometer, PAR, temperature, humidity, wind), `soil_sensors`, `pv_monitoring` (inverter, power meter, IV), `plant_sensors_or_manual_crop_sampling`, `imaging_rgb_multispectral_thermal`, `satellite`, `uav`, `iot_wireless_network`, `none`, `NR`.
- `temporal_resolution` (one, of the finest data used): `sub_minute`, `minute_to_hourly`, `daily`, `coarser`, `NR`, `NA`.
- `data_duration` (one): `less_than_one_season`, `one_season_or_year`, `multi_season_or_multi_year`, `NR`, `NA`.
- `data_or_code_available` (one): `yes_public` (the study shares data or code), `no_or_NR`.

## G. Computing and deployment (RQ4)

- `deployment` (list): `offline_desktop_or_server` (analysis run offline), `cloud`, `edge_or_embedded` (microcontroller, PLC, field device running logic), `fog_or_gateway`, `multi_tier`, `NR`, `NA`.
- `real_time` (one): `real_time_operation_demonstrated` (the system runs on live data or controls the installation), `designed_for_real_time` (claimed or designed but not demonstrated), `offline`, `NR`.
- `decision_timescale` (list): `seconds_or_faster` (MPPT, power electronics), `minutes_to_hours` (tracking, short-term forecasting, fault detection), `days_to_weeks` (irrigation, crop management), `season_or_longer` (design, layout, yield planning).

## H. Validation

- `validation_setting` (one): `none` (no comparison with measurements), `simulation_benchmark_only` (compared with another model), `field_measurements_single_site`, `field_measurements_multi_site`, `laboratory_or_prototype`.
- `validation_metrics` (free text, short: for example RMSE, R2, MAPE).

## I. Limitations and future work (as stated by the study authors)

- `limitations_stated` (list, short phrases, only what the authors state).
- `future_work_stated` (list, short phrases).

## J. Provenance

- `text_basis` (one): `full_text`, `abstract_only`.
- `notes` (free text, short).
