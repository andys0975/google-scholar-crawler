import os
import setuptools

setuptools.setup(
    name = 'scholarpy',
    version = '0.1.0',
    author = 'Shih-Chun Cheng',
    author_email = 'andys0975@gmail.com',

    description = 'Simple crawler for Google Scholar',
    long_description='',
    long_description_content_type="text/markdown",
    license='Unlicense',

    url = 'https://github.com/andys0975/google-scholar-crawler',
    download_url = 'https://github.com/andys0975/google-scholar-crawler/tarball/master',
    packages=setuptools.find_packages(),
    py_modules=['Crawler', 'ParseOut'],
    keywords = ['Google Scholar Crawler'],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    install_requires=['beautifulsoup4', 'requests', 'pandas']
)