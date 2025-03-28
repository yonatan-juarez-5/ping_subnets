from setuptools import setup, find_packages

setup(
    name="ping_subnets",
    version="0.1.0", 
    author="Yonatan Juarez",
    author_email="yjuarez@usc.edu",
    description="A tool to retrieve ip addresses that are pingable on one subnet but not the other.",
    long_description=open("README.md").read(), 
    long_description_content_type="text/markdown",
    packages=find_packages(), 
     install_requires=[
        "tqdm>=4.0.0", 
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",  
)