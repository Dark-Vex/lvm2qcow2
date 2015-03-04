#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2014 Luca Giovenzana <luca@giovenzana.org>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import subprocess
from argparse import ArgumentParser

__author__ = "Luca Giovenzana <luca@giovenzana.org>"
__date__ = "2015-02-28"
__version__ = "0.1dev"


class Device():
    def __init__(self, path):
        # TODO test exists
        # TODO test is a block device
        # TODO consider try catch
        # get path, vg, lv and size from lvdisplay
        out = subprocess.check_output(['sudo', 'lvdisplay', path])
        lv_display = re.findall('LV Path\s+(.+)\s+'
                                'LV Name\s+(.+)\s+'
                                'VG Name\s+(.+)', out)
        lv_size = re.findall('LV Size\s+(.+)', out)
        self.path = lv_display[0][0]
        self.lv = lv_display[0][1]
        self.vg = lv_display[0][2]
        self.size = lv_size[0]

    def create_snapshot(self, name, size):
        # TODO test whether there is enough space
        pass
        #

    def list_snapshot(self, pattern):
        pass

    def delete_snapshot(self, name):
        # check if not used
        pass
        # delete the snapshot


def main():

    parser = ArgumentParser()
    parser.add_argument("-s", "--source",
                        action='store', dest='SOURCE',
                        help="source logical volume device that you want to "
                             "snapshot and backup", required=True)

    parser.add_argument("-d", "--destination",
                        action='store', dest='DESTINATION',
                        help="destination path where the script saves "
                             "the qcow2", required=True)

    parser.add_argument("-q", "--qcow2",
                        action='store', dest='IMAGE',
                        help="destination filename for the backup qcow2 image")

    parser.add_argument("-s", "--snapshot-size",
                        action='store', dest='SIZE', type=int,
                        help="")

    parser.add_argument('--version', action='version',
                        version="%(prog)s {}".format(__version__))

    args = parser.parse_args()

    # Check vg
    # Check lv
    # Check destination isdir
    # Check pending snapshots
    # Check space left in the vg
    # Snapshot lv
    # Check number of backups
    # Do qemu-img copy

    return 0

if __name__ == '__main__':
    main()
