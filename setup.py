"""ScrapeMeAgain Package Handler"""


from setuptools import setup, find_packages


description = "Yet another Python web scraping application"


setup(
    version="1.0.0",
    name="scrapemeagain",
    url="https://github.com/DusanMadar/ScrapeMeAgain",
    author="Dusan Madar",
    author_email="madar.dusan@gmail.com",
    description=description,
    long_description=description,
    keywords="web scraper",
    packages=find_packages(),
    scripts=["scripts/scrapemeagain-compose.py"],
    test_suite="tests",
    license="MIT",
    platforms="linux",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Internet :: WWW/HTTP",
    ],
)
