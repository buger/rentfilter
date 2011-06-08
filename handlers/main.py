# encoding: utf-8

from handlers.base import *
import datetime
import re
from datetime import timedelta
from google.appengine.api import users

rTITLE = re.compile(u"сдается в санкт-петербурге:")

class MainPage(AppHandler):
    def get(self):
        main_page = memcache.get("main_page_6")

        if not self.request.get('phone') and not self.request.get('cursor') and not users.is_current_user_admin():
            if main_page is not None:
                return self.response.out.write(main_page)

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

        if self.request.get('cursor'):
            start_from = datetime.datetime.fromtimestamp(int(self.request.get('start_from')))
        else:
            start_from = today-timedelta(minutes = 180)
            timestamp = time.mktime(start_from.timetuple())
            start_from = datetime.datetime.fromtimestamp(timestamp)


        if not users.is_current_user_admin() and not self.request.get('phone'):
            ads = ads.filter("added_at <", start_from)

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

            if self.request.get('phone'):
                unique_ads.append(ad)
            else:
                if ad.phone not in phones and not ad.deleted:
                    unique_ads.append(ad)

                phones.append(ad.phone)

        timestamp = time.mktime(start_from.timetuple())

        if self.request.get('cursor'):
            html = self.render_template("ads.html", {'ads': unique_ads, 'today': today, 'yesterday': yesterday, 'cursor': ads.cursor(), 'dont_render': True, 'start_from': timestamp})

            self.render_json({'cursor': ads.cursor(), 'html': html });
        else:
            html = self.render_template("index.html", {'ads': unique_ads, 'today': today, 'yesterday': yesterday, 'cursor': ads.cursor(), 'start_from':timestamp, 'dont_render':True})

            if not self.request.get('phone') and not users.is_current_user_admin():
                if not memcache.add("main_page_6", html, 60*20):
                    logging.error("Memcache set failed.")

            return self.response.out.write(html)


route('/', MainPage)


class FaqPage(AppHandler):
    def get(self):
        self.render_template("faq.html")

route('/faq', FaqPage)

class ApiPage(AppHandler):
    def get(self):
        self.render_template("api.html")

route('/api', ApiPage)


class SlandoTest(AppHandler):
    def get(self):
        today = datetime.datetime.now()
        yesterday = today - timedelta(days = 1)

        ads = Ad.all().order("-added_at").filter("parent_url =", "http://nedvizhimost.slando.spb.ru/sankt-peterburg/1572_1.html")

        ads = ads.fetch(100)

        for index, ad in enumerate(ads):
            if index == 0 or (ad.added_at and ad.added_at.day != ads[index-1].added_at.day):
                ad.show_date = True

        ads = filter(lambda x: x.phone is not None, ads)

        self.render_template("index.html", {'ads': ads, 'hide_filter': True, 'hide_controls': True, 'today':today, 'yesterday':yesterday})

route('/slando/spb', SlandoTest)


class IRRTest(AppHandler):
    def get(self):
        today = datetime.datetime.now()
        yesterday = today - timedelta(days = 1)

        ads = Ad.all().order("-added_at").filter("parent_url =", "http://saint-petersburg.irr.ru/real-estate/rent/search/sourcefrom=1/page1/")

        ads = ads.fetch(100)

        for index, ad in enumerate(ads):
            if index == 0 or (ad.added_at and ad.added_at.day != ads[index-1].added_at.day):
                ad.show_date = True

        ads = filter(lambda x: x.phone is not None, ads)

        self.render_template("index.html", {'ads': ads, 'hide_filter': True, 'hide_controls': True, 'today':today, 'yesterday':yesterday})

route('/irr/spb', IRRTest)
