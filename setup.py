from distutils.core import setup
from trombi import version

setup(
    name='trombi',
    version='.'.join(map(str, version)),
    description='CouchDB client for Tornado',
    license='MIT',
    author='Inoi Oy',
    author_email='inoi@inoi.fi',
    maintainer='Jyrki Pulliainen',
    maintainer_email='jyrki.pulliainen@inoi.fi',
    url='http://github.com/inoi/trombi/',
    packages=['trombi'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Database',
        ]
)
