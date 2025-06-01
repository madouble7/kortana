"""
Project Kor'tana Setup Configuration
Sacred Circuit Development Platform
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README.md for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements.txt
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text(encoding="utf-8").strip().split("\n")
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith("#")]

setup(
    name="kortana",
    version="1.0.0",
    description="Project Kor'tana - Autonomous AI Agent Development Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Project Kor'tana Development Team",
    author_email="team@kortana.dev",
    url="https://github.com/kortana/kortana",

    # Package configuration
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",

    # Dependencies
    install_requires=requirements,

    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "ruff>=0.1.0",
            "mypy>=1.5.0",
            "black>=23.0.0",
        ],
        "monitoring": [
            "prometheus-client>=0.17.0",
            "grafana-api>=1.0.0",
        ],
        "visualization": [
            "gradio>=4.0.0",
            "streamlit>=1.28.0",
        ],
    },

    # Console scripts / CLI entry points
    entry_points={
        "console_scripts": [
            # Main application entry points
            "kortana=kortana.cli.main:main",
            "kortana-server=kortana.cli.server:main",
            "kortana-dev=kortana.cli.dev:main",

            # Agent management
            "kortana-agents=kortana.cli.agents:main",
            "kortana-agent-start=kortana.cli.agents:start_agent",
            "kortana-agent-stop=kortana.cli.agents:stop_agent",
            "kortana-agent-status=kortana.cli.agents:status",

            # Memory management
            "kortana-memory=kortana.cli.memory:main",
            "kortana-memory-clean=kortana.cli.memory:clean",
            "kortana-memory-backup=kortana.cli.memory:backup",
            "kortana-memory-restore=kortana.cli.memory:restore",

            # Development tools
            "kortana-test=kortana.cli.test:main",
            "kortana-lint=kortana.cli.lint:main",
            "kortana-format=kortana.cli.format:main",
            "kortana-check=kortana.cli.check:main",

            # Monitoring and debugging
            "kortana-monitor=kortana.cli.monitor:main",
            "kortana-debug=kortana.cli.debug:main",
            "kortana-logs=kortana.cli.logs:main",

            # Configuration management
            "kortana-config=kortana.cli.config:main",
            "kortana-config-validate=kortana.cli.config:validate",
            "kortana-config-init=kortana.cli.config:init",

            # Legacy entry points (backwards compatibility)
            "start-autonomy=kortana.cli.legacy:start_autonomy",
            "main-kortana=kortana.cli.legacy:main_app",
        ]
    },

    # Package data
    package_data={
        "kortana": [
            "config/*.yaml",
            "config/*.yml",
            "templates/*.txt",
            "templates/*.yaml",
        ]
    },

    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Code Generators",
    ],

    # Keywords
    keywords="ai, agents, autonomous, development, automation, sacred-circuit",

    # Project URLs
    project_urls={
        "Documentation": "https://docs.kortana.dev",
        "Source": "https://github.com/kortana/kortana",
        "Tracker": "https://github.com/kortana/kortana/issues",
    },
)
