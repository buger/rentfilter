# encoding: utf-8

from handlers.base import *
import datetime
import re
from datetime import timedelta
from google.appengine.api import users
import adsparser
import urllib2

rTITLE = re.compile(u"сдается в санкт-петербурге:")

class MainPage(AppHandler):
    def get(self):
        region = self.request.get('region') or 'spb'
        offer_type = self.request.get('offer_type') or 1

        if self.request.get('reset'):
            memcache.delete("main_page_spb")
            memcache.delete("main_page_msk")

        main_page = memcache.get("main_page_%s" % region)

        if not self.request.get('phone') and not self.request.get('metro') and not self.request.get('cursor') and not users.is_current_user_admin():
            if main_page is not None:
                return self.response.out.write(main_page)

        today = datetime.datetime.now() + timedelta(hours = 4) # timezone +4
        yesterday = today - timedelta(days = 1)

        try:
            rating = int(self.request.get('rating'))
        except:
            rating = 100

        if self.request.get('phone'):
            ads = Ad.all().filter("phone =", self.request.get('phone'))
        else:
            ads = Ad.all().order("-created_at").filter("rating =", rating)

        ads = ads.filter("region =", region)
        ads = ads.filter("offer_type =", int(offer_type))

        if self.request.get('metro'):
            ads = ads.filter("address_id =", self.request.get('metro'))

        if self.request.get('cursor'):
            start_from = datetime.datetime.fromtimestamp(int(self.request.get('start_from')))
        else:
            start_from = today-timedelta(minutes = 180)
            timestamp = time.mktime(start_from.timetuple())
            start_from = datetime.datetime.fromtimestamp(timestamp)


        if not users.is_current_user_admin() and not self.request.get('phone'):
            ads = ads.filter("created_at <", start_from)

        if self.request.get('cursor'):
            ads = ads.with_cursor(self.request.get('cursor'))


        phones = []
        unique_ads = []

        for index, ad in enumerate(ads.fetch(40)):
            if index == 0 or ad.created_at and ad.created_at.day != ads[index-1].created_at.day:
                ad.show_date = True

            try:
                ad.title = rTITLE.sub('', ad.title)
            except:
                pass

            if ad.source == 'novoebenevo':
                ad.title = u'сдам'
                ad.url = "http://www.google.com/search?btnI=1&q=%22" + ad.key().name().replace("http://", '') + "%22"

            if self.request.get('phone') or users.is_current_user_admin():
                unique_ads.append(ad)
            else:
                if ad.phone not in phones and not ad.deleted:
                    unique_ads.append(ad)

                phones.append(ad.phone)


        timestamp = time.mktime(start_from.timetuple())

        if len(unique_ads):
            unique_ads[0].show_date = True

        if self.request.get('cursor'):
            html = self.render_template("ads.html", {'ads': unique_ads, 'today': today, 'yesterday': yesterday, 'cursor': ads.cursor(), 'dont_render': True, 'start_from': timestamp})

            self.render_json({'cursor': ads.cursor(), 'region': region, 'html': html });
        else:
            metro_list = adsparser.METRO_LIST[region].items()

            import locale
            def sort_metros(x, y):
                return locale.strcoll(x[1][1].encode('utf-8'), y[1][1].encode('utf-8'))

            metro_list = sorted(metro_list, cmp = sort_metros)

            html = self.render_template("index.html", {'ads': unique_ads, 'today': today, 'yesterday': yesterday, 'cursor': ads.cursor(), 'start_from':timestamp, 'dont_render':True, 'region': region, 'metro_list': metro_list})

            if not self.request.get('phone') and not self.request.get('metro') and not users.is_current_user_admin():
                if not memcache.add("main_page_%s" % region, html, 60*20):
                    logging.error("Memcache set failed.")

            return self.response.out.write(html)


route('/', MainPage)


class CommentsPage(AppHandler):
    def get(self):
        ad = Ad.get_by_key_name(self.request.get('key'))

        self.render_template("comments.html", { 'ad': ad })

route('/comments', CommentsPage)


class FaqPage(AppHandler):
    def get(self):
        self.render_template("faq.html")

route('/faq', FaqPage)

class ApiPage(AppHandler):
    def get(self):
        self.render_template("api.html")

route('/api', ApiPage)


class TosPage(AppHandler):
    def get(self):
        self.render_template("tos.html")

