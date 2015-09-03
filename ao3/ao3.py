"""
Downloads data for all publicly-available fics in a given fandom
from archiveofourown.org (AO3) and exports it to structured JSON form
"""

import os
import requests
from bs4 import BeautifulSoup
import html2text
import json

from config import FANDOM
AO3_BASE_URL = 'http://archiveofourown.org/'
CONSTRUCTED_URL = AO3_BASE_URL + 'tags/' + FANDOM + '/works'
FINAL_OUTPUT_FILENAME = FANDOM + '.json'

def get_last_page_number():
    """
    Find out how many pages there are in the fic listing for the entire fandom
    """
    # first get the first page and count how many pages there are
    r = requests.get(CONSTRUCTED_URL)

    # parse the text with BeautifulSoup to obtain the last page number
    soup = BeautifulSoup(r.text)
    pagination = soup.find('ol', class_='pagination actions')
    return pagination.find_all('a')[-2].text


def get_work_ids_on_page(page_number):
    """
    From a particular page in the fic listing, get all the work ids on that page
    """
    url = CONSTRUCTED_URL + '?page=%s' % page_number
    r = requests.get(url)

    # get the list of links to fics on this page
    soup = BeautifulSoup(r.text)
    links = soup.find_all('li', class_='work blurb group')
    return [link['id'].split('_')[1] for link in links]


def get_all_work_ids():
    """
    Gets all the work ids in the given fandom
    """
    last_page_number = get_last_page_number()
    last_page_number = 1  # DEBUG - remove this line to get all fics in fandom

    all_work_ids = list()
    for i in range(1, last_page_number + 1):
        all_work_ids.extend(get_work_ids_on_page(i))

    return all_work_ids


def get_work(work_id):
    """
    Download the html page for a particular fic for later processing
    """
    url = AO3_BASE_URL + 'works/' + work_id \
          + '?view_adult=true&view_full_work=true'
    r = requests.get(url)
    return r.text


def remove_unicode(text):
    """
    Remove things like smart quotes from text/summary
    """
    # set(['u2019', 'u2018', 'u2013', 'u2014', 'u2026'])
    return text.replace(u'\u2019', "'")\
               .replace(u'\u2018', "'")\
               .replace(u'\u2013', '-')\
               .replace(u'\u2014', '--')\
               .replace(u'\u2026', '...')\
               .replace(u'\u201C', '"')\
               .replace(u'\u201D', '"')\
               .replace(u'\u00A0', '')\
               .replace(u'\u00AB', '')\
               .replace(u'\u00BB', '')


def html2markdown(text):
    """
    Convert html text to markdown and replace special unicode characters
    """
    return remove_unicode(html2text.html2text(text.decode('utf-8')))


def parse_work(work_id):
    """
    Parse the html page for a particular fic, extracting out:
    - title
    - author(s)
    - metadata (in the box at the top of each AO3 fic)
    - chapter text
    """
    print "INFO: Parsing work_id %s" % work_id

    html = BeautifulSoup(get_work(work_id))
    all_data = dict()

    # extract title of entire fic
    title = html.find('h2', class_='title heading')
    all_data['title'] = title.get_text().strip()

    # extract author(s) of entire fic
    authors = html.findAll('a', class_='login author')
    all_data['author'] = [author.get_text() for author in authors]

    # extract summary of entire fic (useful because it's what people see
    # on the works index, could be decisive in picking whether to read
    # a certain fic)
    summary = html.find('div', class_='summary module')\
                  .find('blockquote', class_='userstuff')
    all_data['summary'] = html2markdown(str(summary))
    metadata = html.find('dl', class_='work meta group')

    # extract out the keys and values of metadata, such as 'Fandoms'
    for node in metadata.findAll('dd'):
        key = [class_ for class_ in node['class'] if class_ != 'tags'][0]
        # handle things that aren't lists like languages and series name
        if 'language' in node['class'] or 'series' in node['class']:
            all_data[key] = remove_unicode(node.get_text().strip())
        # handle things that are in lists, which is everything else
        else:
            all_data[key] = [subnode.get_text().strip()
                               for subnode in node.findAll('li')]

    # add in the 'stats' metadata, which are embedded in
    # another definition list (dl)
    metadata = html.find('dl', class_='stats')
    keys   = [node['class'][0]
                for node in metadata.findAll('dt')]
    values = [node.get_text().strip() for node in metadata.findAll('dd')]
    all_data.update(zip(keys, values))
    all_data.pop('stats')

    # extract out the actual text, convert to markdown
    # remove the words 'Chapter Text' from the beginning of each chapter
    chapters = dict()
    for i, chapter_node in enumerate(html.findAll('div', class_='userstuff')):
        chapters[i+1] = html2markdown(str(chapter_node))\
                            .replace('### Chapter Text\n\n', '')
    all_data['text'] = chapters

    return all_data


def download_fandom():
    """
    Download all fics for a particular fandom and dump the result to JSON
    """
    all_data = dict()
    all_work_ids = get_all_work_ids()
    for work_id in all_work_ids:
        all_data[work_id] = parse_work(work_id)

    with open(FINAL_OUTPUT_FILENAME, 'w') as f:
        f.write(json.dumps(all_data))


download_fandom()
