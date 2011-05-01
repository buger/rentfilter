# encoding: utf-8
from BeautifulSoup import BeautifulSoup
import re
import urllib2
import hashlib
from dateutil import parser
from dateutil.relativedelta import relativedelta
import logging
from simplejson import loads,dumps
import cookielib
import md5
from datetime import datetime

rPHONE = re.compile("(?:\d[\s\-\)\(\dx\.]{0,2}){6,12}")
rMOBILE_PHONE = re.compile("9(?:\d[\s\-\)\(\dx\.]{0,2}){6,12}")
rREPLACE = re.compile("\D")
rPHONE_PREFIX = re.compile("^[87]")
rCITY_PREFIX = re.compile("^812")
rAGENT = re.compile("(агенство|комиссия|скидки по комиссии|комиссию)")
rOWNER = re.compile("(хозяина|хозяин|без комиссии|без агенства|агенства не|частное|агентам не|без посредников|не агенство)")

class MozillaEmulator(object):
    def __init__(self,cacher={},trycount=0):
        """Create a new MozillaEmulator object.

        @param cacher: A dictionary like object, that can cache search results on a storage device.
            You can use a simple dictionary here, but it is not recommended.
            You can also put None here to disable caching completely.
        @param trycount: The download() method will retry the operation if it fails. You can specify -1 for infinite retrying.
                A value of 0 means no retrying. A value of 1 means one retry. etc."""
        self.cacher = cacher
        self.cookies = cookielib.CookieJar()
        self.debug = False
        self.trycount = trycount
    def _hash(self,data):
        h = md5.new()
        h.update(data)
        return h.hexdigest()

    def build_opener(self,url,postdata=None,extraheaders={},forbid_redirect=False):
        txheaders = {
            'Accept':'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
            'Accept-Language':'ru,en;q=0.8,ru-ru;q=0.5,en-us;q=0.3',
#            'Accept-Encoding': 'gzip, deflate',
            'Accept-Charset': 'utf-8,cp1251;q=0.7,*;q=0.7',
#            'Keep-Alive': '300',
#            'Connection': 'keep-alive',
#            'Cache-Control': 'max-age=0',
        }
        for key,value in extraheaders.iteritems():
            txheaders[key] = value
        req = urllib2.Request(url, postdata, txheaders)
        self.cookies.add_cookie_header(req)
        if forbid_redirect:
            redirector = HTTPNoRedirector()
        else:
            redirector = urllib2.HTTPRedirectHandler()

        http_handler = urllib2.HTTPHandler(debuglevel=self.debug)
        https_handler = urllib2.HTTPSHandler(debuglevel=self.debug)

        u = urllib2.build_opener(http_handler,https_handler,urllib2.HTTPCookieProcessor(self.cookies),redirector)
        u.addheaders = [('User-Agent','Mozilla/5.0 (Windows; U; Windows NT 5.1; hu-HU; rv:1.7.8) Gecko/20050511 Firefox/1.0.4')]
        if not postdata is None:
            req.add_data(postdata)
        return (req,u)

    def download(self,url,postdata=None,extraheaders={},forbid_redirect=False,
            trycount=None,fd=None,onprogress=None,only_head=False):
        """Download an URL with GET or POST methods.

        @param postdata: It can be a string that will be POST-ed to the URL.
            When None is given, the method will be GET instead.
        @param extraheaders: You can add/modify HTTP headers with a dict here.
        @param forbid_redirect: Set this flag if you do not want to handle
            HTTP 301 and 302 redirects.
        @param trycount: Specify the maximum number of retries here.
            0 means no retry on error. Using -1 means infinite retring.
            None means the default value (that is self.trycount).
        @param fd: You can pass a file descriptor here. In this case,
            the data will be written into the file. Please note that
            when you save the raw data into a file then it won't be cached.
        @param onprogress: A function that has two parameters:
            the size of the resource and the downloaded size. This will be
            called for each 1KB chunk. (If the HTTP header does not contain
            the content-length field, then the size parameter will be zero!)
        @param only_head: Create the openerdirector and return it. In other
            words, this will not retrieve any content except HTTP headers.

        @return: The raw HTML page data, unless fd was specified. When fd
            was given, the return value is undefined.
        """
        if trycount is None:
            trycount = self.trycount
        cnt = 0
        while True:
            try:
                key = self._hash(url)
                if (self.cacher is None) or (not self.cacher.has_key(key)):
                    req,u = self.build_opener(url,postdata,extraheaders,forbid_redirect)
                    openerdirector = u.open(req)
                    if self.debug:
                        print req.get_method(),url
                        print openerdirector.code,openerdirector.msg
                        print openerdirector.headers
                    self.cookies.extract_cookies(openerdirector,req)
                    if only_head:
                        return openerdirector
                    if openerdirector.headers.has_key('content-length'):
                        length = long(openerdirector.headers['content-length'])
                    else:
                        length = 0
                    dlength = 0
                    if fd:
                        while True:
                            data = openerdirector.read(1024)
                            dlength += len(data)
                            fd.write(data)
                            if onprogress:
                                onprogress(length,dlength)
                            if not data:
                                break
                    else:
                        data = ''
                        while True:
                            newdata = openerdirector.read(1024)
                            dlength += len(newdata)
                            data += newdata
                            if onprogress:
                                onprogress(length,dlength)
                            if not newdata:
                                break
                        #data = openerdirector.read()
                        if not (self.cacher is None):
                            self.cacher[key] = data
                else:
                    data = self.cacher[key]
                #try:
                #    d2= GzipFile(fileobj=cStringIO.StringIO(data)).read()
                #    data = d2
                #except IOError:
                #    pass
                return data
            except urllib2.URLError:
                cnt += 1
                if (trycount > -1) and (trycount < cnt):
                    raise
                # Retry :-)
                if self.debug:
                    print "MozillaEmulator: urllib2.URLError, retryting ",cnt


    def post_multipart(self,url,fields, files, forbid_redirect=True):
        """Post fields and files to an http host as multipart/form-data.
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files
        Return the server's response page.
        """
        content_type, post_data = encode_multipart_formdata(fields, files)
        result = self.download(url,post_data,{
            'Content-Type': content_type,
            'Content-Length': str(len(post_data))
        },forbid_redirect=forbid_redirect
        )
        return result


