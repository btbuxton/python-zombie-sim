from setuptools import setup, find_packages

config = {
    'python_requires': '>=3.9',
    'description': 'Zombie Simulation',
    'author': 'Blaine Buxton',
    'url': 'http://blabux.net',
    'download_url': 'git://',
    'author_email': 'btbuxton@gmail.com',
    'version': '0.1',
    'install_requires': ['pygame'],
    'packages': find_packages(),
    'scripts': [],
    'name': 'zombie-sim'
}

setup(**config)
