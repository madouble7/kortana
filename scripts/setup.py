#!/usr/bin/env python
"""
Kor'tana setup script.
"""

from setuptools import find_packages, setup

setup(
    name="kortana",
    version="0.1.0",
    description="The warchief's AI companion",
    author="Matt",
    python_requires=">=3.9,<3.12",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.95.0",
        "uvicorn>=0.21.1",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "omegaconf>=2.3.0",
        "openai>=1.0.0",
        "google-generativeai>=0.0.1",
        "langchain>=0.0.300",
        "langchain-community>=0.0.10",
        "langchain-openai>=0.0.2",
        "pinecone-client>=2.2.2",
        "chromadb>=0.4.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "pyyaml>=6.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.3.1",
            "pytest-cov>=4.1.0",
            "mypy>=1.0.0",
            "ruff>=0.0.280",
        ],
    },
    entry_points={
        "console_scripts": [
            "kortana-api=kortana.cli.api:main",
            "kortana-dashboard=kortana.cli.dashboard:main",
            "kortana-autonomous=kortana.cli.autonomous:main",
        ],
    },
)
