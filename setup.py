from setuptools import find_packages, setup

setup(
    name = "simulacovid",
    packages = find_packages(),
    install_requires=[
        "pandas", "numpy", "scipy", "scikit-learn", "plotly"
    ]
)