from setuptools import setup
from setuptools import find_packages

setup(
    name='moosetools',
    version='0.0.0',
    description='A repository containing tools originally designed to support MOOSE (www.mooseframework.org).',
    url='https://github.com/idaholab/moosetools',
    author='Idaho National Lab',
    author_email='blank@blank.com',
    license='GNU GPL',
    packages=find_packages(),
    install_requires=['coverage',
                      'deepdiff',
                      'pandas',
                      'pyyaml',
                      'sympy',
                      'matplotlib',
                      'packaging',
                      'colored',
                      'yapf==0.31.0'
                      ],

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Utilities',
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    ],
)