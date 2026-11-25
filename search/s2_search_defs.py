import json, sys, time, urllib.request, urllib.parse, datetime
AV = ('agrivoltaic | agrivoltaics | "agri-voltaic" | "agri-voltaics" | "agri-photovoltaic" | "agri-photovoltaics" | '
      'agrophotovoltaic | agrophotovoltaics | "agro-photovoltaic" | "agro-photovoltaics" | agrovoltaic | agrovoltaics | '
      '"agro-voltaic" | "solar sharing" | "photovoltaic agriculture" | "solar agriculture" | "PV farming" | agrisolar | '
      '"solar grazing" | "photovoltaic greenhouse" | "photovoltaic greenhouses" | "PV greenhouse" | "PV greenhouses" | '
      '"dual-use solar" | "dual-use photovoltaic"')
E = ('"digital twin" | "digital twins" | "digital shadow" | "machine learning" | "deep learning" | "artificial intelligence" | '
     '"neural network" | "neural networks" | "reinforcement learning" | "random forest" | "support vector" | "gradient boosting" | '
     'XGBoost | LSTM | convolutional | "physics-informed" | "data-driven" | forecasting | forecast | "surrogate model" | metamodel | '
     '"genetic algorithm" | "particle swarm" | "Bayesian optimization" | "Internet of Things" | IoT | "sensor network" | '
     '"wireless sensor" | "edge computing" | "fog computing" | "cloud computing" | "decision support" | "remote sensing" | '
     'UAV | drone | satellite | "computer vision" | "ray tracing" | "ray-tracing" | "crop model" | "crop modeling" | '
     '"crop modelling" | "crop growth model" | "light model" | "radiation model" | "shading model" | "microclimate model" | '
     '"computational fluid dynamics" | CFD | "monitoring system" | "real-time monitoring" | "smart farming" | '
     '"precision agriculture" | "model predictive control" | "control strategy" | "optimization algorithm" | "optimisation algorithm"')
DT = '"digital twin" | "digital twins"'
PVAG = '(photovoltaic | "solar panel" | "solar panels" | "solar array" | PV) + (crop | crops | agriculture | agricultural | farm | farming | greenhouse)'
ARID = ('arid | "semi-arid" | desert | deserts | dryland | drylands | "hot climate" | MENA | "Middle East" | Gulf | UAE | "United Arab Emirates" | '
        'Saudi | Qatar | Oman | Kuwait | Bahrain | Egypt | Jordan | Morocco | Algeria | Tunisia | Libya | Israel | Iran | Iraq | Sahara | Sahel')
