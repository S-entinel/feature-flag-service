"""
Setup script for Feature Flag SDK
"""

from setuptools import setup, find_packages

with open("SDK_README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="feature-flags-sdk",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Python SDK for Feature Flag Service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/S-entinel/feature-flag-service",
    packages=find_packages(include=["sdk", "sdk.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
        ],
    },
)