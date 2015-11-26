import tornado.ioloop
import tornado.web
import tornado.template
import os

def start_proxy_web(proxy_pool, listen_port):
    class MainHandler(tornado.web.RequestHandler):
        def get(self):
            loader = tornado.template.Loader(os.path.abspath(os.path.dirname(__file__)) + "/static/html")
            self.write(loader.load("cms.html").generate(proxy_pool = proxy_pool))
    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
    }
    application = tornado.web.Application([
        (r"/", MainHandler),
    ], **settings)
    application.listen(listen_port)
    def run():
        tornado.ioloop.IOLoop.current().start()
    import threading
    threading.Thread(target=run).start()