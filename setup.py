"""ScrapeMeAgain Package Handler"""


from os import path
from setuptools import setup, find_packages


def read(fname, readlines=False):
    with open(path.join(path.abspath(path.dirname(__file__)), fname)) as f:
        return f.readlines() if readlines else f.read()


requirements = read("requirements.txt", True)


setup(
    version="1.0.4",
    name="scrapemeagain",
    url="https://github.com/DusanMadar/ScrapeMeAgain",
    author="Dusan Madar",
    author_email="madar.dusan@gmail.com",
    description="Yet another Python web scraping application",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    keywords="web scraper",
    packages=find_packages(),
    scripts=["scripts/scrapemeagain-compose.py"],
    include_package_data=True,
    test_suite="tests",
    license="MIT",
    platforms="linux",
    python_requires=">=3.6",
    install_requires=requirements,
    tests_require=requirements,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
