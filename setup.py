from setuptools import setup

setup(name='git-spindle',
    version="3.4.3",
    description='Git subcommands for integrating with central services like github, gitlab and bitbucket',
    author='Dennis Kaarsemaker',
    author_email='dennis@kaarsemaker.net',
    url='http://github.com/seveas/git-spindle',
    packages=['gitspindle'],
    package_dir={'': 'lib'},
    entry_points={
        'console_scripts':[
            'git-hub=gitspindle:hub',
            'git-lab=gitspindle:lab',
            'git-bucket=gitspindle:bucket',
            'git-bb=gitspindle:bb',
        ]
    },
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Topic :: Software Development",
        "Topic :: Software Development :: Version Control"
    ],
    install_requires=["github3.py>=0.9.0,<1.0","whelk>=2.6", "docopt>=0.5.0", "six"],
)
