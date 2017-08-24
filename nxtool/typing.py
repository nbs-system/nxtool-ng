#-*- coding: utf-8 -*-

import re
import collections
import logging

# Each regexp is (almost) a subset of the next one
REGEXPS = [
    [r'^$', 'empty'],
    [r'^[01]$', 'boolean'],
    [r'^\d+$', 'integer'],
    [r'^#[0-9a-f]+$', 'colour'],  # '#' + hex
    [r'^[0-9a-f]+$', 'hexadecimal'],
    [r'^[0-9a-z]+$', 'alphanum'],
    [r'^[./]?([0-9a-z]/)+[\w?+-=&/ ]+$', 'relative url'],
    [r'^https?://([0-9a-z-.]+\.)+[\w?+-=&/ ]+$', 'absolute url'],  # like http://example.com?hello=1&id=3
    [r'^\w+$', 'alphanumdash'],
    [r'^[0-9a-z?&=+_-]+$', 'url parameter'],
    [r'^[\w[] ,&=+-]+$', 'array'],
    [r'^[' + r'\s\w' + r'!$%^&*()[]:;@~#?/.,' + r']+$', 'plaintext'],
    [r'', 'none'],  # untypables parameters
]

REGEXPS_URI = [r'^$', r'[01]+', r'\d+', r'[a-f]+', r'[a-z]+', r'[0-9a-f]+', r'[0-9a-z]+', r'']

def typification(source):
    # rules = {zone1: {var1:0, var2:0}, zone2: {var6:0, ...}, ...}
    rules = collections.defaultdict(lambda: collections.defaultdict(int))

    # Compile regexp for speed
    regexps = [re.compile(reg, re.IGNORECASE) for reg, _ in REGEXPS]

    for line in source.get_results():
        line = {i: line[i] for i in line}  # because `Results` objects are weird, we prefer to manipulate `dict` instead

        # naxsi inverts the var_name and the content
        # when a rule match on var_name
        if line.get('zone', 'zone0').endswith('|NAME'):
            continue
        zone = line.get('zone', 'zone0')

        var_name = line.get('var_name', '')
        if not var_name:  # No types for empty variable names
            continue

        try:
            content = line['content']
        except KeyError as e:
            logging.error('%s has no "content" (line %s): %s', var_name, line, e)
            continue

        # Bump regexps until one matches
        # Since every regexp is a subset of the next one,
        # this works great.
        while not regexps[rules[zone][var_name]].match(content):
            rules[zone][var_name] += 1

    for zone, zone_data in rules.items():
        for var_name, index in zone_data.items():
            if index < len(REGEXPS) - 1:  # Don't return untyped things
                yield [REGEXPS[index][0], REGEXPS[index][1], zone, var_name]

def regexify_uri(source, rules):
    """ This function "regexifies" the uris to print regexified rules
    :param source:
    :return:
        """

    # Compile regexp for speed
    regexps = [re.compile(reg, re.IGNORECASE) for reg in REGEXPS_URI]
    regexp_alphanum = re.compile("([0-9a-zA-Z]+)")

    def repl(mo):
        for regexp in regexps:
            if regexp.match(mo.string[mo.start():mo.end()]):
                uri_type.append(regexps.index(regexp))
                return regexp.pattern

    new_rules = list()
    for rule in rules:
        if len(rule['mz']) != 1:
            continue
        source.reset_filters()
        source.add_filters({'id': rule.get('wl', '*')})
        source.minimum_occurences = 0
        source.percentage = 0
        uris = source.get_top('uri')
        t = collections.defaultdict(list)
        for uri in uris:
            new_key = regexp_alphanum.sub("P", uri)
            t[new_key].append(uri)
        ## t is now a dict of uri for example { 'P.P': ['aaa.aaa', 'aaa.aab'] }
        sorted_t = dict()

        for key, values in t.items():
            matched_list = list()
            uri_types = list()
            uri_type = list()
            for value in values:
                ## here value are single url
                ## We check all url of the same type (key in our t dict) to find the better match
                matched_list.append(regexp_alphanum.sub(repl, value))
                uri_types.append(uri_type)

#                ## TODO use zip for that
#            crossed_list = [[item[i] for item in uri_types] for i in range(len(uri_types[0]))]
            crossed_list = zip(*uri_types)
            best_crossed_list = [max(crossed_list[i]) for i in range(len(crossed_list))]
            new_value = key
            for i in best_crossed_list:
                new_value = new_value.replace('P', REGEXPS_URI[i], 1)
                sorted_t[key] = new_value

        for key, value in sorted_t.items():
            new_rule = rule.copy()
            new_rule['mz'] = ["URL_X:{0}|{1}".format(value, rule['mz'][0])]
            new_rules.append(new_rule)

    return new_rules
