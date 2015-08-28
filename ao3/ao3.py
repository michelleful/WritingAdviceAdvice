import requests
import codecs
from bs4 import BeautifulSoup
from collections import OrderedDict
import json

AO3_BASE_URL = 'http://archiveofourown.org/'
FANDOM = 'Lewis%20(TV)'
CONSTRUCTED_URL = AO3_BASE_URL + 'tags/' + FANDOM + '/works'


def get_last_page_number():
    # first get the first page and count how many pages there are
    first_page = CONSTRUCTED_URL
    r = requests.get(first_page)

    # parse the text with BeautifulSoup to obtain the last page number
    soup = BeautifulSoup(r.text)
    pagination = soup.find('ol', class_='pagination actions')
    return pagination.find_all('a')[-2].text


def get_links_on_page(page_number):
    url = CONSTRUCTED_URL + '?page=%s' % page_number
    r = requests.get(url)

    # get the list of links to fics on this page
    soup = BeautifulSoup(r.text)
    links = soup.find_all('li', class_='work blurb group')
    return [link['id'].split('_')[1] for link in links]


def get_work(work_id):
    url = AO3_BASE_URL + 'works/' + work_id + '?view_adult=true&view_full_work=true'
    r = requests.get(url)
    return r.text


def parse_work(work_id):
    print "Parsing work_id %s" % work_id

    html = BeautifulSoup(get_work(work_id))
    all_data = dict()

    # extract title of entire fic
    title = html.find('h2', class_='title heading')
    all_data['title'] = title.get_text()

    # extract author(s) of entire fic
    authors = html.findAll('a', class_='login author')
    all_data['authors'] = [author.get_text() for author in authors]

    # extract summary of entire fic (useful because it's what people see
    # on the works index, could be decisive in picking whether to read
    # a certain fic)
    summary = html.find('div', class_='summary module')\
                  .find('blockquote', class_='userstuff')
    all_data['summary'] = summary.get_text()
    metadata = html.find('dl', class_='work meta group')
    # extract out the keys for metadata, such as 'Kudos' 
    keys = list()
    for node in metadata.findAll('dt'):
        keys.append(','.join(node.findAll(text=True)).strip())
    values = list()
    for node in metadata.findAll('dd'):
        if 'language' in node["class"] or 'series' in node["class"]:
            values.append(','.join(node.findAll(text=True)).strip())
        else:
            values.append([subnode.get_text() for subnode in node.findAll("li")])
    all_data.update(zip(keys, values))
    
    #add in the 'stats' metadata 

    metadata = html.find('dl', class_='stats')
    for node in metadata.findAll('dt'):
        keys.append(','.join(node.findAll(text=True)))
    for node in metadata.findAll('dd'):
        values.append(','.join(node.findAll(text=True)).strip())

    all_data.update(zip(keys, values))

    all_data.pop("Stats:")



    # extract out the actual text - handles single chapters only
    chapters = dict()
    for i, chapter_node in enumerate(html.findAll('div', class_='userstuff')):
        chapters[i+1] = chapter_node.get_text()
    all_data['text'] = chapters

    return all_data


def download_fandom():
    last_page_number = get_last_page_number()
    last_page_number = 1  # DEBUG - remove this line to get all

    all_data = OrderedDict()
    for i in range(1, last_page_number + 1):
        work_ids = get_links_on_page(i)
        for work_id in work_ids:
            all_data[work_id] = parse_work(work_id)

    with open(FANDOM + '.json', 'w') as f:
        f.write(json.dumps(all_data))


download_fandom()
