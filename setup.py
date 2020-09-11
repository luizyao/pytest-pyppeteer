from pathlib import Path

from pkg_resources import parse_requirements
from setuptools import setup, find_packages

with Path("requirements.txt").open(mode="r") as requirements_txt:
    install_requires = [
        str(requirement) for requirement in parse_requirements(requirements_txt)
    ]

with Path("README.md").open(mode="r", encoding="utf-8") as readme_md:
    long_description = readme_md.read()

setup(
    name="pytest-pyppeteer",
    version="0.1.3",
    author="Luiz Yao",
    author_email="yaomeng614@gmail.com",
    description="Plugin for running pyppeteer in pytest.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    keywords="pytest-plugin pyppeteer puppeteer",
    url="https://github.com/luizyao/pytest-pyppeteer",
    packages=find_packages("src"),
    package_dir={"": "src"},
    classifiers=[
        "Framework :: Pytest",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    entry_points={"pytest11": ["pytest_pyppeteer = pytest_pyppeteer.plugin"]},
    python_requires=">=3.6",
    install_requires=install_requires,
)
