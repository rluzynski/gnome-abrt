## Copyright (C) 2012 ABRT team <abrt-devel-list@redhat.com>
## Copyright (C) 2001-2005 Red Hat, Inc.

## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.

## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 51 Franklin Street, Suite 500, Boston, MA  02110-1335  USA

import collections
import logging

# libreport
import report

def singleton(cls):
    """
    http://www.python.org/dev/peps/pep-0318/#examples
    """
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance

@singleton
class Configuration(object):

    def __init__(self):
        self.options = {}
        self.app_conf_files = collections.defaultdict(list)

    def set_watch(self, option, observer):
        self.options[option].observers.append(observer)

    def __getitem__(self, option):
        return self.options[option].value

    def _update_option(self, option_name, option, value):
        if option.value != value:
            option.value = value
            logging.debug("Updating option: {0}".format(option_name))
            for observer in option.observers:
                observer.option_updated(self, option_name)

    def __setitem__(self, option, value):
        self._update_option(option, self.options[option], value)

    def __delitem__(self, option):
        pass

    def __len__(self):
        return len(self.options)

    def get_option_value(self, option, default):
        if option in self.options:
            return self.options[option].value
        return default

    def add_option(self, short_key,
            long_key=None, description=None, default_value=None):

        if short_key in self.options:
            raise KeyError("The option already exists")

        option = collections.namedtuple('Option',
                'long_key description value observers')

        option.long_key = long_key
        option.description = description
        option.value = default_value
        option.observers = []

        self.options[short_key] = option
        return option

    def _reload_app_conf(self, app_name, options):
        logging.debug("Reloading configuration file: {0}".format(app_name))

        app = None
        try:
            app = report.load_app_conf_file(app_name)
        except OSError as ex:
            logging.debug("'{0}' conf file not loaded: {1}"
              .format(app_name, ex.message))
            return

        for opt in (opt for opt in options if opt.long_key in app):
            self._update_option(opt.long_key, opt, app[opt.long_key])

    def add_option_from_app_conf_file(self, app_name,
            option_name=None, default_value=None):
        """
        Raises KeyError if option already exists
        """

        option = self.add_option(option_name,
                option_name, None, default_value)

        self.app_conf_files[app_name].append(option)
        self._reload_app_conf(app_name, [option])

    def reaload_app_conf_files(self):
        logging.debug("Reloading all configuration files")
        for app_name, options in self.app_conf_files.iteritems():
            self._reload_app_conf(app_name, options)

    def get_as_bool(self, short_key):
        opt_val = self[short_key]
        return opt_val and opt_val.lower() in ["yes", "on", "1"]


def get_configuration():
    return Configuration()
