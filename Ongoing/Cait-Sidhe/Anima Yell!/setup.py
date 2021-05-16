import setuptools

name = "AY_NCs"
version = "0.0.2"
release = "0.0.2"

setuptools.setup(
    name=name,
    version=release,
    author="RivenSkaye",
    author_email="imake@yomomma.com",
    description="Anima Yell! NCs",
    packages=["AY_NCs"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
