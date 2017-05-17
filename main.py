#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-04-12 22:05:02
# @Author  : Tom Hu (h1994st@gmail.com)
# @Link    : http://h1994st.com
# @Version : 1.0

import os
import sys
import json
import time
from datetime import datetime
import getpass
from pprint import pprint

import requests
from lxml import html

import pushbullet
from pushbullet import Pushbullet

LOGIN_PAGE_URL = 'https://weblogin.umich.edu/'
LOGIN_POST_URL = 'https://weblogin.umich.edu/cosign-bin/cosign.cgi'
HOUSING_PAGE_URL = 'https://studentweb.housing.umich.edu'
APARTMENT_SELECTION_PAGE_URL = 'https://studentweb.housing.umich.edu/SelectRoom.asp?Function=6164'
SEARCH_ROOM_URL = 'https://studentweb.housing.umich.edu/SelectRoomResults.asp'

HOUSING_PATE_SECTION_TEXT = 'Graduate and Family Residences 2017-2018'
NO_RESULT_TEXT = 'There are no rooms available that match your search.'

session_requests = requests.session()


class VoidDevice(object):
    """A fake device."""
    def __init__(self):
        super(VoidDevice, self).__init__()

    def push_note(self, *args, **kwargs):
        pass


def init_device(pushusername):
    """Initialize the device that receives notification."""

    # Notification option (Default: Y)
    # ans = raw_input('Do you need Pushbullet notification? (Y/n): ')
    # while ans.strip().upper() not in ['Y', '', 'N']:
    #     ans = raw_input('Do you need Pushbullet notification? (Y/n): ')

    # if ans.strip().upper() == 'N':
    #     # Do not need notification
    #     return VoidDevice()

    # Check configuration file 'conf.json'
    if pushusername == 'yuxin':
        if not os.path.exists('conf.json'):
            conf = {
                'pushbullet_access_token': '',
                'device_name': ''
            }

            # Dump template file
            with open('conf.json', 'w') as fp:
                json.dump(conf, fp)

            print >> sys.stderr, 'Please set "conf.json" at first.'
            sys.exit(1)

        # Load configuration file
        with open('conf.json', 'r') as fp:
            conf = json.load(fp)

        # Please refer to related document on 'pushbullet.com'
        access_token = conf.get('pushbullet_access_token', None)
        device_name = conf.get('device_name', None)

        # Check access token
        if access_token is None:
            print >> sys.stderr, 'Please set your own pushbullet access token.'
            sys.exit(1)

        try:
            pb = Pushbullet(access_token)
        except pushbullet.errors.InvalidKeyError:
            print >> sys.stderr, 'Wrong api key!'
            sys.exit(1)

        # Check device name
        if device_name is None:
            print >> sys.stderr, 'Please set your own device name.'
            sys.exit(1)

        try:
            device = pb.get_device(device_name)
        except pushbullet.errors.InvalidKeyError:
            print >> sys.stderr, 'Wrong device name!'
            device_names = [device.nickname for device in pb.devices]
            print >> sys.stderr, 'Please select from: %s.' % (
                ','.join(device_names))
            sys.exit(1)

        # Print the information of the device
        print device

        return device
    else:
        if not os.path.exists('conf_nan.json'):
            conf = {
                'pushbullet_access_token': '',
                'device_name': ''
            }

            # Dump template file
            with open('conf.json', 'w') as fp:
                json.dump(conf, fp)

            print >> sys.stderr, 'Please set "conf.json" at first.'
            sys.exit(1)

        # Load configuration file
        with open('conf.json', 'r') as fp:
            conf = json.load(fp)

        # Please refer to related document on 'pushbullet.com'
        access_token = conf.get('pushbullet_access_token', None)
        device_name = conf.get('device_name', None)

        # Check access token
        if access_token is None:
            print >> sys.stderr, 'Please set your own pushbullet access token.'
            sys.exit(1)

        try:
            pb = Pushbullet(access_token)
        except pushbullet.errors.InvalidKeyError:
            print >> sys.stderr, 'Wrong api key!'
            sys.exit(1)

        # Check device name
        if device_name is None:
            print >> sys.stderr, 'Please set your own device name.'
            sys.exit(1)

        try:
            device = pb.get_device(device_name)
        except pushbullet.errors.InvalidKeyError:
            print >> sys.stderr, 'Wrong device name!'
            device_names = [device.nickname for device in pb.devices]
            print >> sys.stderr, 'Please select from: %s.' % (
                ','.join(device_names))
            sys.exit(1)

        # Print the information of the device
        print device

        return device


