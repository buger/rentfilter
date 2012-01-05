import urllib2
import re

url = "http://www.incom-realty.ru/offices/"

rPHONE = re.compile("(?:\d[ \-\)\(\dx\.]{0,2}(?!\n)){6,12}")
rMOBILE_PHONE = re.compile("9(?:\d[ \-\)\(\dx\.]{0,2}){6,12}")
rREPLACE = re.compile("\D")
rCITY_PREFIX = re.compile("^(812|813|811|495|499)")
rPHONE_PREFIX = re.compile("^[87]")


def format_phone(phone, remove_prefix = False):
    phone = rREPLACE.sub('', phone)

    if len(phone) >= 9 and rPHONE_PREFIX.match(phone):
        phone = rPHONE_PREFIX.sub('', phone)

    phone = re.sub("^0", '', phone)

    if remove_prefix:
        phone = rCITY_PREFIX.sub('', phone)

    return phone


def get_phones(url):
    f = urllib2.urlopen(url)
    content = f.read()

    phones = []

    matches = re.finditer(rPHONE, content)

    for match in matches:
        phones.append(format_phone(match.group(0)))

    phones = filter(lambda p: p[0:3] == '495' or p[0:3] == '499', phones)
    phones = [rCITY_PREFIX.sub("", phone) for phone in phones]

    return phones

arr = []

from subprocess import call

for i in range(25,38):
    print "page %d" % i

    url = "http://www.moscowmap.ru/sprav2/search.asp?rub_id=690&page=%d" % i

    f = urllib2.urlopen(url)
    content = f.read()

    rCONTACT = re.compile("showkont\.asp\?id=(\d+)")

    matches = re.finditer(rCONTACT, content)

    for match in matches:
        url = "http://www.moscowmap.ru/sprav2/showkont.asp?id=%s" % match.group(1)

        phones = " ".join(get_phones(url))

        call("echo \"%s \" >> phones.txt" % phones, shell=True)
