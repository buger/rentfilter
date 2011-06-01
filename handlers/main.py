# encoding: utf-8

from handlers.base import *
import datetime
import re
from datetime import timedelta
from google.appengine.api import users

rTITLE = re.compile(u"сдается в санкт-петербурге:")

class MainPage(AppHandler):
    def get(self):
        today = datetime.datetime.now()
        yesterday = today - timedelta(days = 1)

        try:
            rating = int(self.request.get('rating'))
        except:
            rating = 100

        if self.request.get('phone'):
            ads = Ad.all().filter("phone =", self.request.get('phone'))
        else:
            ads = Ad.all().order("-added_at").filter("rating =", rating)

        if not users.is_current_user_admin():
            ads = ads.filter("added_at <", today-timedelta(minutes = 20))

        if self.request.get('cursor'):
            ads = ads.with_cursor(self.request.get('cursor'))

        phones = []
        unique_ads = []

        for index, ad in enumerate(ads.fetch(40)):
            if index == 0 or (ad.added_at and ad.added_at.day != ads[index-1].added_at.day):
                ad.show_date = True

            try:
                ad.title = rTITLE.sub('', ad.title)
            except:
                pass

            if ad.phone not in phones and not ad.deleted:
                unique_ads.append(ad)

        if self.request.get('cursor'):
            html = self.render_template("ads.html", {'ads': unique_ads, 'today': today, 'yesterday': yesterday, 'cursor': ads.cursor(), 'dont_render': True})

            self.render_json({'cursor': ads.cursor(), 'html': html });
        else:
            self.render_template("index.html", {'ads': unique_ads, 'today': today, 'yesterday': yesterday, 'cursor': ads.cursor()})

route('/', MainPage)
