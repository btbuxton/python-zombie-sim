try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Zombie Simulation',
    'author': 'Blaine Buxton',
    'url': 'http://blabux.net',
    'download_url': 'git://',
    'author_email': 'btbuxton@gmail.com',
    'version': '0.1',
    'install_requires': ['nose' , 'pygame'],
    'packages': ['zombiesim'],
    'scripts': [],
    'name': 'zombie-sim'
}

setup(**config)
