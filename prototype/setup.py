from setuptools import setup, find_packages

setup(
    name="kelime_oyunu",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pyodbc",
    ],
    author="Kelime Oyunu Developer",
    author_email="example@example.com",
    description="A word guessing game with tkinter GUI",
    keywords="game, word, turkish",
    python_requires=">=3.6",
) 