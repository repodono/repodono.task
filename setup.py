from setuptools import setup, find_packages

version = '0.0'

classifiers = """
Development Status :: 3 - Alpha
License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)
Operating System :: OS Independent
Programming Language :: JavaScript
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
""".strip().splitlines()

long_description = (
    open('README.rst').read()
    + '\n' +
    open('CHANGES.rst').read()
    + '\n')

setup(
    name='repodono.task',
    version=version,
    description="A collection of common tasks for the repodono framework",
    long_description=long_description,
    classifiers=classifiers,
    keywords='',
    author='Tommy Yu',
    author_email='',
    url='https://github.com/repodono/repodono.task',
    license='gpl',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['repodono'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        # -*- Extra requirements: -*-
    ],
    extras_require={
        'requests': [
            'requests',
        ],
    },
    python_requires='>=3.4',
    entry_points={
    },
    test_suite="repodono.task.tests.make_suite",
)
