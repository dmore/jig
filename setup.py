import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.rst')).read()


version = '0.1.0'

install_requires = [
    'GitPython>=0.3.2RC1',
    'docutils==0.8.1']


setup(name='jig',
    version=version,
    description="Check your code for stuff before you `git commit`",
    long_description=README + '\n\n' + NEWS,
    classifiers=[
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
    keywords='git hooks code smell lint',
    author='Rob Madole',
    author_email='robmadole@gmail.com',
    url='http://github.com/robmadole/jig',
    license='BSD',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'jig = jig.entrypoints:main'],
        'nose.plugins.0.10': [
            'jig = jig.tests.noseplugin:TestSetup']}
)
