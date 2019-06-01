import re
import shutil

from os import path, walk, remove
from codecs import open

from setuptools import setup, find_packages
from distutils.command.clean import clean

pwd = path.abspath(path.dirname(__file__))
__version__ = re.search(
    r"__version__\s*=\s*'(.*)'", open('yasm/__init__.py').read(), re.M
).group(1)
assert __version__

# Get the long description from the README file
with open(path.join(pwd, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


class MyClean(clean):

    def run(self):
        # Delete generated files in the code tree.
        for (dirpath, dirnames, filenames) in walk("."):
            for filename in filenames:
                filepath = path.join(dirpath, filename)
                if filepath.endswith(".pyc") or filepath.endswith('.pyo'):
                    remove(filepath)
            for dirname in dirnames:
                if dirname in ('build', 'dist', 'yasm.egg-info'):
                    shutil.rmtree(path.join(dirpath, dirname))
        clean.run(self)


setup(
    name='yasm',
    description='Python State Machines for Humans',
    long_description=long_description,
    author='Catstyle',
    author_email='catstyle.lee@gmail.com',

    url='http://github.com/Catstyle/yasm',
    version=__version__,
    license='MIT',

    packages=find_packages(),
    keywords='state_machine',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here.
        # In particular, ensure that you indicate whether you support
        # Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    cmdclass={'clean': MyClean}
)
