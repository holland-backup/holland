"""
Define command plugins
"""

import warnings

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="pkg_resources is deprecated as an API.*",
)

__import__("pkg_resources").declare_namespace(__name__)
