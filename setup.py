from setuptools import setup, find_packages

setup(
    name="smartcase",
    version="0.2.0",
    author="Nivetha G",
    author_email="nivethaga@gmail.com",
    description="A smart text cleaner that preserves important capitalization using NER",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Nivetha9april/smartcase.git",
    packages=find_packages(),
    install_requires=["spacy"],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "smartcase=smartcase.cli:main",
        ],
    },
)
