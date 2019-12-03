
from setuptools import setup

with open('README.rst', 'r') as fh:
    long_description = fh.read()

setup(
    name='simplezfs',
    version='0.0.1',
    author='Andreas Gonschorek, Stefan Valouch',
    description='Simple, low-level ZFS API',
    long_description=long_description,
    packages=['simplezfs'],
    package_data={'simplezfs': ['py.typed']},
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    license='BSD-3-Clause',
    url='https://github.com/svalouch/python-simplezfs',
    platforms='any',
    python_requires='>=3.6',

    install_requires=[
        'pydantic<1',
    ],

    extras_require={
        'tests': [
            'mypy',
            'pytest',
            'pytest-cov',
        ],
        'docs': [
            'Sphinx>=2.0',
        ],
    },

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
