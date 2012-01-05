phone_formats = [
    "7%s%s%s%s%s%s%s%s%s%s",
    "8%s%s%s%s%s%s%s%s%s%s",
    "%s%s%s-%s%s%s-%s%s-%s%s",
    "%s%s%s-%s%s-%s%s-%s%s%s",
    "8%s%s%s-%s%s%s-%s%s-%s%s",
    "7%s%s%s-%s%s-%s%s-%s%s%s",
    "8%s%s%s-%s%s%s%s%s%s%s"]

def format_phone(phone):
    query = []

    for p_format in phone_formats:
        f_phone = p_format % tuple(phone)

        query.append('"%s"' % f_phone)

    return " OR ".join(query)

print format_phone("9219840091")
