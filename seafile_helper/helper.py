#!/usr/bin/python
# -*- coding:Utf-8 -*-
"""\
Seafile-server and seahub helper for upgrade and deployment
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
along with this program.  If not, see <https://www.gnu.org/licenses/>.\
"""

VERSION = '0.1.4'

import os
import sys
import shutil
import glob
import argparse

from configparser import ConfigParser


class Color(object):
    """Defines a Color class object for color output
    """

    def __init__(self):
        self._colors = {
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
        return '\033[3' + self._colors[color] + string + '\033[0;0m'

    def bold(self, string, color=None):
        """Return string with bold weight color
        """
        if color:
            return '\033[1;3' + self._colors[color] + string + '\033[0;0m'
        else:
            return '\033[1m' + string + '\033[0;0m'

    def background(self, string, color):
        """Return string with background color
        """
        return '\033[4' + self._colors[color] + string + '\033[0;0m'


class UI(Color):
    """Defines an UI class derived of Color
    """

    def __init__(self):
        Color.__init__(self)

    def arrow(self, msg=''):
        """msg with arrow prefix
        """
        return self.bold('==> ', 'yellow') + self.bold(msg)

    def bullet(self, ch, msg):
        """msg with bullet prefix
        """
        brut = '{:<2} {}'.format(ch, msg)
        return brut.replace(ch, self.bold(ch, 'magenta'), 1)

    def scope(self, msg):
        """msg with scope prefix
        """
        return self.bold(':: ', 'blue') + self.bold(msg)

    def show_bullet_list(self, list_items, numbered=False):
        """Show all list elements
        """
        i = 0
        ch = '|-'
        for item in list_items:
            i += 1
            if numbered:
                ch = str(i)
            print(self.bullet(ch, item))

    def select_in_list(self, list_items, msg):
        """Show list elements
        Asks to select an element
        Return element selected
        """
        self.show_bullet_list(list_items, numbered=True)
        print(self.arrow(msg))
        try:
            reply = int(input(self.arrow()))
        except ValueError:
            sys.exit(1)
        if reply > 0 and reply <= len(list_items):
            return list_items[reply - 1]

    def msg(self, msg):
        """Write msg in stdout without endline
        """
        sys.stdout.write(msg)

    def msgerr(self, msg):
        """Print msg in stderr
        """
        print(self.bold(msg, 'red'), file=sys.stderr)


class Helper(UI):
    """Defines a Helper class derived of UI and Settings
    """

    def __init__(self, upgrade=None, locale=None, confirm=True):
        UI.__init__(self)
        self._wrkdir = os.getcwd()
        self._srvdir = os.path.join(self._wrkdir, 'seafile-server')
        self._pkgdir = '/usr/share/seafile-server'
        self._locale = locale
        self._upgrade = upgrade
        self._confirm = confirm

    def check(self):
        """Check required conditions
        """
        if not os.path.isdir(self._srvdir):
            self.msgerr('"seafile-server" not found in the current directory')
            sys.exit(1)
        if os.environ['USER'] != 'seafile':
            self.msgerr('You must use seafile user, view sudo usage')
            sys.exit(1)
        if os.path.isfile(os.path.join(self._srvdir, 'runtime/seahub.pid')):
            self.msgerr('You must stop seafile-server service')
            sys.exit(1)

    def confirm(self, msg, interactive=False):
        """Ask confirmation
        """
        if self._confirm or interactive:
            reply = input(self.scope(msg + ' [Y/n] '))
            return reply in ('Y', 'y', '')
        else:
            return True

    def prepare_server(self):
        """Prepare server
        Import runtime directory
        Remove seahub-old and old upgrade
        Backup seahub to seahub-old
        Import seahub and upgrades
        """
    # Import runtime directory
        self.msg('-> Import runtime... ')
        try:
            shutil.copytree(
                os.path.join(self._pkgdir, 'runtime'),
                os.path.join(self._srvdir, 'runtime'))
        except FileExistsError:
            self.msg('Already exist\n')
        else:
            self.msg('Done\n')
    # Remove old backup
        for dire in ('upgrade', 'seahub-old'):
            self.msg('-> Remove {}... '.format(dire))
            try:
                shutil.rmtree(
                    os.path.join(self._srvdir, dire))
            except FileNotFoundError:
                self.msg('Not exist\n')
            else:
                self.msg('Done\n')
    # Seahub Backup
        self.msg('-> Backup seahub to seahub-old... ')
        try:
            shutil.move(
                os.path.join(self._srvdir, 'seahub'),
                os.path.join(self._srvdir, 'seahub-old'))
        except FileNotFoundError:
            self.msg('Not exist\n')
        else:
            self.msg('Done\n')
    # Import new files
        self.msg('-> Import scripts upgrade... ')
        shutil.copytree(
            os.path.join(self._pkgdir, 'upgrade'),
            os.path.join(self._srvdir, 'upgrade'))
        self.msg('Done\n')
        self.msg('-> Import seahub... ')
        shutil.copytree(
            os.path.join(self._pkgdir, 'seahub'),
            os.path.join(self._srvdir, 'seahub'))
        self.msg('Done\n')

    def get_locales_available(self):
        """Return list of locales available
        """
        os.chdir(os.path.join(self._pkgdir, 'seahub/locale'))
        return sorted(next(os.walk('.'))[1])

    def get_upgrades_available(self):
        """Return list of upgrades available
        """
        os.chdir(os.path.join(self._pkgdir, 'upgrade'))
        return sorted(glob.glob('*upgrade*.sh'))

    def show_locales(self):
        """Show locales available
        """
        self.show_bullet_list(self.get_locales_available())

    def show_upgrades(self):
        """Show upgrades available
        """
        self.show_bullet_list(self.get_upgrades_available())

    def set_locale_selected(self):
        """Defines __locale attribut with locale selected
        """
        self._locale = self.select_in_list(
            self.get_locales_available(),
            'Select a locale (ex: 1)'
        )

    def set_upgrade_selected(self):
        """Defines __upgrade attribut with upgrade selected
        """
        self._upgrade = self.select_in_list(
            self.get_upgrades_available(),
            'Select an upgrade (ex: 1)'
        )

    def compile_locale(self):
        """Compile seahub locale with __locale attribut
        """
        if self.confirm('Compile "{}" locale ?'.format(self._locale)):
            self.msg('-> Compile seahub locale... ')
            try:
                os.chdir(os.path.join(
                    self._srvdir, 'seahub/locale',
                    self._locale, 'LC_MESSAGES'))
            except FileNotFoundError:
                self.msgerr('"' + self._locale + '" locale is not available')
            else:
                os.system('msgfmt -o django.mo django.po')
                self.msg('Done\n')

    def run_upgrade(self):
        """Run __upgrade attribut as script
        """
        os.chdir(os.path.join(self._srvdir, 'upgrade'))
        if self.confirm('Run "{}" ?'.format(self._upgrade)):
            os.system('./' + self._upgrade)

    def interactive(self):
        """Interactive upgrade of seahub
        """
        self.check()
        if self.confirm('Prepares seafile-server\'s instance ?', True):
            self.prepare_server()
        if self.confirm('Select a script upgrade ?', True):
            self.set_upgrade_selected()
            self.run_upgrade()


def main():
    """For run helper in the console
    """
    def show_version():
        """Show version and license
        """
        print(os.path.basename(sys.argv[0]) + ' version ' + VERSION)
        print(__doc__)
        sys.exit(0)

    def call_funcs(dict_args, dict_funcs):
        """Call functions
        Requiere dictionnary arguments
        """
        for key in dict_args.keys():
            if dict_args[key]:
                try:
                    dict_funcs[key]()
                except KeyError:
                    continue

    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--show-locales', action='store_true',
                        help='show locales available')
    parser.add_argument('-u', '--show-upgrades', action='store_true',
                        help='show upgrades scripts available')
    parser.add_argument('-p', '--prepare', action='store_true',
                        help='prepare seafile-server for upgrade or deploying')
    parser.add_argument('-L', '--locale', type=str,
                        help='compile locale')
    parser.add_argument('-U', '--upgrade', type=str,
                        help='run script upgrade')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='ask confirmation')
    parser.add_argument('-V', '--version', action='store_true',
                        help='show version information and exit')
    args = parser.parse_args()

    helper = Helper(args.upgrade, args.locale, args.interactive)

    try:
        if len(sys.argv) == 1:
            helper.interactive()
        elif args.show_locales or args.show_upgrades or args.version:
            funcs = {
                'show_locales': helper.show_locales,
                'show_upgrades': helper.show_upgrades,
                'version': show_version,
            }
            call_funcs(args.__dict__, funcs)
        else:
            helper.check()
            funcs = {
                'prepare': helper.prepare_server,
                'locale': helper.compile_locale,
                'upgrade': helper.run_upgrade,
            }
            call_funcs(args.__dict__, funcs)
    except KeyboardInterrupt:
        sys.stdout.write('\n')
        sys.exit(130)


if __name__ == '__main__':
    main()