def format_phone(phone):
    phone = rREPLACE.sub('', phone)

    if len(phone) >= 9 and rPHONE_PREFIX.match(phone):
        phone = rPHONE_PREFIX.sub('', phone)

    phone = re.sub("^0", '', phone)
    phone = rCITY_PREFIX.sub('', phone)

    return phone


class BaseAdParser:
    def __init__(self, url):
        self.url = url
        content = MozillaEmulator().download(self.url)

        content = content.decode('utf-8','ignore')

        self.page = BeautifulSoup(content)

    def parse(self):
        self.title = re.sub(u"\n", "", self.get_title().strip().lower())

        self.content = self.get_content().lower().strip()


        self.md5 = self.get_md5(self.content)

        self.contact = self.get_contact().lower().strip()

        self.phone = self.get_phone()
        self.date = self.get_date()
        self.date = self.date

        if self.__class__.__name__ == 'EmlsAdParser':
            self.contact = self.get_md5(self.contact)

        if type(self.date).__name__ == 'str':
            try:
                self.date = parser.parse(self.date)
            except:
                self.date = None

        self.agent = self.is_agent()

        title = unicode(self.title).encode('utf-8', 'ignore')
        try:
            content = unicode(self.content).encode('utf-8', 'ignore')
        except:
            content = self.content
        contact = unicode(self.contact).encode('utf-8', 'ignore')

        content_for_search = "%s %s %s" % (content, contact, title)

        if not self.agent and rOWNER.search(content_for_search):
            self.agent = False
        else:
            if self.phone is None or rAGENT.search(content_for_search):
                self.agent = True

        return self

    def get_phone(self, expression = rMOBILE_PHONE):
        phone_match = expression.search(self.contact)

        if phone_match is None:
            phone_match = expression.search(self.content)

        if phone_match:
            return format_phone(phone_match.group(0))
        elif expression != rPHONE:
            return self.get_phone(rPHONE)

    def get_md5(self, content):
        md5 = hashlib.md5()
        try:
            content = unicode(content).encode('utf-8')
        except:
            pass
        md5.update(content)

        return md5.hexdigest()

    def __str__(self):
        arr = []
        for attr in [self.agent, self.title, self.date, self.contact, self.phone, self.md5, self.url]:
            if attr is not None:
                try:
                    arr.append(unicode(attr).encode('utf-8', 'ignore'))
                except:
                    arr.append(str(attr))

        return ', '.join(arr)



