"""
Downloads data for all publicly-available fics in a given fandom
from archiveofourown.org (AO3) and exports it to structured JSON form
"""

import requests
import codecs
from bs4 import BeautifulSoup
import json

AO3_BASE_URL = 'http://archiveofourown.org/'
FANDOM = 'Lewis%20(TV)'
CONSTRUCTED_URL = AO3_BASE_URL + 'tags/' + FANDOM + '/works'


def get_last_page_number():
    """
    Find out how many pages there are in the fic listing for the entire fandom
    """
    # first get the first page and count how many pages there are
    first_page = CONSTRUCTED_URL
    r = requests.get(first_page)

    # parse the text with BeautifulSoup to obtain the last page number
    soup = BeautifulSoup(r.text)
    pagination = soup.find('ol', class_='pagination actions')
    return pagination.find_all('a')[-2].text


def get_links_on_page(page_number):
    """
    From a particular page in the fic listing, get links to the fics
    """
    url = CONSTRUCTED_URL + '?page=%s' % page_number
    r = requests.get(url)

    # get the list of links to fics on this page
    soup = BeautifulSoup(r.text)
    links = soup.find_all('li', class_='work blurb group')
    return [link['id'].split('_')[1] for link in links]


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
               .replace(u'\u201D', '"')


def parse_work(work_id):
    """
    Parse the html page for a particular fic, extracting out:
    - title
    - author(s)
    - metadata (in the box at the top of each AO3 fic)
    - chapter text
    """
    print "LOG: Parsing work_id %s" % work_id

    html = BeautifulSoup(get_work(work_id))
    all_data = dict()

    # extract title of entire fic
    title = html.find('h2', class_='title heading')
    all_data['Title'] = title.get_text().strip()

    # extract author(s) of entire fic
    authors = html.findAll('a', class_='login author')
    all_data['Authors'] = [author.get_text() for author in authors]

    # extract summary of entire fic (useful because it's what people see
    # on the works index, could be decisive in picking whether to read
    # a certain fic)
    summary = html.find('div', class_='summary module')\
                  .find('blockquote', class_='userstuff')
    all_data['Summary'] = remove_unicode(summary.get_text())
    metadata = html.find('dl', class_='work meta group')

    # extract out the keys for metadata, such as 'Kudos'
    keys = [node.get_text().strip() for node in metadata.findAll('dt')]
    # extract out the actual values for the metadata
    values = list()
    for node in metadata.findAll('dd'):
        # handle things that aren't lists like languages and series name
        if 'language' in node['class'] or 'series' in node['class']:
            values.append(node.get_text().strip())
        # differently from those that are lists
        else:
            values.append([subnode.get_text().strip()
                           for subnode in node.findAll('li')])
    all_data.update(zip(keys, values))

    # add in the 'stats' metadata, which are embedded in
    # another definition list (dl)
    metadata = html.find('dl', class_='stats')
    keys   = [node.get_text().strip() for node in metadata.findAll('dt')]
    values = [node.get_text().strip() for node in metadata.findAll('dd')]
    all_data.update(zip(keys, values))
    all_data.pop('Stats:')

    # extract out the actual text
    chapters = dict()
    for i, chapter_node in enumerate(html.findAll('div', class_='userstuff')):
        chapters[i+1] = remove_unicode(chapter_node.get_text().strip())
    all_data['Text'] = chapters

    return all_data


def download_fandom():
    """
    Download all fics for a particular fandom and dump the result to JSON
    """
    last_page_number = get_last_page_number()
    last_page_number = 1  # DEBUG - remove this line to get all fics in fandom

    all_data = dict()
    for i in range(1, last_page_number + 1):
        work_ids = get_links_on_page(i)
        for work_id in work_ids:
            all_data[work_id] = parse_work(work_id)

    with open(FANDOM + '.json', 'w') as f:
        f.write(json.dumps(all_data))


download_fandom()
