from setuptools import setup, find_packages

setup(
    name="pyloan",
    version="0.9.0",
    description="Computes repayment plan for loans with constant monthly payment and variable rate.",
    author="vinymeuh",
    author_email="vinymeuh@gmail.com",
    url="https://github.com/vinymeuh/pyloan",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(),
    install_requires=["Click", "python-dateutil", "ruamel.yaml"],
    entry_points="""
        [console_scripts]
        pyloan=pyloan.main:main
        pyloanng=pyloan.app:cli
    """,
)
