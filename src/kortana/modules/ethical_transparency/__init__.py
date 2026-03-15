"""
Ethical Transparency Module for Kor'tana
Provides logging and dashboard for ethical decision-making
"""

from .decision_logger import EthicalDecisionLogger
from .transparency_service import TransparencyService

__all__ = ["EthicalDecisionLogger", "TransparencyService"]
