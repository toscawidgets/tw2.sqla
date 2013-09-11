import sys
from setuptools import setup, find_packages

# Required imports to avoid weird error messages in python2.7
try:
    import multiprocessing, logging
except Exception:
    pass

# Requirements to install buffet plugins and engines
_extra_cheetah = ["Cheetah>=1.0", "TurboCheetah>=0.9.5"]
_extra_genshi = ["Genshi >= 0.3.5"]
_extra_kid = ["kid>=0.9.5", "TurboKid>=0.9.9"]
_extra_mako = ["Mako >= 0.1.1"]

requires = [
    "tw2.forms>=2.0b4",
    "tw2.dynforms",
    "sqlalchemy >= 0.7",
    "zope.sqlalchemy >= 0.4",
]

setup(
    name='tw2.sqla',
    version='2.0.6',
    description='SQLAlchemy database layer for ToscaWidgets 2, a web widget toolkit.',
    long_description=open('README.rst').read().split('.. split here', 1)[1],
    author='Paul Johnston',
    author_email='paj@pajhome.org.uk',
    url='http://github.com/toscawidgets/tw2.sqla',
    download_url="https://pypi.python.org/pypi/tw2.sqla/",
    license='MIT',
    install_requires=requires,
    packages=find_packages(exclude=['ez_setup', 'tests']),
    namespace_packages = ['tw2'],
    zip_safe=False,
    include_package_data=True,
    test_suite = 'nose.collector',
    tests_require = [
        'BeautifulSoup',
        'strainer',
        'nose',
        'FormEncode',
        'WebTest',
        'tw2.core>=2.0.1',
        'tw2.forms',
        'elixir',
        'sieve>=0.1.9',
    ] + _extra_cheetah + _extra_genshi + _extra_kid + _extra_mako,
    extras_require = {
        'cheetah': _extra_cheetah,
        'kid': _extra_kid,
        'genshi': _extra_genshi,
        'mako': _extra_mako,
    },
    entry_points="""
        [tw2.widgets]
        # Register your widgets so they can be listed in the WidgetBrowser
        widgets = tw2.sqla
    """,
    keywords = [
        'toscawidgets.widgets',
    ],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Environment :: Web Environment :: ToscaWidgets',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Widget Sets',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
)
