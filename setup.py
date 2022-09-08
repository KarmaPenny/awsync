import io
import os
from setuptools import setup, find_packages

def read(file_name):
  with io.open(os.path.join(os.path.dirname(__file__), file_name), encoding="utf-8") as f:
    return f.read()

setup(
  name="awsync",
  version="1.0",
  license="BSD-2-Clause",
  description="library for basic async calls in aws",
  long_description=read("README.md"),
  long_description_context_type="text/markdown",
  author="Cole Robinette",
  author_email="please.dont@gmail.com",
  url="https://github.com/KarmaPenny/awsync",
  packages=find_packages("src"),
  package_dir={"": "src"},
  include_package_data=True,
  zip_safe=True,
  #python_requires=">=3.9",
  install_requires=[
    "boto3",
    "pydantic",
  ],
)
