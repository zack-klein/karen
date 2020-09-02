from setuptools import setup

with open("requirements.txt") as f:
    reqs = f.readlines()


setup(
    name="karen",
    description="ESPN Fantasy Football Analytics.",
    author="Zachary Klein",
    author_email="zack.klein1@gmail.com",
    url="https://zacharyjklein.com",
    packages=["app", "karen"],
    include_package_data=True,
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    install_requires=reqs,
)
