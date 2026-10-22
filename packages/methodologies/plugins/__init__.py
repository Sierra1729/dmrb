"""Methodology plugins package."""
from methodologies.plugins.ag04_001.plugin import BMAG04001Plugin
from methodologies.plugins.ag04_002.plugin import BMAG04002Plugin
from methodologies.plugins.fr05_001.plugin import BMFR05001Methodology
from methodologies.plugins.fr05_002.plugin import BMFR05002Methodology
from methodologies.plugins.wa03_002.plugin import BMWA03002Methodology

# Aliases for consistent naming
BMAG04001Methodology = BMAG04001Plugin
BMAG04002Methodology = BMAG04002Plugin
BMFR05001Plugin = BMFR05001Methodology
BMFR05002Plugin = BMFR05002Methodology
BMWA03002Plugin = BMWA03002Methodology

__all__ = [
    "BMFR05001Methodology",
    "BMFR05002Methodology",
    "BMWA03002Methodology",
    "BMAG04001Methodology",
    "BMAG04002Methodology",
    "BMFR05001Plugin",
    "BMFR05002Plugin",
    "BMWA03002Plugin",
    "BMAG04001Plugin",
    "BMAG04002Plugin",
]