class SlandoAdParser(BaseAdParser):
    MONTH = [[u"Января", "Jan"], [u"Февраля", "Feb"], [u"Марта", "Mar"], [u"Апреля", "Apr"], [u"Мая", "May"], [u"Июня","Jun"], [u"Июля","Jul"], [u"Августа","Aug"], [u"Сентября", "Sept"], [u"Октября", "Oct"], [u"Ноября","Nov"], [u"Декабря","Dec"]]

    def get_title(self):
        contents = self.page.find('h1').contents
        title = "".join([item.string or "" for item in contents])

        return title

    def get_name(self):
        return "slando"

    def get_contact(self):
        try:
            contacts = self.page.find('p', 'contacts').find('span').string

            if contacts is None:
                contacts = self.page.find('p', 'contacts').find('a').contents[0]

            return contacts
        except:
            return ""

    def get_content(self):
        arr = []

        content = self.page.find('p', 'copy').contents

        for tag in content:
            if tag.string:
                arr.append(tag.string)

        return u''.join(arr)

    def get_date(self):
        try:
            date = self.page.find('div', 'date').find('strong').string
            date = re.sub("[^\d]+", '', date, 1)
            date = unicode(date).encode('utf-8')

            for idx, month in enumerate(SlandoAdParser.MONTH):
                date = re.sub(unicode(month[0]).encode('utf-8'), month[1], date)

            return date
        except:
            return ""

    def is_agent(self):
        try:
            is_agent = self.page.find('div', 'openpanel').find('a', 'current')
            is_agent = is_agent.contents[0].strip().lower()

            return is_agent == u'квартиры от агентств'
        except:
            return ""


class AvitoAdParser(BaseAdParser):
    def get_title(self):
        return self.page.find('h1').string

    def get_name(self):
        return "avito"

    def get_contact(self):
        return self.page.find('dd', id='seller').find('strong').string

    def is_agent(self):
        try:
            user_type = self.page.find('dd', id='seller').find('span', 'grey').string
            return user_type == u"(компания)"
        except:
            return False


    def get_content(self):
        try:
            contents = self.page.find('dd', id='desc_text').contents
            return "".join([item.string or "" for item in contents])
        except:
            return ""

    def get_date(self):
        date = self.page.find('dd', itemprop='priceValidUntil')['datetime']
        date = parser.parse(date)
        date = date - relativedelta(months=2)

        return date


class OlxAdParser(BaseAdParser):
    MONTH = [[u"Январь", "Jan"], [u"Февраль", "Feb"], [u"Март", "Mar"], [u"Апрель", "Apr"], [u"Май", "May"], [u"Июнь","Jun"], [u"Июль","Jul"], [u"Август","Aug"], [u"Сентябрь", "Sept"], [u"Октябрь", "Oct"], [u"Ноябрь","Nov"], [u"Декабрь","Dec"]]

    def get_title(self):
        return self.page.find('p', id = 'olx_item_title').contents[3]

    def get_name(self):
        return "olx"

    def get_info(self, item, element = "item-data"):
        info = self.page.find('div', id = element).findAll('li')
        for i in info:
            title = i.contents[0].strip().lower()
            title = unicode(title)

            if title == item:
                return i.find('strong').string

    def get_contact(self):
        return self.get_info(u"телефон:") or ""


    def get_content(self):
        contents = self.page.find('div', id='description-text').contents

        return "".join([item.string or "" for item in contents])

    def get_date(self):
        date = self.get_info(u"дата:")
        date = unicode(date).encode('utf-8')

        for idx, month in enumerate(OlxAdParser.MONTH):
            date = re.sub(unicode(month[0]).encode('utf-8'), month[1], date)

        return date

    def is_agent(self):
        try:
            return self.get_info(u"комиссия брокера:", "item-desc") == u"Да"
        except:
            return False


class EmlsAdParser(BaseAdParser):
    def get_title(self):
        return self.page.find('h1','h1-fullinfo').string

    def get_name(self):
        return "emls"

    def get_content(self):
        tds = self.page.findAll('td')
        for td in tds:
            if td.find('td'):
                continue

            link = td.find('a')

            if link and re.search("agent", link['href']):
                return td.contents[1]

    def is_agent(self):
        return True

    def get_contact(self):
        tds = self.page.findAll('td', colspan='2')
        for td in tds:
            if td.find('strong'):
                contents = td.contents
                return "".join([item.string or "" for item in contents])

    def get_date(self):
        return ""


class IrrAdParser(BaseAdParser):
    def get_title(self):
        return self.page.find('div', 'w-title').find('b').string

    def get_name(self):
        return "irr"

    def get_content(self):
        contents = self.page.find('div', 'additional-text').find('p').contents
        return "".join([item.string or "" for item in contents])

    def is_agent(self):
        return False

    def get_contact(self):
        contents = self.page.find('div', 'contacts-info').find('li', 'ico-phone')
        return "".join([item.string or "" for item in contents])

    def get_date(self):
        timestamp = self.page.find('li', id = "ad_date_create").string
        return datetime.fromtimestamp(int(timestamp))


rAVITO = re.compile("avito.ru")
rSLANDO = re.compile("slando.spb.ru")
rOLX = re.compile("olx.ru")
rARENDA_OPEN = re.compile("arenda-open.ru")
rEMLS = re.compile("emls.ru")
rIRR = re.compile("irr.ru")

