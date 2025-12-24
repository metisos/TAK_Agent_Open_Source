#!/usr/bin/env python3
"""TAK AI Agent Framework - Setup"""

from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="tak-ai-agent",
    version="1.0.0",
    description="AI agent framework for TAK (Team Awareness Kit) networks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Christian Johnson",
    author_email="cjohnson@metisos.com",
    url="https://github.com/metisos/TAK_Agent_Open_Source",
    project_urls={
        "Documentation": "https://github.com/metisos/TAK_Agent_Open_Source#readme",
        "Source": "https://github.com/metisos/TAK_Agent_Open_Source",
        "Issue Tracker": "https://github.com/metisos/TAK_Agent_Open_Source/issues",
    },
    license="MIT",
    keywords=[
        "tak",
        "atak",
        "wintak",
        "cot",
        "cursor-on-target",
        "situational-awareness",
        "ai-agent",
        "llm",
        "tactical",
        "geospatial",
    ],
    python_requires=">=3.11",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "tak_agent": [
            "templates/system_prompts/*.txt",
        ],
    },
    install_requires=[
        "pytak>=6.2.0",
        "aiohttp>=3.9.0",
        "anthropic>=0.40.0",
        "groq>=0.4.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "geopy>=2.4.0",
        "cryptography>=41.0.0",
        "xmltodict>=0.13.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "tak-agent=tak_agent.run:cli",
            "tak-agent-cli=tak_agent.cli:main_menu",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Framework :: AsyncIO",
    ],
)
