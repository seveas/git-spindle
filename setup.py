from setuptools import setup
import codecs

with codecs.open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(name='hub',
    version="1.20",
    description='Github integration for git',
    long_description=long_description,
    author='Dennis Kaarsemaker',
    author_email='dennis@kaarsemaker.net',
    url='http://github.com/seveas/git-hub',
    scripts=['git-hub'],
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Topic :: Software Development",
        "Topic :: Software Development :: Version Control"
    ],
    install_requires=["github3.py>=0.8.2", "whelk>=1.11", "docopt>=0.5.0"],
)
