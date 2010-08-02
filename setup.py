from setuptools import setup, find_packages

setup(
    name='tw2.sqla',
    version='2.0a1',
    description='SQLAlchemy database layer for ToscaWidgets 2',
    author='Paul Johnston',
    author_email='paj@pajhome.org.uk',
    url='http://www.toscawidgets.org/documentation/tw2.core/',
    install_requires=[
        "tw2.forms>=2.0b4",
        "sqlalchemy",
        "repoze.tm2 >= 1.0a4",
        "zope.sqlalchemy >= 0.4",
        ],
    packages=find_packages(exclude=['ez_setup', 'tests']),
    namespace_packages = ['tw2'],
    zip_safe=False,
    include_package_data=True,
    test_suite = 'nose.collector',
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
    ],
)
