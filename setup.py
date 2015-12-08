from setuptools import setup

setup(
    name="ggp",
    version="0.1.0",
    description="General Game Playing",
    url="https://github.com/EdTsft/ggp",
    author="Eric Langlois",
    author_email="eric@langlois.xyz",
    license="MIT",
    packages=["ggp"],
    install_requires=[
        "pyparsing",
        "pyswip>=0.2.5",
        "swilite",
    ],
)
