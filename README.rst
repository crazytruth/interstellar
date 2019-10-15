============
interstellar
============


.. image:: https://img.shields.io/github/tag/MyMusicTaste/interstellar.svg
        :target: https://pypi.python.org/pypi/interstellar

.. image:: https://img.shields.io/travis/crazytruth/interstellar.svg
        :target: https://travis-ci.org/crazytruth/interstellar

.. image:: https://readthedocs.org/projects/interstellar/badge/?version=latest
        :target: https://interstellar.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


.. image:: https://pyup.io/repos/github/crazytruth/interstellar/shield.svg
     :target: https://pyup.io/repos/github/crazytruth/interstellar/
     :alt: Updates



A grpc plugin for interservice communications for insanic.


* Free software: MIT license
* Documentation: https://interstellar.readthedocs.io.


Background
----------

You might be wondering why. What is interstellar?


Features
--------

* Client interface for sending grpc requests

Prerequisites
-------------

To install interstellar for both client and server usage.

.. code-block:: bash

    # for basic usage
    $ pip install interstellar

    # for development
    $ pip install interstellar[development]

    # for docs
    $ pip install interstellar[docs]

    # for cli
    $ pip install interstellar[cli]


GRPC Packages
=============

A little background information on the packages interstellar interacts with.
Our [protobuf](https://github.com/MyMusicTaste/mmt-msa-protobuf) repository holds all our protobuf files.
Please read up on the protobuf repo readme on how it works.

Once you have selected the grpc methods you will be using, we need to install the grpc packages.
In our example, we will be using `grpc-test-monkey`. (i.e. `$ pip install grpc-test-monkey`)

1. A couple things to note is that interstellar will be looking through all installed packages for the prefix `grpc-`

2. The second token indicates the `service` you will want to fire request to. (i.e. "test")
These service methods will be bound to the `service` object.

3. The third (i.e. "monkey") is the namespace. More on this later.

4. Another thing to note, but not needed at this point in time, is the actual `Stub` and `ServiceMethod` within the package
that you will need to know the name of.

5. The same package will be used for both the client side and server side services, but these protobuf files will
probably be created by the server side developer.



Interstellar Client
-------------------

If you will be needing to fire grpc requests to certain services. This is what you will need.


Initialization
==============

First we need to initialize app for client side usage.

.. code-block:: bash

    # in app.py

    from insanic import Insanic
    from interstellar.client import InterstellarClient

    app = Insanic('A')

    InterstellarClient.init_app(app)

This does the following:

1. Loads interstellar client configs

2. Binds a `grpc` interface to Insanic's service object, but only to the ones defined in your `SERVICE_CONNECTIONS`
config.

3. Imports and Loads grpc packages

For more information, look at the code.

Basic Usage
===========

After we have initialized `Insanic` with `InterstellarClient` and have installed the respective grpc packages,
we can now go ahead and use the provided interface for dispatching requests.


.. code-block:: python

    # somewhere.py
    from insanic.loading import get_service


    service = get_service('test')

    with service.grpc("monkey", "ApeService", "GetChimpanzee") as method:
        request = method.request_type(id='1', include="sound")
        reply = await method(request)

        assert reply.extra == "woo woo ahh ahh"

    # or we can also use the stubs if there are different methods we want to use

    with service.grpc("monkey", "ApeService") as stub:
        chimpanzee_request = stub.GetChimpanzee.request_type(id="1", include="sound")
        chimpanzee_task = stub.GetChimpanzee(chimpanzee_request)

        gorilla_request = stub.GetGorilla.request_type(id="1", include="sound")
        gorilla_task = stub.GetGorilla(gorilla_request)

        chimpanzee_reply, gorilla_reply = await asyncio.gather([chimpanzee_task, gorilla_task])


A couple things to note in this example.

1. "monkey" is the namespace as defined in `grpc-test-monkey`. (i.e. last word in package name)

2. "ApeService" is the generated Stub class. Refer to either protobuf file/service definition or your friendly grpc
documentation

3. "GetChimpanzee" is the service method defined in the Stub. Again refer to documentation or protobuf file.

4. Each eventual service method (either as an attribute of the stub, or from the context manager) will have
a `request_type` attribute. This is the actual object you will need to create as defined in the service definition
and will be sent in the actual request.

5. If no issues arise, you will get a reply with the reply object, in which you can access the fields as attributes.


Interstellar Server
-------------------

The server side requires a little more that just plug and play compared to the client side.

Setup and Initialization
========================

There are a couple thing that need to be done. We will continue with our `grpc-test-monkey`
example.

1. First we need to install the package that you have created.

.. code-block:: bash

    $ pip install grpc-test-monkey

2. Now, you need to create the actual handler that will handle the request.

.. code-block:: python

    # somewhere.py maybe handlers.py?

    from grpc_test_monkey.monkey_grpc import ApeServiceBase

    class ApeService(ApeServiceBase):

        async def GetChimpanzee(self, stream):
            request = await stream.recv_message()

            # ... do some chimpanzee stuff

            await stream.send_message(ApeResponse(id=1, extra="woo woo ahh ahh"))

        async def GetGorilla(self, stream):
            request = await stream.recv_message()

            # ... do some gorilla stuff

            await stream.send_message(ApeResponse(id=1, extra="rahh"))

3. Once we have created the service. We need interstellar to load this.
And we can do this by defining the location with `INTERSTELLAR_SERVERS`

.. code-block:: python

    # in your config.py

    INTERSTELLAR_SERVERS = ['test.handlers.ApeService']


4. Now to initialize the grpc server.

.. code-block:: python

    # in app.py

    from insanic import Insanic
    from interstellar.server import InterstellarServer

    app = Insanic('test')

    InterstellarServer.init_app(app)


* This will do the following:

    1. Load server side configuration.

    2. Load the servers defined in config `INTERSTELLAR_SERVERS`. (More on this later)

    3. Attach listeners to app for grpc server start and stop

    4. Attach grpc events.

    5. Registers plugin.

5. RUN!



Running Tests
-------------

Make sure you have development extras installed!

.. code-block:: bash

    $ pytest

    # with coverage
    $ pytest --cov=interstellar --cov-report term-missing:skip-covered





Credits
-------

* **Kwang Jin Kim** - *Initial Work* - [crazytruth](https://github.com/crazytruth)

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
