import tw2.core as twc, tw2.sqla as tws, sqlalchemy as sa, elixir as el, webtest, webob as wo, threading, os, random

#import testapi

class TestTransactions(object):
    def setup(self):
        #testapi.setup()
        # Note: we can't use :memory: from two threads
        try:
            os.unlink('test.db')
        except:
            pass
        el.metadata = sa.MetaData('sqlite:///test.db')
        el.session = tws.transactional_session()
        class Test(el.Entity):
            name = el.Field(el.String)
        self.DBEnt = Test
        el.setup_all()
        el.metadata.create_all()

        self.DBEnt(name='rjb')
        import transaction
        transaction.commit()

        def app(environ, start_response):
            req = wo.Request(environ)
            resp = wo.Response(
                request=req, content_type="text/html; charset=UTF8")
            if req.path == '/createok':
                self.DBEnt(name='paj')
            if req.path == '/createfail':
                self.DBEnt(name='paj')
                resp.status = 404
            if req.path == '/read':
                # ensure the object isn't expired due to weakref session
                global keep
                keep = self.DBEnt.query.all()[0]
                resp.body = keep.name.encode('utf-8')
            if req.path == '/update': # Change object
                self.DBEnt.query.all()[0].name = 'bob'
            return resp(environ, start_response)
        self.app = twc.make_middleware(app, repoze_tm=True)
        self.app = webtest.TestApp(self.app)

    def test_createok(self):
        el.session.remove()
        before = len(self.DBEnt.query.all())
        self.app.get('/createok')
        el.session.remove()
        assert(len(self.DBEnt.query.all()) == before + 1)

    def test_createfail(self):
        el.session.remove()
        before = len(self.DBEnt.query.all())
        self.app.get('/createfail', expect_errors=True)
        el.session.remove()
        assert(len(self.DBEnt.query.all()) == before)

    def test_freshness(self):
        assert(self.app.get('/read').body == 'rjb')
        # Update the object in a separate thread
        class ThreadB(threading.Thread):
            def run(shmelf):
                self.app.get('/update')
        thrdb = ThreadB()
        thrdb.start()
        thrdb.join()
        # Check it's updated in the first thread
        assert(self.app.get('/read').body == 'bob')
