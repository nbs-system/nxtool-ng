# Example of NAXSI_FMT:
# 2013/11/10 07:36:19 [error] 8278#0: *5932 NAXSI_FMT: ip=X.X.X.X&server=Y.Y.Y.Y&uri=/phpMyAdmin-2.8.2/scripts/setup.php&learning=0&vers=0.52&total_processed=472&total_blocked=204&block=0&cscore0=$UWA&score0=8&zone0=HEADERS&id0=42000227&var_name0=user-agent, client: X.X.X.X, server: blog.memze.ro, request: "GET /phpMyAdmin-2.8.2/scripts/setup.php HTTP/1.1", host: "X.X.X.X"

try:
    from urlparse import parse_qs
except ImportError:  # python3
    from urllib.parse import parse_qs
import logging
import dateutil
import itertools


def parse_log(line):
    for separator in {'[error]', '[debug]'}:
        end_of_date = line.find(separator)
        if end_of_date != -1:
            break
    else:
        logging.error('Unable to find [error] or [debug] in the line. Something is wrong with your log.')
        return None

    date = dateutil.parser.parse(line[:end_of_date])

    for keyword in {" NAXSI_FMT: ", " NAXSI_EXLOG: "}:
        start_of_query = line.find(keyword)
        if start_of_query != -1:
            end = line.find(', client:')
            end = end if end != -1 else len(line)
            data = line[start_of_query + len(keyword):end]
            break
    else:
        logging.error('Unable to find NAXSI_EXLOG: or NAXSI_FMT: in the line. Something is wrong with your log.')
        return None

    parsed_data = parse_qs(data)
    parsed_data = {k:v[0] for k,v in parsed_data.items()}  # parse_qs is returning a dict of list, flatten it!

    if 'zone0' in parsed_data:
        for cpt in itertools.count():
            has_zone = 'zone%d' % cpt in parsed_data
            has_id = 'id%d' % cpt in parsed_data

            if has_zone and has_id:
                continue
            elif not (has_zone or has_id):
                break
            else:
                logging.error('You have unmatching id and zone. Something is wrong with your log.')
                return None

    return date, parsed_data

