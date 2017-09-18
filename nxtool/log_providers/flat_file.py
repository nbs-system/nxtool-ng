import collections
import fileinput
import mimetypes
import zipfile
import tarfile
import re
import logging

from nxapi.nxlog import parse_nxlog

from nxtool.log_providers import LogProvider


class FlatFile(LogProvider):
    def __init__(self, fname=None):
        super(LogProvider, self)

        self.minimum_occurrences = 250
        self.percentage = 10
        self.logs = list()
        self.filters = collections.defaultdict(list)
        self.negative_filters = collections.defaultdict(list)
        self.filters_regexp = collections.defaultdict(list)
        self.negative_filters_regexp = collections.defaultdict(list)
        self.fname = fname

        try:
            ftype = mimetypes.guess_all_extensions(self.fname)[0]
        except AttributeError:  # `self.fname` is None
            self.__transform_logs(fileinput.input("-"))
        except IndexError:  # `self.fname` has no guessable mimtype
            self.__transform_logs(fileinput.input(self.fname))
        else:
            if ftype == 'application/zip':  # zip file!
                with zipfile.ZipFile(self.fname) as f:
                    for name in f.namelist():
                        self.__transform_logs(f.read(name))
            elif ftype == 'application/tar':  # tar file!
                with tarfile.open(self.fname) as f:
                    for name in f.namelist():
                        self.__transform_logs(f.read(name))

    def export_search(self):
        return self.filters, self.negative_filters, self.filters_regexp, self.negative_filters_regexp

    def import_search(self, search):
        self.filters, self.negative_filters, self.filters_regexp, self.negative_filters_regexp = search

    def __transform_logs(self, it):
        for line in it:
            error, log = parse_nxlog(line)
            if error:
                logging.error('%s while parsing %s', error, line)
            if log:
                self.logs.extend(log)

    def get_top(self, field, size=250):
        ret = dict()
        values = (log[field] for log in self.__get_filtered_logs())
        for key, value in collections.Counter(values).most_common(10):
            ret[key] = value
        return ret

    def __get_filtered_logs(self):
        """
        yield the loglines accordingly to the filtering policy defined in `self.filters`
        """
        if not any((self.filters, self.filters_regexp, self.negative_filters_regexp, self.negative_filters)):
            for log in self.logs:  # we don't filter, give everything!
                yield log
        else:
            for log in self.logs:
                for key, value in log.items():
                    if key in self.filters:  # are we filtering on this `key`?
                        if value in self.filters[key] and value != '*':  # is the current `value` in the filtering list?
                            if key not in self.negative_filters:  # are we filtering on this particular `key`?
                                if value not in self.negative_filters[key] and value != '*':
                                    yield log
                    if key in self.filters_regexp:  # are we filtering on this `key`?
                        if re.match(self.filters_regexp[key], value):  # is the current `value` in the filtering list?
                            if key not in self.negative_filters_regexp:  # are we filtering on this particular `key`?
                                if not re.match(self.negative_filters_regexp[key], value):
                                    yield log

    def get_results(self):
        return self.__get_filtered_logs()

    def add_filters(self, filters, regexp=False, negative=False):  # TODO: simplify this shit
        for key, value in filters.items():
            if negative is True:
                if isinstance(value, list):
                    if regexp is True:
                        self.negative_filters_regexp[key].extend(value)
                    else:
                        self.negative_filters[key].extend(value)
                else:
                    if regexp is True:
                        self.negative_filters_regexp[key].append(value)
                    else:
                        self.negative_filters[key].append(value)
            else:
                if isinstance(value, list):
                    if regexp is True:
                        self.filters_regexp[key].extend(value)
                    else:
                        self.filters[key].extend(value)
                else:
                    if regexp is True:
                        self.filters_regexp[key].append(value)
                    else:
                        self.filters[key].append(value)

    def get_relevant_ids(self, fields, percentage=0, minimum_occurrences=0):
        """
         We want to keep alerts that are spread over a vast number of different`fields`

            To measure the spreading, we're using this metric: https://en.wikipedia.org/wiki/Coefficient_of_variation
        :param list of str fields:
        :return:
        """
        minimum_occurences = minimum_occurrences or self.minimum_occurrences
        percentage = percentage or self.percentage
        
        id_blacklist = set()
        ret = set()
        for field in fields:
            stats = collections.defaultdict(int)
            size = 0
            for logline in self.get_results():
                if logline['id'] not in id_blacklist:
                    stats[logline['id']] += 1
                size += 1

            for k, v in stats.items():
                if size < minimum_occurrences:
                    logging.debug('The field %s has not enough occurrences (%d): non-significant', field, size)
                    continue
                if v < size / percentage:
                    logging.debug('The id %s is present in less than 10%% (%d) of %s : non-significant.', k, v, field)
                    id_blacklist.add(k)
                else:
                    ret.add(k)

        return list(map(int, ret))
