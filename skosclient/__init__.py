"""
SKOSClient - A Python client for extracting and processing SKOS thesauri
"""

__version__ = "0.1.0"
__author__ = "Giacomo Marchioro"

from .extractor import SKOSExtractor, ExtractionResult

__all__ = ["SKOSExtractor", "ExtractionResult"]