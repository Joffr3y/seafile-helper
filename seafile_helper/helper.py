#!/usr/bin/python
# -*- coding:Utf-8 -*-
"""Seafile-server and seahub helper for upgrade and deployment
Copyright (C) 2018 Joffrey Darcq

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

VERSION = '0.1'

import os
import sys
import shutil
import glob
import argparse


class Color(object):
    """Defines a Color class object for color stdout
    """
    def __init__(self, activate=True):
        """activate=False deactivate the coloring
        """
        self.__activate = activate
        self.__colors = {
            'black': '0m',
            'red': '1m',
            'green': '2m',
            'yellow': '3m',
            'blue': '4m',
            'magenta': '5m',
            'cyan': '6m',
            'white': '7m',
        }

    def color(self, string, color):
        """Return string with light weight color
        """
        if self.__activate:
            return '\033[3' + self.__colors[color] + string + '\033[0;0m'
        else:
            return string

    def bold(self, string, color=None):
        """Return string with bold weight color
        """
        if self.__activate:
            if color:
                return '\033[1;3' + self.__colors[color] + string + '\033[0;0m'
            else:
                return '\033[1m' + string + '\033[0;0m'
        else:
            return string

    def background(self, string, color):
        """Return string with background color
        """
        if self.__activate:
            return '\033[4' + self.__colors[color] + string + '\033[0;0m'
        else:
            return string


class Helper(Color):
    """Defines a Helper derived of Color class
    """
    def __init__(self,
        upgrade=None,
        locale=None,
        verbose=True,
        confirm=True,
        color=True):

        Color.__init__(self, color)
        self.__wkdir = os.getcwd()
        self.__pkgdir = '/usr/share/seafile-server'
        self.__locale = locale
        self.__verbose = verbose
        self.__upgrade = upgrade
        self.__confirm = confirm

    def get_locales_available(self):
        """Return list of locales available
        """
        os.chdir(os.path.join(self.__pkgdir, 'seahub/locale'))
        return sorted(next(os.walk('.'))[1])

    def get_upgrades_available(self):
        """Return list of upgrades available
        """
        os.chdir(os.path.join(self.__pkgdir, 'scripts', 'upgrade'))
        return sorted(glob.glob('*upgrade*.sh'))

    def check(self):
        """Check required conditions
        """
        if os.path.basename(self.__wkdir) != 'seafile-server':
            sys.exit('You must be in /YourInstance/seafile-server/')
        if os.environ['USER'] != 'seafile':
            sys.exit('You must use seafile user, view « sudo usage »')
        if os.path.isfile(os.path.join(self.__wkdir, 'runtime', 'seahub.pid')):
            sys.exit('You must stop seafile-server service')

    def verbose(self, msg):
        """Write in stdout
        """
        if self.__verbose:
            sys.stdout.write(msg)

    def confirm(self, msg):
        """Ask confirmation
        """
        if self.__confirm:
            ask = self.bold(':: ', 'blue') + self.bold(msg + ' [y/N] ')
            reply = input(ask)
            return reply == 'y' or reply == 'Y'
        else:
            return True

    def prepare_upgrade(self):
        """Prepare upgrade
        Import requierements
        Remove seahub-old and old upgrade
        Backup seahub to seahub-old
        Import seahub and upgrades
        """
        ## Requierements
        self.verbose('-> Import runtime content... ')
        try:
            os.mkdir('runtime', 0o755)
        except FileExistsError:
            self.verbose('Already exist\n')
        else:
            shutil.copy2(
                os.path.join(self.__pkgdir, 'scripts', 'seahub.conf'),
                os.path.join(self.__wkdir, 'runtime', 'seahub.conf'))
            self.verbose('Done\n')
        ## Remove
        for dire in ('upgrade', 'seahub-old'):
            self.verbose('-> Remove {}... '.format(dire))
            try:
                shutil.rmtree(
                    os.path.join(self.__wkdir, dire))
            except FileNotFoundError:
                self.verbose('Not exist\n')
            else:
                self.verbose('Done\n')
        ## Backup
        self.verbose('-> Backup seahub to seahub-old... ')
        try:
            shutil.move(
                os.path.join(self.__wkdir, 'seahub'),
                os.path.join(self.__wkdir, 'seahub-old'))
        except FileNotFoundError:
            self.verbose('Not exist\n')
        else:
            self.verbose('Done\n')
        ## Import
        self.verbose('-> Import scripts upgrade... ')
        shutil.copytree(
            os.path.join(self.__pkgdir, 'scripts', 'upgrade'),
            os.path.join(self.__wkdir, 'upgrade'))
        self.verbose('Done\n')
        self.verbose('-> Import seahub... ')
        shutil.copytree(
            os.path.join(self.__pkgdir, 'seahub'),
            os.path.join(self.__wkdir, 'seahub'))
        self.verbose('Done\n')

    def show(self, list_items, numbered=False):
        """Show all list elements in stdout
        """
        i = 0
        bullet = '|-'
        for item in list_items:
            i += 1
            if numbered:
                bullet = str(i)
            bullet_list = '{0:<2} {1}'.format(bullet, item)
            print(bullet_list.replace(bullet, self.bold(bullet, 'magenta'), 1))

    def show_locales(self):
        """Show locales available in stdout
        """
        self.show(self.get_locales_available())

    def show_upgrades(self):
        """Show upgrades available in stdout
        """
        self.show(self.get_upgrades_available())

    def select(self, list_items, msg):
        """Show list elements
        Asks to select an element
        Return element selected
        """
        self.show(list_items, numbered=True)
        arrow = self.bold('==> ', 'yellow')
        print(arrow + self.bold(msg))
        try:
            reply = int(input(arrow))
        except ValueError:
            sys.exit(1)
        if reply > 0 and reply <= len(list_items):
            return list_items[reply - 1]

    def set_locale_selected(self):
        """Defines __locale attribut with locale selected
        """
        locales = self.get_locales_available()
        self.__locale = self.select(locales, 'Select a locale (ex: 1)')

    def set_upgrade_selected(self):
        """Defines __upgrade attribut with upgrade selected
        """
        upgrades = self.get_upgrades_available()
        self.__upgrade = self.select(upgrades, 'Select an upgrade (ex: 1)')

    def configure_locale(self):
        """Configure seahub locale with __locale attribut
        """
        if self.confirm('Use "{}" as locale ?'.format(self.__locale)):
            self.verbose('-> Configure seahub locale... ')
            try:
                os.chdir(os.path.join(
                    self.__wkdir, 'seahub/locale',
                    self.__locale, 'LC_MESSAGES'))
            except FileNotFoundError:
                print('ignored "{}" not available'.format(self.__locale))
            else:
                os.system('msgfmt -o django.mo django.po')
                os.chdir(self.__wkdir)
                self.verbose('Done\n')

    def run_upgrade(self):
        """Run __upgrade attribut as script
        """
        os.chdir(os.path.join(self.__wkdir, 'upgrade'))
        if self.confirm('Run "{}" ?'.format(self.__upgrade)):
            os.system('./' + self.__upgrade)

    def interactive(self):
        """Interactive upgrade of seahub
        """
        self.check()
        if self.confirm('Prepares seafile-server\'s instance ?'):
            self.prepare_upgrade()
        if self.confirm('Select a seahub locale ?'):
            self.set_locale_selected()
            self.configure_locale()
        if self.confirm('Select a script upgrade ?'):
            self.set_upgrade_selected()
            self.run_upgrade()


def main():
    """For run helper in the console
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-L', '--show-locales', action='store_true',
        help='show locales available')
    parser.add_argument('-U', '--show-upgrades', action='store_true',
        help='show upgrades scripts available')
    parser.add_argument('-i', '--interactive', action='store_true',
        help='run in interactive mode')
    parser.add_argument('-p', '--prepare', action='store_true',
        help='prepare seafile-server for upgrade or deploying')
    parser.add_argument('-l', '--locale', type=str,
        help='configure locale')
    parser.add_argument('-u', '--upgrade', type=str,
        help='run script upgrade')
    parser.add_argument('--about', action='store_true')
    parser.add_argument('--no-verbose', action='store_false')
    parser.add_argument('--no-confirm', action='store_false')
    parser.add_argument('--no-color', action='store_false')
    args = parser.parse_args()

    def call_funcs(dict_args, dict_funcs):
        """Call functions
        Requiere dictionnary arguments
        """
        for key in dict_args.keys():
            if dict_args[key]:
                try:
                    dict_funcs[key]()
                except KeyError:
                    pass

    helper = Helper(args.upgrade,
                    args.locale,
                    args.no_verbose,
                    args.no_confirm,
                    args.no_color)
    scriptname = os.path.basename(sys.argv[0])
    try:
        if len(sys.argv) == 1:
            sys.exit('Argument missing, view « {} --help »'.format(scriptname))
        elif args.interactive:
            helper.interactive()
        elif args.about:
            print(scriptname + ' version ' + VERSION)
            print(__doc__)
        elif args.show_locales or args.show_upgrades:
            funcs = {
                'show_locales': helper.show_locales,
                'show_upgrades': helper.show_upgrades,
            }
            call_funcs(args.__dict__, funcs)
        else:
            funcs = {
                'prepare': helper.prepare_upgrade,
                'locale': helper.configure_locale,
                'upgrade': helper.run_upgrade,
            }
            helper.check()
            call_funcs(args.__dict__, funcs)
    except KeyboardInterrupt:
        sys.exit('')

if __name__ == '__main__':
    main()