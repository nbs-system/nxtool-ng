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
    ['r^[./]?([0-9a-z]/)+[\w?+-=&/ ]+$', 'relative url'],
    [r'^https?://([0-9a-z-.]+\.)+[\w?+-=&/ ]+$', 'absolute url'],  # like http://example.com?hello=1&id=3
    [r'^\w+$', 'alphanumdash'],
    [r'^[0-9a-z?&=+_-]+$', 'url parameter'],
    [r'^[\w[] ,&=+-]+$', 'array'],
    [r'^[' + r'\s\w' + r'!$%^&*()[]:;@~#?/.,' + r']+$', 'plaintext'],
    [r'', 'none'],  # untypables parameters
]


def typification(source):
    # rules = {zone1: {var1:0, var2:0}, zone2: {var6:0, ...}, ...}
    rules = collections.defaultdict(lambda: collections.defaultdict(int))

    # Compile regexp for speed
    regexps = [re.compile(reg, re.IGNORECASE) for reg, _ in REGEXPS]

    for line in source.get_results():
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
