from pathlib import Path

from pkg_resources import parse_requirements
from setuptools import find_packages, setup

with Path("requirements.txt").open(mode="r", encoding="utf-8") as requirements_txt:
    install_requires = [
        str(requirement) for requirement in parse_requirements(requirements_txt)
    ]

with Path("README.md").open(mode="r", encoding="utf-8") as readme:
    long_description = readme.read()

setup(
    name="pytest-pyppeteer",
    version="0.2.0",
    author="Yao Meng",
    author_email="yaomeng614@gmail.com",
    maintainer="Yao Meng",
    maintainer_email="yaomeng614@gmail.com",
    description="A plugin to run pyppeteer in pytest.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    keywords="pytest-plugin pyppeteer puppeteer",
    url="https://github.com/luizyao/pytest-pyppeteer",
    packages=find_packages("src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={"pytest11": ["pytest_pyppeteer = pytest_pyppeteer.plugin"]},
    python_requires=">=3.6",
    install_requires=install_requires,
)