def extract_info_from_html_elems(elems):
    # Cut table header
    elems = elems[1:]

    departments = []
    for elem in elems:
        vals = elem.cssselect('td')
        vals[0] = vals[0].cssselect('a')[0]

        department = {
            'Name': vals[0].text,
            'Area': vals[1].text,
            'Apartment Type': vals[2].text,
            'Contract Start Date': vals[3].text,
            'Square Footage': vals[4].text,
            'Environment': vals[5].text,
            'Air Conditioning': vals[6].text,
            'Furniture Type': vals[7].text,
            'Bedroom Dimensions': vals[8].text,
            'Available Space': vals[9].text
        }

        departments.append(department)

    return departments


def search():
    payload = {
        'fld24526': 49,  # Ready to process: {49(Yes)}
        'fld24527': '',  # Furnishings: {Furnished, Unfurnished}
        'fld24524': 'September 1',  # Contract start date: {July 1, July 16, August 1, August 16, September 1, September 16}
        'dateflddtArrival': '9/1/2017',  # Arrival date: %-m/%-d/%Y (e.g., 8/15/2017)
        'dateValueflddtArrival': '',
        'fldFunction': 6164,
        'btnSubmit': 'Search'
    }

    session_requests.get(APARTMENT_SELECTION_PAGE_URL)

    print 'Search'
    result = session_requests.post(
        SEARCH_ROOM_URL, data=payload)

    if result.status_code / 100 != 2:
        print 'Failed'
        return None

    if result.text.find(NO_RESULT_TEXT) != -1:
        # No result
        print 'No result'
        return None

    # f = open('myhtml.html')
    # txt = f.read()
    # tree = html.fromstring(txt)
    # Parse html file
    tree = html.fromstring(result.text)

    # Select apartment list
    elems = tree.cssselect('table.DataTable tr')

    # Check the number of elements (at lease one row)
    if len(elems) < 1:
        # No result
        print 'No result (false positive)'
        return None

    # Extract from html elements
    departments = extract_info_from_html_elems(elems)

    print 'Results!'
    return departments


def login(username, password):
    payload = {
        'ref': '',
        'service': '',
        'required': '',
        'login': username,
        'password': password
    }

    # Get cookie
    print 'Get cookie'
    result = session_requests.get(LOGIN_PAGE_URL)
    if result.status_code / 100 != 2:
        print 'Failed'
        return False

    # Login
    print 'Login'
    result = session_requests.post(
        LOGIN_POST_URL, data=payload)
    if result.status_code / 100 != 2:
        print 'Failed'
        return False

    # Check login
    result = session_requests.get(HOUSING_PAGE_URL)
    if result.status_code / 100 != 2:
        print 'Failed'
        return False

    if result.text.find(HOUSING_PATE_SECTION_TEXT) == -1:
        print 'Failed'
        return False

    return True


def main():
    device = init_device('yuxin')
    device_nan = init_device('nan')
    username = "yuxinliu"
    pwd = "Irislyx1024"
    if login(username, pwd):
        print "login success"
        while True:
            print str(datetime.now())
            departments = search()

            if departments is not None:
                pprint(departments)

                simple_info = [(
                    '%s (Space: %s)' % (
                        department['Name'],
                        department['Available Space'])) for department in departments]

                device.push_note(
                    'NORTHWOOD!!!!!!!', '\n'.join(simple_info))
                device_nan.push_note(
                    'NORTHWOOD!!!!!!!', '\n'.join(simple_info))

                print 'Sleeping 5 minutes...'
                time.sleep(2 * 60)
            else:
                device.push_note("test!", '\n')
                device_nan.push_note("test!", '\n')
                # print 'Sleeping 2 minutes...'
                time.sleep(2 * 60)
    else:
        print >> sys.stderr, 'Please check your uniqname and password.'


if __name__ == '__main__':
    main()
