.. _design:

Design
======


Features
--------

`Session and Transaction Management`

    It is desirable to wrap individual HTTP requests in database transactions and ORM sessions. This ensures, for example, that if a web request fails part way through, no changes are made to the database. More advanced session management can retry a request if it fails due to a transitive error. Some also avoid the overhead of a database transaction for read-only requests.

    Many web frameworks include session and transaction management. For example, TurboGears 2 uses `Repoze.tm <http://repoze.org/tmdemo.html>`_ and `zope.sqlalchemy <http://pypi.python.org/pypi/zope.sqlalchemy>`_ to support this.


`Loading and Saving Data`

    For loading, data needs to be converted from the format loaded from the database into a format that can be displayed by the forms library. This conversion needs to be performed in reverse for saving. ToscaWidgets itself makes this relatively straightforward, but some conversion is still necessary. A database layer should aim to do all such conversion in a transparent manner.

    Applications often contain quite repetitive code to initiate the act of loading and saving data. A database layer should aim to do this automatically.


`Populating Selection Fields`

    Selection fields, such as dropdown lists, often have their options sourced from a database table. A database layer should load these automatically, and ideally support cacheing for efficiency.


`Generating Widget Definitions`

    Many applications contain long widget definitions that closely match the underlying database models. The idea is to reduce application code by automatically generating these definitions. Some tools exist that automatically generate source code at design time, but tw2.sqla avoids that approach and generates the definitions at run time.

    For flexibility it is very important to be able to override the automatic definitions. This needs to be possible on a per-field basis. It should also be possible to provide a customised policy, specifying the rules for generating widgets from model definitions. For example, an application may decide that all fields named "comment" should have a TextArea, instead of a TextField.



Existing Technology
-------------------

Django has long had the `Django admin site <http://docs.djangoproject.com/en/dev/ref/contrib/admin/>`_, which is a key feature and receives much development attention. There have been several projects in the Python WSGI space to provide automatic form creation, or administrative interfaces. For example, TurboGears 1.0 had both `FastData <http://docs.turbogears.org/FastData>`_ and `Catwalk <http://docs.turbogears.org/1.0/Catwalk>`_. Such projects have tended to be relatively fragmented and unmaintained. A particular challenge was that FastData and Catwalk originally only worked with SQLObject and could not easily be changed to support SQLAlchemy.

As of 2010, the leading efforts in the Python WSGI space are `Sprox <http://sprox.org/>`_ and `Rum <http://www.python-rum.org/>`_. Sprox helps automatically define forms and views from database models; it is a relatively thin layer that can be readily customised. Rum is a somewhat thicker layer, almost a web framework in itself, and is primarily aimed at producing automatic admin interfaces. Both work with SQLAlchemy and ToscaWidgets, while making efforts to abstract the dependencies.

Sprox and Rum are the primary influences for tw2.sqla. One major difference is that tw2.sqla is only intended to work with SQLAlchemy and ToscaWidgets 2, and makes no attempt to abstract the dependencies. Here is a high-level comparison of their functionality:

==================================  =======================================================  ==============================================  =======================================================
Feature                             Sprox                                                    Rum                                             tw2.sqla
==================================  =======================================================  ==============================================  =======================================================
Session and transaction management  None; relies on the containing framework                 Supported, same technique as TG2                Supported, same technique as TG2
Loading and saving data             None; responsibility of the application                  Supported, with both conversion and initiation  Supported, with both conversion and initiation
Generating widget definitions       Supported, with customisation of both fields and policy  Supported; Sprox can be used if desired         Supported, with customisation of both fields and policy
Populating selection fields         Supported; no cacheing                                   Supported; no cacheing                          Supported, with cacheing
==================================  =======================================================  ==============================================  =======================================================



Open issues
-----------

RelativeValidator, efficiency consideration: Say we have a ManyToOne relation, "status" using the column "status_id". We could have a SelectionField on "status" using RelatedValidator, or one on "status_id" using IntValidator. The former would do stronger validation, while the latter would be more efficient.

