#!/usr/bin/env python
# -*- coding:utf-8 -*-  


import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import os.path
import uuid
import datetime

from tornado.options import define, options
import sockjs.tornado

define("port", default=8888, help="run on the given port", type=int)

PASSWORD="2015-05-24longping"

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class MainHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        self.render("index.html", messages=ChatConnection.cache, name=name)

class LoginHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.render("login.html",error="")
        else:
            self.redirect("/")
            return

    def post(self):
        if self.get_argument("password")==PASSWORD:
            self.set_secure_cookie("user", self.get_argument("name"))
            self.redirect("/")    
            return
        else:
            self.render("login.html",error="username or password not match, please try again!") 

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/login") 
        return
        

class ChatConnection(sockjs.tornado.SockJSConnection):
    participants = set()
    cache = []
    cache_size = 200


    def on_open(self,info):
        self.broadcast(self.participants, "Someone joined.")    
        ChatConnection.participants.add(self)

    def on_close(self):
        ChatConnection.participants.remove(self)
        self.broadcast(self.participants, "Someone left.")


    def on_message(self, message):
        parsed = tornado.escape.json_decode(message)
        logging.info("got message %r, %s", message, parsed)
        chat = "%s:%s (--%s)"%(parsed["username"],parsed["text"],datetime.datetime.now().ctime())
        ChatConnection.cache.append(chat)
        if len(ChatConnection.cache) > ChatConnection.cache_size:
            ChatConnection.cache = ChatConnection.cache[-ChatConnection.cache_size:]        
        self.broadcast(self.participants, chat)

        
        
def main():
    ChatRouter = sockjs.tornado.SockJSRouter(ChatConnection, '/chat')
    tornado.options.parse_command_line()
    app = tornado.web.Application(            
            handlers=[(r"/", MainHandler),
                      (r"/login",LoginHandler),
                      (r"/logout",LogoutHandler)] + ChatRouter.urls,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/auth/login",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            debug=True,
                      )
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
