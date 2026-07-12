"""Quant Research Tools (qrt).

Usage:
    import qrt as q
"""

from qrt import bt, data, dataload, feat, models, portfolio, splits, tearsheet, utils, vendors
from qrt.utils import set_seed

from typing import Dict, List, Tuple, Union                     # Type hints for function signatures

# Machine learning framework
import torch                                # PyTorch for neural networks
import torch.nn as nn                       # Neural network modules
import torch.optim as optim                 # Optimization algorithms

# Numerical computing and datetime
import numpy as np                          # Numerical operations
import numpy.typing as npt
from datetime import datetime, timedelta    # Date and time handling

# Visualization
#import altair                               # Interactive plotting library
import matplotlib.pyplot as plt

import random
import re
import itertools
from pathlib import Path
from tqdm import tqdm
import os


__version__ = "0.0.1"

__all__ = [
    "bt",
    "data",
    "dataload",
    "feat",
    "models",
    "portfolio",
    "splits",
    "tearsheet",
    "utils",
    "vendors",
    "set_seed",
]