route('/tos', TosPage)

class RulesPage(AppHandler):
    def get(self):
        self.render_template("rules.html")

route('/rules', RulesPage)



class SlandoTest(AppHandler):
    def get(self):
        today = datetime.datetime.now()
        yesterday = today - timedelta(days = 1)

        ads = Ad.all().order("-added_at").filter("parent_url =", "http://nedvizhimost.slando.spb.ru/sankt-peterburg/1572_1.html")

        ads = ads.fetch(100)

        for index, ad in enumerate(ads):
            if index == 0 or (ad.added_at and ad.added_at.day != ads[index-1].added_at.day):
                ad.show_date = True

        #ads = filter(lambda x: x.phone is not None, ads)

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


class OlxTest(AppHandler):
    def get(self):
        today = datetime.datetime.now()
        yesterday = today - timedelta(days = 1)

        ads = Ad.all().order("-added_at").filter("parent_url =", "http://saintpetersburg.olx.ru/cat-363")

        ads = ads.fetch(100)

        for index, ad in enumerate(ads):
            if index == 0 or (ad.added_at and ad.added_at.day != ads[index-1].added_at.day):
                ad.show_date = True

        ads = filter(lambda x: x.phone is not None, ads)

        self.render_template("index.html", {'ads': ads, 'hide_filter': True, 'hide_controls': True, 'today':today, 'yesterday':yesterday})

route('/olx/spb', OlxTest)


class AvitoTest(AppHandler):
    def get(self):
        today = datetime.datetime.now()
        yesterday = today - timedelta(days = 1)

        ads = Ad.all().order("-added_at").filter("parent_url =", "http://www.avito.ru/catalog/kvartiry-24/sankt-peterburg-653240/params.201_1060?user=1")

        ads = ads.fetch(100)

        for index, ad in enumerate(ads):
            if index == 0 or (ad.added_at and ad.added_at.day != ads[index-1].added_at.day):
                ad.show_date = True

        ads = filter(lambda x: x.phone is not None, ads)

        self.render_template("index.html", {'ads': ads, 'hide_filter': True, 'hide_controls': True, 'today':today, 'yesterday':yesterday})

route('/avito/spb', AvitoTest)


class OneGSTest(AppHandler):
    def get(self):
        today = datetime.datetime.now()
        yesterday = today - timedelta(days = 1)

        ads = Ad.all().order("-added_at").filter("parent_url =", "http://spb.1gs.ru/arenda-kvartiry.1gs")

        ads = ads.fetch(100)

        for index, ad in enumerate(ads):
            if index == 0 or (ad.added_at and ad.added_at.day != ads[index-1].added_at.day):
                ad.show_date = True

        #ads = filter(lambda x: x.phone is not None, ads)

        self.render_template("index.html", {'ads': ads, 'hide_filter': True, 'hide_controls': True, 'today':today, 'yesterday':yesterday})

route('/1gs/spb', OneGSTest)


class OneGSTestMsk(AppHandler):
    def get(self):
        today = datetime.datetime.now()
        yesterday = today - timedelta(days = 1)

        ads = Ad.all().order("-added_at").filter("parent_url =", "http://msk.1gs.ru/arenda-kvartiry.1gs")

        ads = ads.fetch(100)

        for index, ad in enumerate(ads):
            if index == 0 or (ad.added_at and ad.added_at.day != ads[index-1].added_at.day):
                ad.show_date = True

        #ads = filter(lambda x: x.phone is not None, ads)

        self.render_template("index.html", {'ads': ads, 'hide_filter': True, 'hide_controls': True, 'today':today, 'yesterday':yesterday})

route('/1gs/msk', OneGSTestMsk)

class SiteTest(AppHandler):
    def get(self):
        today = datetime.datetime.now()
        yesterday = today - timedelta(days = 1)

        ads = Ad.all().order("-added_at").filter("parent_url =", self.request.get('url'))

        ads = ads.fetch(500)

        for index, ad in enumerate(ads):
            if index == 0 or (ad.added_at and ad.added_at.day != ads[index-1].added_at.day):
                ad.show_date = True

        #ads = filter(lambda x: x.phone is not None, ads)

        self.render_template("index.html", {'ads': ads, 'hide_filter': True, 'hide_controls': True, 'today':today, 'yesterday':yesterday})

route('/site/test', SiteTest)
