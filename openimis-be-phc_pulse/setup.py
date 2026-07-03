import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='openimis-be-phc_pulse',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    license='GNU AGPL v3',
    description='PHC Pulse: capitation and output-based-aid (OBA) payment module for openIMIS (Track 2 hackathon submission).',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://openimis.org/',
    author='Team PHC Pulse',
    author_email='',
    install_requires=[
        'django',
        'django-db-signals',
        'djangorestframework',
        'graphene-django<3',
        'openimis-be-core',
        'openimis-be-location',
        'openimis-be-product',
        'openimis-be-insuree',
        'openimis-be-api_fhir_r4',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.10',
    ],
)
