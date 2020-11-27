from pathlib import Path

from setuptools import find_packages, setup

with Path("README.md").open(encoding="utf-8") as readme:
    long_description = readme.read()

setup(
    name="pytest-pyppeteer",
    version="0.2.3",
    author="Yao Meng",
    author_email="yaomeng614@gmail.com",
    maintainer="Yao Meng",
    maintainer_email="yaomeng614@gmail.com",
    description="A plugin to run pyppeteer in pytest.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    keywords="pytest-plugin pyppeteer pytest",
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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={"pytest11": ["pytest_pyppeteer = pytest_pyppeteer.plugin"]},
    python_requires=">=3.7",
    install_requires=[
        "pyppeteer==0.2.2",
        "pytest-asyncio>=0.14.0",
        "pytest>=6.0.2",
        "pydantic>=1.6.1",
        "cssselect>=1.1.0",
        "lxml>=4.5.2",
    ],
)
