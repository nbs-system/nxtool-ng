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

REGEXPS_URI = [
    [r'^$', 'empty'],
    [r'^[01]$', 'boolean'],
    [r'^\d+$', 'integer'],
    [r'^[a-z]+$', 'string'],
    [r'^[0-9a-f]+$', 'hexadecimal'],
    [r'^[0-9a-z]+$', 'alphanum'],
    [r'', 'none'],  # untypables parameters
]

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
    regexps = [re.compile(reg, re.IGNORECASE) for reg, _ in REGEXPS_URI]
    regexp_alphanum = re.compile("([0-9a-zA-Z]+)")

    def repl(mo):
        for regexp in regexps:
            if regexp.match(mo.string[mo.start():mo.end()]):
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
        for key in uris:
            new_key = regexp_alphanum.sub("P", key)
            t[new_key].append(regexp_alphanum.sub(repl, key))
        ## We might be in a case where a regex matched on a degenerated case
        ## For example one instance of alphanumeric string without [g-z] matching the hexa case
        ## We try to sort this out
        for key, value in t.items():
            if len(t[key]) > 1:
                for i in t[key]:
                    for regexp in REGEXPS_URI:
                        index = 0
                        if i in regexp:
                            if REGEXPS_URI[regexp] > index and index not in [3, 4]:
                                ## We have to disinguish between hexa and alphnum separatly
                                index = REGEXPS_URI.index(regexp)
            t[key] = REGEXPS_URI[index]
            ## We can now be in the case of problem distinguishing between hexa and alphanum

        print "New T"
        for key, value in t.items():
            print("{}: {}".format(key, value))
        for key, value in t.items():
            new_rule = rule.copy()
            new_rule['mz'] = ["URL_X:{0}|{1}".format(value[0], rule['mz'][0])]
            new_rules.append(new_rule)

    return new_rules
