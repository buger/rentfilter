# encoding: utf-8

from handlers.base import *
import datetime
import re
from datetime import timedelta
from google.appengine.api import users

rTITLE = re.compile(u"Сдается в Санкт-Петербурге:")

class MainPage(AppHandler):
    def get(self):
        today = datetime.datetime.now()
        yesterday = today - timedelta(days = 1)

        if self.request.get('phone'):
            ads = Ad.all().filter("phone =", self.request.get('phone'))
        else:
            ads = Ad.all().order("-added_at").filter("rating =", 100)

#        if not users.is_current_user_admin():
#            ads = ads.filter("added_at <", today-timedelta(minutes = 20))

        ads = ads.fetch(50)

        for index, ad in enumerate(ads):
            if index == 0 or (ad.added_at and ad.added_at.day != ads[index-1].added_at.day):
                ad.show_date = True

            ad.title = rTITLE.sub('', ad.title)


        self.render_template("index.html", {'ads': ads, 'today': today, 'yesterday': yesterday})

route('/', MainPage)
