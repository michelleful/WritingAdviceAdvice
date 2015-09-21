# Specify the fandom name exactly as it appears in the
# Archive of our own main page for that fandom, e.g.
# http://archiveofourown.org/tags/Lewis%20(TV)/works
# --> FANDOM = 'Lewis%20(TV)'

FANDOM = 'Lewis%20(TV)'

# specify the maximum number of pages to download
# downloading will be in reverse chronological order (i.e. newest first),
# so if MAX_PAGES is small and MINIMUM_AGE filter is large, you
# may end up with no fics after filtering.
MAX_PAGES = 5  # None  if you want to download all

# FILTERS
# the overall purpose of this filters is to ensure that we have
# a relatively uniform corpus with respect to the things we wish
# to measure

# the audience for fics in a different language is very different
# so it makes sense to include only English fics
ENGLISH_ONLY = True

# similarly, crossover fics get audiences from multiple fandoms
# (though some people avoid them)
# so it makes sense to eliminate them
NO_CROSSOVER = True

# multi-chapter stories have more chances to be noticed than a
# single-chapter story and get more hits over time
# we'll probably want to include these eventually, but
# our initial approach will be to analyze only single-chapter fics
SINGLE_CHAPTER = True

# some people wait for a fic to be done before reading it
# and we might get odd results from incomplete fics anyway
# so it makes sense to set this to be true
COMPLETE = True  # doesn't matter if SINGLE_CHAPTER is set to True

# kudos/comments/views tend to come in quickly initially and then level off
# in order to capture the kudos count in its stable state, only consider
# fics older than a certain number of days
MINIMUM_AGE = 0   # 6 * 30  # in days

# Note: something we're not accounting for - if people search by kudos,
# they will tend to read the fics that are at the top - a 'rich get richer'
# effect. Is this a problem?

# don't consider tags with fewer than MIN_TAG_NUMBER uses in the dataset
MIN_TAG_NUMBER = 2

# write down canonical tags that you wish to omit from the set
# e.g. fanart, poetry
OMIT_TAGS = [
    'Fanart',
    'Poetry'
    'Podfic'
]
