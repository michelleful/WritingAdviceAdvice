import json
from datetime import datetime
from config import *

# load the JSON file into memory
f = open(FANDOM + '.json', 'r')
fics = json.loads(f.read())
f.close()

print 'INFO: Number of fics before filtering: %s' % len(fics)

# start filtering!
# see config.py for explanation of the variables and the reasoning
# behind using these as filters
filtered = dict()
for fic_id, fic in fics.items():
    # handle the straightforward tags
    if ENGLISH_ONLY and fic['language'] != 'English':
        continue
    if NO_CROSSOVER and len(fic['fandom']) > 1:
        continue
    if SINGLE_CHAPTER and fic['chapters'] != '1/1':
        continue
    if COMPLETE:
        existing_chapters, total_chapters = fic['chapters'].split('/')
        if existing_chapters != total_chapters:
            continue

    # remove fics that are younger than OLDER_THAN days
    # first we have to figure out which variable to use
    # published: when it was first published to the site
    # status: when it was last updated (key will not exist for
    #         single-chaptered fics)
    if 'status' in fic:
        last_date = fic['status']
    else:
        last_date = fic['published']
    # now convert that last date to something we can compute on
    last_date = datetime.strptime(last_date, '%Y-%m-%d')
    age = (datetime.today() - last_date).days
    if age < MINIMUM_AGE:
        continue

    # if it's passed all the filters
    filtered[fic_id] = fic

print 'INFO: Number of fics  after filtering: %s' % len(filtered)

with open(FANDOM + '.filtered.json', 'w') as f:
    f.write(json.dumps(filtered))
