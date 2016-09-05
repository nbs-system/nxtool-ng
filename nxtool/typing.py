import re
import collections

# Each regexp is (almost) a subset of the next one
REGEXPS = [
    [r'^$', 'empty'],
    [r'^[01]$', 'boolean'],
    [r'^\d+$', 'integer'],
    [r'^#[0-9a-f]+$', 'colour'],  # '#' + hex
    [r'^[0-9a-f]+$', 'hexadecimal'],
    [r'^[0-9a-z]+$', 'alphanum'],
    [r'^https?://([0-9a-z-.]+\.)+[\w?+-=&/ ]+$', 'url'],  # like http://example.com?hello=1&id=3
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
        try:  # some events are fucked up^w^w empty
            # naxsi inverts the var_name and the content
            # when a rule match on var_name
            if line['zone'].endswith('|NAME'):
                continue
            zone = line['zone']
            content = line['content']
            var_name = line['var_name']
        except KeyError as e:
            print('Error with : {0} ({1})'.format(line, e))
            continue

        if not var_name:  # No types for empty varnames.
            continue

        # Bump regexps until one matches
        # Since every regexp is a subset of the next one,
        # this works great.
        while not regexps[rules[zone][var_name]].match(content):
            rules[zone][var_name] += 1

    for zone, zone_data in rules.items():
        for var_name, index in zone_data.items():
            if index < len(REGEXPS) - 1:  #  Don't return untyped things
                yield [REGEXPS[index][0], REGEXPS[index][1], zone, var_name]
