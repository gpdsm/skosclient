from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="skosclient",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python client for extracting and processing SKOS thesauri",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/skosclient",
    packages=find_packages(),
    package_data={
        'skosclient': ['websiteresources/*.html', 'websiteresources/*.json'],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: XML",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "skosclient=skosclient.cli:main",
        ],
    },
    keywords="skos, thesaurus, rdf, turtle, knowledge organization",
)