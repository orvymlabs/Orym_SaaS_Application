
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/create.py", line 643, in connect
    return dialect.connect(*cargs, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 621, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server at "dpg-d7gg8sfavr4c738p4fg0-a.ohio-postgres.render.com" (18.118.220.241), port 5432 failed: SSL connection has been closed unexpectedly
(Background on this error at: https://sqlalche.me/e/20/e3q8)
During handling of the above exception, another exception occurred:
Traceback (most recent call last):
  File "/opt/render/project/src/.venv/bin/uvicorn", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/click/core.py", line 1524, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/click/core.py", line 1445, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/click/core.py", line 1308, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/click/core.py", line 877, in invoke
    return callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/uvicorn/main.py", line 412, in main
    run(
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/uvicorn/main.py", line 579, in run
    server.run()
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/uvicorn/server.py", line 66, in run
    return asyncio.run(self.serve(sockets=sockets))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/python/Python-3.11.9/lib/python3.11/asyncio/runners.py", line 190, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/opt/render/project/python/Python-3.11.9/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/python/Python-3.11.9/lib/python3.11/asyncio/base_events.py", line 654, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/uvicorn/server.py", line 70, in serve
    await self._serve(sockets)
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/uvicorn/server.py", line 77, in _serve
    config.load()
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/uvicorn/config.py", line 435, in load
    self.loaded_app = import_from_string(self.app)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/uvicorn/importer.py", line 19, in import_from_string
    module = importlib.import_module(module_str)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/python/Python-3.11.9/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 940, in exec_module
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "/opt/render/project/src/backend/main.py", line 19, in <module>
    from database import init_db
  File "/opt/render/project/src/backend/database.py", line 75, in <module>
    raise RuntimeError(f"Could not connect to production database: {e}")
RuntimeError: Could not connect to production database: (psycopg2.OperationalError) connection to server at "dpg-d7gg8sfavr4c738p4fg0-a.ohio-postgres.render.com" (18.118.220.241), port 5432 failed: SSL connection has been closed unexpectedly
(Background on this error at: https://sqlalche.me/e/20/e3q8)
==> Exited with status 1
==> Common ways to troubleshoot your deploy: https://render.com/docs/troubleshooting-deploys
==> Running 'uvicorn main:app --host 0.0.0.0 --port $PORT'
==> No open ports detected, continuing to scan...
==> Docs on specifying a port: https://render.com/docs/web-services#port-binding
DATABASE CONNECTION FAILED: (psycopg2.OperationalError) connection to server at "dpg-d7gg8sfavr4c738p4fg0-a.ohio-postgres.render.com" (18.118.220.241), port 5432 failed: SSL connection has been closed unexpectedly
(Background on this error at: https://sqlalche.me/e/20/e3q8)
PostgreSQL connection details: dpg-d7gg8sfavr4c738p4fg0-a.ohio-postgres.render.com/orvyn_ut1d
PRODUCTION DATABASE CONNECTION FAILED! STOPPING TO PREVENT DATA LOSS.
Traceback (most recent call last):
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 146, in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 3302, in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/base.py", line 449, in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/base.py", line 1263, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/base.py", line 712, in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/impl.py", line 179, in _do_get
    with util.safe_reraise():
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/util/langhelpers.py", line 146, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/impl.py", line 177, in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/base.py", line 390, in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/base.py", line 674, in __init__
    self.__connect()
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/base.py", line 900, in __connect
    with util.safe_reraise():
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/util/langhelpers.py", line 146, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/base.py", line 896, in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/create.py", line 643, in connect
    return dialect.connect(*cargs, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 621, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
psycopg2.OperationalError: connection to server at "dpg-d7gg8sfavr4c738p4fg0-a.ohio-postgres.render.com" (18.118.220.241), port 5432 failed: SSL connection has been closed unexpectedly
The above exception was the direct cause of the following exception:
Traceback (most recent call last):
  File "/opt/render/project/src/backend/database.py", line 60, in <module>
    with engine.connect() as conn:
         ^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 3278, in connect
    return self._connection_cls(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 148, in __init__
    Connection._handle_dbapi_exception_noconnection(
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 2442, in _handle_dbapi_exception_noconnection
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 146, in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 3302, in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/base.py", line 449, in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/base.py", line 1263, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/base.py", line 712, in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/impl.py", line 179, in _do_get
    with util.safe_reraise():
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/util/langhelpers.py", line 146, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/impl.py", line 177, in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/base.py", line 390, in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/base.py", line 674, in __init__
    self.__connect()
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/base.py", line 900, in __connect
    with util.safe_reraise():
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/util/langhelpers.py", line 146, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/pool/base.py", line 896, in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/create.py", line 643, in connect
    return dialect.connect(*cargs, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 621, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server at "dpg-d7gg8sfavr4c738p4fg0-a.ohio-postgres.render.com" (18.118.220.241), port 5432 failed: SSL connection has been closed unexpectedly
(Background on this error at: https://sqlalche.me/e/20/e3q8)
During handling of the above exception, another exception occurred:
Traceback (most recent call last):
  File "/opt/render/project/src/.venv/bin/uvicorn", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/click/core.py", line 1524, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/click/core.py", line 1445, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/click/core.py", line 1308, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/click/core.py", line 877, in invoke
    return callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/uvicorn/main.py", line 412, in main
    run(
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/uvicorn/main.py", line 579, in run
    server.run()
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/uvicorn/server.py", line 66, in run
    return asyncio.run(self.serve(sockets=sockets))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/python/Python-3.11.9/lib/python3.11/asyncio/runners.py", line 190, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/opt/render/project/python/Python-3.11.9/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/python/Python-3.11.9/lib/python3.11/asyncio/base_events.py", line 654, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/uvicorn/server.py", line 70, in serve
    await self._serve(sockets)
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/uvicorn/server.py", line 77, in _serve
    config.load()
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/uvicorn/config.py", line 435, in load
    self.loaded_app = import_from_string(self.app)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/uvicorn/importer.py", line 19, in import_from_string
    module = importlib.import_module(module_str)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/python/Python-3.11.9/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 940, in exec_module
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "/opt/render/project/src/backend/main.py", line 19, in <module>
    from database import init_db
  File "/opt/render/project/src/backend/database.py", line 75, in <module>
    raise RuntimeError(f"Could not connect to production database: {e}")
RuntimeError: Could not connect to production database: (psycopg2.OperationalError) connection to server at "dpg-d7gg8sfavr4c738p4fg0-a.ohio-postgres.render.com" (18.118.220.241), port 5432 failed: SSL connection has been closed unexpectedly
(Background on this error at: https://sqlalche.me/e/20/e3q8)