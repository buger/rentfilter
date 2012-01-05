from adsparser import *
from google.appengine.ext import db

avtoru_url = "http://all.auto.ru/list/?category_id=15&section_id=1&subscribe_id=&filter_id=&mark_id=0&year%5B1%5D=&year%5B2%5D=&color_id=&price_usd%5B1%5D=@price_start@&price_usd%5B2%5D=@price_end@&currency_key=RUR&body_key=&run%5B1%5D=&run%5B2%5D=&engine_key=0&engine_volume%5B1%5D=&engine_volume%5B2%5D=&drive_key=&engine_power%5B1%5D=&engine_power%5B2%5D=&transmission_key=0&used_key=&wheel_key=&custom_key=1&available_key=&change_key=&owner_pts=&stime=1&country_id=1&has_photo=1&region%5B%5D=89&region_id=89&sort_by=2&city_id=1566&output_format=1&client_id=1&extras%5B1%5D=0&extras%5B2%5D=0&extras%5B3%5D=0&extras%5B4%5D=0&extras%5B5%5D=0&extras%5B6%5D=0&extras%5B7%5D=&extras%5B8%5D=0&extras%5B9%5D=0&extras%5B10%5D=0&extras%5B11%5D=0&extras%5B12%5D=&extras%5B13%5D=0&extras%5B14%5D=0&extras%5B15%5D=0&extras%5B16%5D=0&extras%5B17%5D=0&extras%5B18%5D=&extras%5B19%5D=&extras%5B20%5D=&extras%5B21%5D=&extras%5B22%5D=&extras%5B23%5D=0&extras%5B24%5D=0&extras%5B25%5D=&extras%5B26%5D=&extras%5B27%5D=0&extras%5B28%5D=0&extras%5B29%5D="

class AvtoAd(db.Expando):
    parent_url = db.StringProperty()
    phone = db.StringProperty()
    created_at = db.DateTimeProperty()

class AvtoSettings(db.Expando):
    price_start = db.IntegerProperty(default = 20000)
    price_end = db.IntegerProperty(default = 500000)

class AvtoruParser(SiteParser):
    def get_paged_url(self):
        return "%s&_p=%d" % (self.base_url, self.page_number)

    def get_list(self):
        ads = []
        links = self.page.findAll("a", "offer-list")

        for link in links:
            ads.append(link['href'])

        return ads

class AvtoruAdParser:
    def __init__(self, url):
        self.url = url
        content = MozillaEmulator().download(self.url)

        content = content.decode('utf-8','ignore')

        self.page = BeautifulSoup(content)

    def parse(self):
        try:
            self.phone = self.page.find('ul', 'sale-phones').find('strong').string
        except:
            phone_url = self.page.find('span', id='get-sale-phones')['rel']
            phone_url = "http://cars.auto.ru%s" % phone_url

            content = MozillaEmulator().download(phone_url)
            self.phone = rMOBILE_PHONE.search(content).group(0)

        self.phone = format_phone(self.phone, False)

        self.date = self.page.find('div', 'columns sale-counter').find('strong').string
        self.date = datetime.datetime.strptime(self.date, "%d.%m.%Y")

        return self
