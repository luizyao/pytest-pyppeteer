from setuptools import setup, find_packages
from pkg_resources import parse_requirements
from pathlib import Path

with Path("requirements.txt").open(mode="r") as requirements_txt:
    install_requires = [
        str(requirement) for requirement in parse_requirements(requirements_txt)
    ]

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="pytest-pyppeteer",
    version="0.1.0",
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
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3 :: Only",
    ],
    entry_points={"pytest11": ["pytest_pyppeteer = pytest_pyppeteer.plugin"]},
    python_requires=">=3.6",
    install_requires=install_requires,
)
