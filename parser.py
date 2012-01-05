# encoding: utf-8
import adsparser
import time
from BeautifulSoup import BeautifulSoup
import urllib2
import re

urls = ["http://nedvizhimost.slando.spb.ru/sankt-peterburg/sdam-2h-komnatnuyu-kvartiru-u-metro_P_34026130.html",
        "http://nedvizhimost.slando.spb.ru/sankt-peterburg/sdam-1-k-kv-metro-primorskaya_P_34045468.html",
        "http://www.avito.ru/items/sankt-peterburg_kvartiry_kvartira_na_akademke_26817388"]
"""
#ArendaPiter parser

urls = []
content = adsparser.MozillaEmulator().download("http://arenda-piter.ru/firmi.php")
page = BeautifulSoup(content)
links = page.findAll('a')
for link in links:
    if link.has_key('href') and re.search(u'firmaone', link['href']):
        urls.append(link['href'])

urls = set(urls)

arr = []

for url in urls:
    content = adsparser.MozillaEmulator().download(url)
    page = BeautifulSoup(content)

    table = page.find('table', 'tarif_tbl')
    table = str(table)

    phone_match = adsparser.rPHONE.findall(table, re.M)

    phones = [adsparser.format_phone(phone) for phone in phone_match]

    arr.append(" ".join(phones))

print " ".join(arr)

exit()
"""



#print avtoru_parser.AvtoruAdParser("http://cars.auto.ru/cars/used/sale/11458490-f214.html").parse()
#exit();

#print adsparser.parse("http://nedvizhimost.slando.ru/moskva/srochno-snimu-2-h-komnatnuyu-kvartiru_P_38854056.html", 'msk')
#exit()

#urls = adsparser.ads_list("http://nedvizhimost.slando.ru/moskva/1377_1.html").parse()
#urls = adsparser.ads_list("http://www.novoebenevo.ru/sdam/area_3").parse()
urls = adsparser.ads_list("http://nedvizhimost.slando.ru/moskva/1376_T2_1.html").parse()

for url in urls:
    print adsparser.parse(url, 'msk')

exit()

"""
#ArendaOpen parser
phones = []
for url in urls:
    page = BeautifulSoup(urllib2.urlopen(url))
    bs = page.findAll('b')
    for b in bs:
        try:
            phone = adsparser.rPHONE.search(b.string)
            if phone:
                phones.append(adsparser.format_phone(phone.group(0)))
        except:
            pass

print " ".join(phones)
"""
"""
#AdendaPiter parser

"""

#print adsparser.parse("http://saintpetersburg.olx.ru/iid-181729853")

exit()

for url in urls:
    print url
    print adsparser.parse(url)

    time.sleep(2)
