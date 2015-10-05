"""
This script looks at the filtered list of fics from a fandom,
(1) isolates the tags, (2) resolves tags to their canonical forms
and (3) drops rare ones (in two steps - first tags that AO3 considers
rare and unfilterable, then tags that are underused in the corpus
we are gathering. This number is specified in config.py under
MIN_TAG_NUMBER). This script also (4) removes fics from consideration
that have tags in OMIT_TAGS, also configured in config.py.

Tag resolution
--------------
For each tag, the script determines whether it is
(1) common (canonical)
(2) merged (synonym)
(3) unfilterable -- rare

How to tell the difference:

-- common tags look like:

"This tag belongs to the (...) category. It's a common tag.

Tags with the same meaning: X, Y, Z, ..."
.
-- merged tags look like:

"Mergers

X has been made a synonym of ___Y____

-- unfilterable tags look like:

"This tag has not been marked common and can't be filtered on (yet)."

We create a dictionary that maps merged tags to their canonical
counterparts, and drop all the rare, unfilterable tags. Take the set of those
to drop duplicate tags (e.g. if the fic is tagged with X and Y and X resolves
to Y). As we do this, we also drop fics with tags that the user has
specified as undesired, i.e. OMIT_TAGS.
"""

import os
import re
import json
from collections import defaultdict
import operator
import requests
from bs4 import BeautifulSoup

from config import *
BASE_URL = 'http://archiveofourown.org/tags/'

TAG_TYPES = ['character', 'relationship', 'freeform']

# ---------------------
#  Load existing files
# ---------------------

# load the JSON file of fics into memory
try:
    f = open(FANDOM + '.filtered.json', 'r')
except IOError:
    print 'ERROR: could not find fic file %s' % FANDOM + '.filtered.json'
fics = json.loads(f.read())
f.close()

# load the JSON file of tags, if it exists
if os.path.isfile('canonical_tags.json'):
    try:
        f = open('canonical_tags.json', 'r')
    except IOError:
        print 'ERROR: Found canonical_tags.json but could not open it'
    CANONICAL_TAGS = json.loads(f.read())
    f.close()
    print 'INFO:  Starting with tag correspondences from canonical_tags.json'
else:
    print 'INFO:  Did not find tags.json, will start tag location from scratch'
    CANONICAL_TAGS = defaultdict(dict)


# -----------
#  FUNCTIONS
# -----------

def get_tags_used(fics):
    """
    Make a dictionary of all the tags used in the corpus,
    divided into 'character', 'relationship' and 'freeform' categories
    """
    # get dictionary of tags used in our corpus
    used_tags = defaultdict(lambda: defaultdict(int))

    for fic_id, fic in fics.items():
        for tag_type in TAG_TYPES:
            if tag_type in fic:
                for tag in fic[tag_type]:
                    used_tags[tag_type][tag] += 1

    return used_tags


def get_correspondences_for_tag(tag):
    """
    Helper function that gets the correspondence info for a tag

    If canonical, get list of tags it corresponds to, and return
    dictionary of (merged -> canonical) pairs.

    If merged, get canonical tag it corresponds to, return
    dictionary with single (merged -> canonical) pair.

    If unfilterable, return dictionary with single (unfilterable -> None) pair.
    """
    r = requests.get(BASE_URL + tag.replace('/', '%2F'))

    # first do a regex to match unfilterable tags
    if re.search('This tag has not been marked common', r.text):
        # if it matches, it's unfilterable, so its canonical tag is None
        return dict([(tag, None)])

    # next do a regex to match the merged tags
    m = re.search('has been made a synonym of <a href=\".*\">(.*)</a>', r.text)
    if m:
        # if it matches, return its canonical tag
        return dict([(tag, m.groups()[0])])

    # lastly, if it's canonical
    if re.search('a common tag', r.text):
        soup = BeautifulSoup(r.text)
        return_dict = {tag: tag}
        list_of_synonyms = soup.find('div', class_='synonym listbox group')
        if list_of_synonyms:
            for node in list_of_synonyms.find_all('li'):
                return_dict[node.get_text().strip()] = tag
        return return_dict

    # shouldn't get here, but just in case:
    print "ERROR: Couldn't determine what kind of tag %s was" % tag
    return dict([(tag, None)])


def update_tag_correspondences(used_tags):
    """
    Update dictionary of all non-canonical -> canonical tag correspondences.
    Does not return anything but modifies CANONICAL_TAGS in place.
    """
    tag_correspondences = defaultdict(dict)

    for tag_type in TAG_TYPES:
        for tag, count in sorted(used_tags[tag_type].items(),
                                 key=operator.itemgetter(1),
                                 reverse=True):
            if tag not in CANONICAL_TAGS[tag_type]:
                # if we haven't already got the info for that tag, get it and
                # add it to the dictionary
                CANONICAL_TAGS[tag_type].update(
                    get_correspondences_for_tag(tag))


def get_new_tags(old_tags, tag_type):
    """
    For a given fic in the form of its old_tags of a certain tag_type,
    return a new set of a tags that have been converted to their canonical
    forms. Remove any tags that convert to None or are in OMIT_TAGS,
    and uniq the set.
    """
    new_tags = {CANONICAL_TAGS[tag_type][old_tag] for old_tag in old_tags}

    new_tags = new_tags - set(OMIT_TAGS)
    new_tags.discard(None)

    return list(new_tags)


# --------------
#     MAIN
# --------------

# get the tags that were used in this set of fics
used_tags = get_tags_used(fics)

# update the dictionary of tag -> canonical tag (or None) correspondences,
# CANONICAL_TAGS
update_tag_correspondences(used_tags)
# write out new set to file
with open('canonical_tags.json', 'w') as f:
    f.write(json.dumps(CANONICAL_TAGS))
print 'INFO:  updated CANONICAL_TAGS in canonical_tags.json'

# create new 'canonical_character', 'canonical_relationship',
# 'canonical_freeform' attributes for each fic and fill them with the
# corresponding canonical tags
for fic_id, fic in fics.items():
    for tag_type in TAG_TYPES:
        if tag_type in fic:
            fics[fic_id]['canonical_%s_tags' % tag_type] = \
                get_new_tags(fic[tag_type], tag_type)
        else:
            fics[fic_id]['canonical_%s_tags' % tag_type] = list()

# write out to file
with open(FANDOM + '.filtered.canonical.json', 'w') as f:
    f.write(json.dumps(fics))
