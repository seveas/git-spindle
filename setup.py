from distutils.core import setup

setup(name='hub',
    version="1.11",
    description='Github integration for git',
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
    install_requires=["github3.py>=0.5", "whelk>=1.2", "docopt>=0.5.0"],
)