def parser_name(url):
    if rAVITO.search(url):
        return "avito"
    elif rSLANDO.search(url):
        return "slando"
    elif rOLX.search(url):
        return "olx"
    elif rARENDA_OPEN.search(url):
        return "arenda-open"
    elif rEMLS.search(url):
        return "emls"
    elif rIRR.search(url):
        return "irr"


def parse(url):
    if rAVITO.search(url):
        result = AvitoAdParser(url).parse()
    elif rSLANDO.search(url):
        result = SlandoAdParser(url).parse()
    elif rOLX.search(url):
        result = OlxAdParser(url).parse()
    elif rARENDA_OPEN.search(url):
        result = ArendaOpenAdParser(url).parse()
    elif rEMLS.search(url):
        result = EmlsAdParser(url).parse()
    elif rIRR.search(url):
        result = IrrAdParser(url).parse()

    return result



class SiteParser:
    def __init__(self, url, page_number = 1):
        self.base_url = url
        self.page_number = page_number

        self.url = self.get_paged_url()

        content = MozillaEmulator().download(self.url)

        self.page = BeautifulSoup(content)

    def parse(self):
        links = self.get_list()
        return set(links)


rRENT_LINKS = re.compile(u'(ищу квартиру|домик|домики|посуточно|часы|сут\.|садовый дом|суток|посуточная|дома|сниму|снимет|снимет|снимут|помогу|дача|дачу|гостиница|отл дом|дом на лето|сдам дом|аренда дома|коттедж|номер)')

class AvitoParser(SiteParser):
    def get_paged_url(self):
        return "%s/page%d" % (self.base_url, self.page_number)

    def get_list(self):
        ads = []
        links = self.page.find("ul", "item-table").findAll("a", itemprop="name")

        for link in links:
            if rRENT_LINKS.search(link.string.lower().strip()) is None:
                ads.append("http://www.avito.ru"+link['href'])

        return ads


class SlandoParser(SiteParser):
    rPAGE = re.compile("\d\.html$")

    def get_paged_url(self):
        return SlandoParser.rPAGE.sub("%d.html" % self.page_number, self.base_url)

    def get_list(self):
        ads = []
        links = self.page.findAll("a", "preserve_search_term")

        for link in links:
            contents = "".join([item.string or "" for item in link.contents])

            if contents and rRENT_LINKS.search(contents.lower().strip()) is None:
                ads.append(link['href'])

        return ads



class OlxParser(SiteParser):
    def get_paged_url(self):
        return self.base_url + "-p-%d" % self.page_number

    def get_list(self):
        ads = []
        links = self.page.findAll("div", "c-2")

        for link in links:
            a = link.find('a')
            if rRENT_LINKS.search(a.string.strip().lower()) is None:
                ads.append(link.find('a')['href'])

        return ads


class ArendaOpenParser(SiteParser):
    def get_paged_url(self):
        return self.base_url

    def get_list(self):
        ads = []
        links = self.page.findAll('a')

        for link in links:
            if re.search('page=company', link['href']):
                ads.append("http://arenda-open.ru%s" % link['href'])

        return ads


class EmlsMainParser(SiteParser):
    def get_paged_url(self):
        return self.base_url

    def get_list(self):
        ads = []
        links = self.page.findAll('a')

        for link in links:
            try:
                if re.search('flats', link['href']):
                    ads.append("http://www.emls.ru%s" % link['href'])
            except:
                pass

        return ads


class EmlsParser(SiteParser):
    def get_paged_url(self):
        return re.sub("flats/", "flats/page%d.html" % self.page_number, self.base_url)

    def get_list(self):
        ads = []
        links = self.page.findAll('a')

        for link in links:
            try:
                if re.search('fullinfo', link['href']):
                    ads.append("http://www.emls.ru%s" % link['href'])
            except:
                pass

        return ads


class IrrParser(SiteParser):
    def get_paged_url(self):
        return re.sub("page1", "page%d" % self.page_number, self.base_url)

    def get_list(self):
        ads = []
        links = self.page.findAll('a')

        for link in links:
            if re.search('advert/', link['href']) and rRENT_LINKS.search(link.string.lower().strip()):
               ads.append("http://www.irr.ru%s" % link['href'])

        return ads


def ads_list(url, page = 1):
    if rAVITO.search(url):
        return AvitoParser(url, page)
    elif rSLANDO.search(url):
        return SlandoParser(url, page)
    elif rOLX.search(url):
        return OlxParser(url, page)
    elif rARENDA_OPEN.search(url):
        return ArendaOpenParser(url, page)
    elif rEMLS.search(url):
        return EmlsParser(url, page)
    elif rIRR.search(url):
        return IrrParser(url, page)
