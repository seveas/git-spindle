from distutils.core import setup
 
setup(name='git-hub',
    version="1.0",
    description='Github integration for git',
    author='Dennis Kaarsemaker',
    author_email='dennis@kaarsemaker.net',
    url='http://github.com/seveas/django-sqlviews',
    scripts=['git-hub'],
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Topic :: Software Development",
        "Topic :: Software Development :: Version Control",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    install_requires = ["requests>=0.13.8", "github3.py>=0.1a8"],
)
