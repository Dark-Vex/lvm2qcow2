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

import os
import re
import sys
import time
import glob
import subprocess
from argparse import ArgumentParser

__author__ = "Luca Giovenzana <luca@giovenzana.org>"
__date__ = "2015-02-28"
__version__ = "0.1dev"


class Device():

    def __init__(self, path):
        # get path, vg, lv and size from lvdisplay
        try:
            out = subprocess.check_output(['lvdisplay', path])
        except subprocess.CalledProcessError as e:
            print e.cmd
            print e.output
            sys.exit(1)
        except OSError as e:
            print "OSError: lvdisplay command not found"
            sys.exit(1)
        else:
            lv_display = re.findall('LV Path\s+(.+)\s+'
                                    'LV Name\s+(.+)\s+'
                                    'VG Name\s+(.+)', out)
            lv_size = re.findall('LV Size\s+(.+)', out)
            self.path = lv_display[0][0]
            self.lv = lv_display[0][1]
            self.vg = lv_display[0][2]
            self.size = lv_size[0]

    def __str__(self):
        return ("LV Path: {}\n"
                "LV Name: {}\n"
                "VG Name: {}\n"
                "LV Size: {}".format(self.path, self.lv, self.vg, self.size))

    def create_snapshot(self, name=None, snapshot_size='5g'):
        if name is None:
            snapshot_name = '{}-lvm2qcow2-snapshot'.format(self.lv)
        cmd_args = '-s {} -n {} -L {}'.format(self.path, snapshot_name,
                                              snapshot_size)
        try:
            subprocess.check_output(['lvcreate'] + cmd_args.split())
        except subprocess.CalledProcessError as e:
            print e.cmd
            print e.output
            sys.exit(1)
        except OSError as e:
            print "OSError: lvcreate command not found"
            sys.exit(1)
        else:
            snapshot_name = os.path.join(os.path.dirname(self.path),
                                         snapshot_name)
            return snapshot_name

    def delete_snapshot(self, name=None):
        # check if not used
        if name is None:
            name = '{}-lvm2qcow2-snapshot'.format(self.lv)
        # adding the full path
        snapshot_name = os.path.join(os.path.dirname(self.path), name)
        try:
            subprocess.check_output(['lvremove', '-f'] + snapshot_name.split())
        except subprocess.CalledProcessError as e:
            print e.cmd
            print e.output
            sys.exit(1)
        except OSError as e:
            print "OSError: lvremove command not found"
            sys.exit(1)
        else:
            return snapshot_name


class Images():
    def __init__(self, path, prefix, suffix='.qcow2'):
        self.files = [os.path.abspath(i) for i in glob.glob(os.path.join(path,
                      '{}*{}'.format(prefix, suffix)))]
        self.files = sorted(self.files, reverse=True)

    def keep_only(self, copies):
        # TODO delete also md5sum file
        while len(self.files) > copies:
            try:
                subprocess.check_output(['rm'] + self.files.pop().split())
            except subprocess.CalledProcessError as e:
                print e.cmd
                print e.output
                sys.exit(1)

    def __iter__(self):
        return self.files.__iter__()


def _qemu_img_cmd(source, destination, image):
    """ Run qemu-img command to convert lv to qcow2:
    qemu-img convert -c -O qcow2 SOURCE DESTINATION/IMAGE"""
    destination = os.path.join(destination, image)
    # FIXME remove .split find better way to preserve spaces in arguments
    cmd_args = 'convert -c -O qcow2 {} {}'.format(source, destination)
    try:
        subprocess.check_output(['qemu-img'] + cmd_args.split())
    except subprocess.CalledProcessError as e:
        print e.cmd
        print e.output
        sys.exit(1)
    except OSError as e:
        print "OSError: qemu-img command not found"
        sys.exit(1)
    else:
        return destination


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

    parser.add_argument("-i", "--image-prefix",
                        action='store', dest='IMAGE_PREFIX',
                        help="destination prefix for the backup qcow2 image "
                             "name")

    parser.add_argument("-c", "--copies",
                        action='store', dest='COPIES',
                        help="")

    parser.add_argument("-S", "--snapshot-size",
                        action='store', dest='SIZE', type=int,
                        help="")

    parser.add_argument('--version', action='version',
                        version="%(prog)s {}".format(__version__))

    # Validate and manipulate arguments input
    args = parser.parse_args()
    # Create the source device object getting data with lvdisplay
    src_device = Device(args.SOURCE)
    # Check destination folder exists and is a directory
    if os.path.isdir(args.DESTINATION):
        dst_dir = args.DESTINATION
    else:
        print "OSError: '{}' invalid destination".format(args.DESTINATION)
        sys.exit(1)
    # If prefix is not provided lv name will be used as default prefix
    if args.IMAGE_PREFIX:
        image_prefix = args.IMAGE_PREFIX
    else:
        image_prefix = src_device.lv
    image = '{}-{}.qcow2'.format(image_prefix, time.strftime('%Y%m%d'))

    # Create the lv snapshot
    snapshot = src_device.create_snapshot()
    _qemu_img_cmd(snapshot, dst_dir, image)

    # Delete old copies
    images = Images(dst_dir, image_prefix)
    images.keep_only(args.COPIES)

    # TODO add parameter defaults and help
    # TODO read a configuration file
    # TODO delete check pending snapshots
    # Check space left in the vg (done by lvcreate itself)
    # TODO Check number of backups (delete early/after?)
    # TODO md5sum file
    # TODO write a run function to include subprocess code
    # TODO check image file already exists

    src_device.delete_snapshot()
    return 0

if __name__ == '__main__':
    main()
