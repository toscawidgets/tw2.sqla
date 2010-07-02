import tw2.core as twc, tw2.sqla as tws, sqlalchemy as sa, elixir as el, webtest, webob as wo, threading, os


# Note: we can't use :memory: from two threads
if os.path.exists('test.db'):
    os.unlink('test.db')
el.metadata = sa.MetaData('sqlite:///test.db')
el.session = tws.transactional_session()
class Test(el.Entity):
    name = el.Field(el.String)
el.setup_all()
el.metadata.create_all()


def app(environ, start_response):
    req = wo.Request(environ)
    resp = wo.Response(request=req, content_type="text/html; charset=UTF8")
    if req.path == '/createok':
        Test(name='paj')
    if req.path == '/createfail':
        Test(name='paj')
        resp.status = 404
    if req.path == '/read':
        global keep # ensure the object isn't expired due to weakref session
        keep = Test.query.all()[0]
        resp.body = keep.name.encode('utf-8')
    if req.path == '/update': # Change object
        Test.query.all()[0].name = 'bob'
    return resp(environ, start_response)
app = twc.make_middleware(app, repoze_tm=True)
app = webtest.TestApp(app)


def test_createok():
    el.session.remove()
    before = len(Test.query.all())
    app.get('/createok')
    el.session.remove()
    assert(len(Test.query.all()) == before + 1)

def test_createfail():
    el.session.remove()
    before = len(Test.query.all())
    app.get('/createfail', expect_errors=True)
    el.session.remove()
    assert(len(Test.query.all()) == before)

def test_freshness():
    assert(app.get('/read').body == 'paj')
    # Update the object in a separate thread
    class ThreadB(threading.Thread):
        def run(self):
            app.get('/update')
    thrdb = ThreadB()
    thrdb.start()
    thrdb.join()
    # Check it's updated in the first thread
    assert(app.get('/read').body == 'bob')
