"""Setup script for de-af package."""
from setuptools import setup, find_packages

setup(
    name="de-af",
    version="0.1.0",
    description="Autonomous Data Engineering agent node for AgentField",
    packages=find_packages(),
    python_requires=">=3.12",
    install_requires=[
        "agentfield>=0.1.9",
        "pydantic>=2.0",
        "claude-agent-sdk==0.1.20",
    ],
    extras_require={
        "dev": ["pytest", "pytest-asyncio", "ruff"],
    },
    entry_points={
        "console_scripts": [
            "de-af=de_af.app:main",
            "de-fast=de_af.fast.app:main",
        ],
    },
)
