from typing import Text
import requests
import urllib
import sys
from lxml.html import fromstring
from lxml import etree
import argparse
import validators
import json
import os
import re
from datetime import datetime, timedelta, timezone

def request_page(url):
    headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'accept-ancoding': 'gzip, deflate, br',
               'connection': 'keep-alive',
               'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0',
               }

    try:
        page = requests.get(url, headers=headers)
    except requests.exceptions.HTTPError as e:
        print('HTTP Error.\nUsing: ' + url)
        print(e)
    except requests.exceptions.Timeout as e:
        print('Connection Timeout.\nUsing: ' + url)
        print(e)
    except requests.exceptions.TooManyRedirects as e:
        print('Check URL.\nUsing: ' + url)
        print(e)
    except requests.exceptions.RequestException as e:
        print('Bad Request.\nUsing: ' + url)
        print(e)
    except Exception as e:
        print('General Exception.\nUsing: ' + url)
        print(e)
    return(page)

def get_bitly_link(link, title):
    # bitly connection

    header = {
        "Authorization": "Bearer "+config["API_KEY"],
        "Content-Type": "application/json"
    }
    title = title or link
    params = {
        "long_url": link,
        "title": title
    }
    link = requests.post("https://api-ssl.bitly.com/v4/bitlinks",
                         json=params, headers=header).json()['link'] or link
    return(link)


def main(base_url, bitly, but):
    # get the content
    page = request_page(base_url)

    # build the parser
    parser = fromstring(page.content, base_url=base_url)

    # Save the webinar to order them later
    webinars = []
    year = datetime.now(tz=timezone.utc).strftime('%Y')

    # looping over the TR in the webinar's table discating what is not a webinar
    # to use if have no the trending now "/html/body/table[1]/tbody/tr/td/table/tbody/tr/td/table/tbody/tr[3]/td/*"
    # /html/body/table[1]/tbody/tr/td/table/tbody/tr/td/table/tbody/tr[3]/td
    # /html/body/table[1]/tbody/tr/td/table/tbody/tr[1]/td/table/tbody/tr[5]
    # /html/body/table[1]/tbody/tr/td/table/tbody/tr[1]/td/table/tbody/tr[5]/td
    for e in parser.xpath("/html/body/table[1]/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/*"):
        if e.get('class') != 'responsive_padding':
            continue
        elif e.text != None:
            continue
        context = etree.iterwalk(e, events=("start",), tag=("strong","a"))
        for action, elem in context:
            if elem.text == None:
                continue
            if (elem.tag.lower() == 'strong'):
                times = re.split("\|",elem.text.strip())
                date = times.pop(0).strip()
            if (elem.tag == 'a' and elem.text.strip().lower() != 'register'):
                title = elem.text.strip()
            if (elem.tag == 'a' and elem.text.strip().lower() == 'register'):
                link = elem.get('href')
                # The Split is to remove the tracking parameters and get just the link to the registration page.
                link = urllib.request.urlopen(link).url.split('?')[0]
                if bitly:
                    link = get_bitly_link(link, title)
                #TODO: add here the case insensitivity 
                if not any([m in date for m in but]):
                    for time in times:
                        if   ('EDT' in time) or ('EST' in time):
                            utc_offset = -5
                        elif ('GMT' in time):
                            utc_offset = 0
                        elif ('BST' in time):
                            utc_offset = 1
                        elif ('CST' in time) or ('SGT' in time):
                            utc_offset = 8
                        elif ('AEDT' in time) or ('AEST' in time):
                            utc_offset = 11
                        try:
                            time = re.findall("\d{1,2}:\d{2}\s?(?:AM|PM|a\.m\.|p\.m\.)?",time)[0]
                            utc_time = time.strip().lower().replace('.', '')
                            break
                        except Exception as e:
                            print(f'Error processing: {title}')
                            print('\t',e)
                    else:
                        # Assume EDT
                        utc_offset = 0
                        
                    eventdatetime = datetime.now(tz=timezone.utc)
                    date_noday = re.split("^[a-zA-Z]+,\s",date)[1]
                    try:
                        eventdatetime = datetime.strptime(date_noday + ' ' + year + ' ' + utc_time + ' UTC',
                                                         '%B %d %Y %H:%M %p %Z') + timedelta(hours=utc_offset)
                        
                    except Exception as e:
                        print(f'Error in: {title}, Date: {date_noday} as: {e}\n')
                        try:
                            eventdatetime = datetime.strptime(date_noday + ' ' + year + ' UTC',
                                                             '%B %d %Y %Z') + timedelta(hours=utc_offset)
                        except Exception as e:
                            print(f'Error in: {title}, Date: {date_noday} as: {e}\n')
                    finally:
                        webinars.append(
                            {'date': eventdatetime,
                            'event': f"{date.split(',')[1].strip()} : **{title}**\n* :(fas fa-user-clock fa-fw): {' / '.join(times)}\n* :(fas fa-user-check fa-fw): [Register]({link})"})

    # sorting by datetime
    webinars.sort(key=lambda x: x['date'])

    # printing out
    print(f'({len(webinars)}) Events ready for copy & Paste ...\n\n')
    for webinar in webinars:
        print(webinar['event'], "\n")


if __name__ == '__main__':
    print('GartnerEmailParser (by BigG):')
    print('THe URL only need few parameters as: https://app.gartnerformarketers.com/e/es?e=xxx&elqTrackId=yyy&elq=zzz')
    # Define how to use the program
    parser = argparse.ArgumentParser(description="Parser for emails from gartnerwebinars@gartner.com")
    parser.add_argument("-c", "--config", default='./GartnerEmailParser.json',
                        help="configuration file (default: GartnerEmailParser.json)")
    parser.add_argument("-b", help="create the bit.ly links using your API details", action="store_true")
    parser.add_argument("-e", nargs='+', default=[], help="exclude specific the months (e.g -e January February)")
    parser.add_argument("URL", help="url from the gartner email (at the top)")

    args = parser.parse_args()

    # Check for the config file
    if os.path.isfile(args.config):
        with open(args.config, "r") as configfile:
            config = json.load(configfile)
    else:
        print(f'Could not find {args.config}')
        # command line syntax error return 2
        sys.exit(2)

    # check if the URL is well formed
    if not validators.url(args.URL.replace('\\', ''), public=True):
        print(f'Invalid URL: {args.URL}')
        # command line syntax error return 2
        sys.exit(2)

    main(args.URL.replace('\\', ''), args.b, args.e)
