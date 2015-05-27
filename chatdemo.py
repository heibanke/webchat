#!/usr/bin/env python
# -*- coding:utf-8 -*-  

import redis
import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import os.path
import uuid
import datetime
from tornado.web import decode_signed_value
from tornado.options import define, options
import sockjs.tornado

db = redis.StrictRedis(host='localhost', port=6379, db=0)

define("port", default=8888, help="run on the given port", type=int)

SETTINGS = dict(cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/login",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            debug=True)
            
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
        self.render("index.html", messages=db.lrange('messages',-100,-1), name=name)

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

    def on_open(self,info):
        self.broadcast(self.participants, info_get_secure_cookie(info,"user")+" joined.")   
        self.username = info_get_secure_cookie(info,"user")
        ChatConnection.participants.add(self)

    def on_close(self):
        ChatConnection.participants.remove(self)
        self.broadcast(self.participants, self.username+" left.")


    def on_message(self, message):
        parsed = tornado.escape.json_decode(message)
        #logging.info("got message %r, %s", message, parsed)
        chat = "%s:%s (--%s)"%(parsed["username"],parsed["text"],datetime.datetime.now().ctime())
        db.rpush('messages',chat)
        self.broadcast(self.participants, chat)


def get_morsel_cookie(info, name, default=None):
    """Gets the value of the cookie with the given name, else default."""
    if info.cookies is not None and name in info.cookies:
        return info.cookies[name].value
    return default        
        
        
def info_get_secure_cookie(info, name, value=None, max_age_days=31,
                      min_version=None):

    if value is None:
        value = get_morsel_cookie(info,name)
    return decode_signed_value(SETTINGS["cookie_secret"],
                                   name, value, max_age_days=max_age_days,
                                   min_version=min_version)          
        
def main():
    ChatRouter = sockjs.tornado.SockJSRouter(ChatConnection, '/chat')
    tornado.options.parse_command_line()
    app = tornado.web.Application(            
            handlers=[(r"/", MainHandler),
                      (r"/login",LoginHandler),
                      (r"/logout",LogoutHandler)] + ChatRouter.urls,
            **SETTINGS
                      )
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
