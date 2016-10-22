import praw
import os
import os.path
import argparse
from urllib import urlretrieve
from PIL import Image

SUBREDDIT = {'earthporn', 'spaceporn', 'skyporn', 'waterporn'}
DEFAULT_DIRECTORY = r'C:\Users\Lawrence\Pictures\Wallpapers\\'
FAIL_DIRECTORY = r'C:\Users\Lawrence\Pictures\Rejected Wallpapers\\'
MIN_RATIO, MAX_RATIO = 1.15, 1.6
DEFAULT_LIMIT = 25
time = {
    'hour': lambda x: x.get_top_from_hour(limit=DEFAULT_LIMIT),
    'day': lambda x: x.get_top_from_day(limit=DEFAULT_LIMIT),
    'week': lambda x: x.get_top_from_week(limit=DEFAULT_LIMIT),
    'month': lambda x: x.get_top_from_month(limit=DEFAULT_LIMIT),
    'year': lambda x: x.get_top_from_year(limit=DEFAULT_LIMIT)
}

user_agent = 'Wallpaper Retreiver 1.0 by /u/burstoflight'
reddit = praw.Reddit(user_agent=user_agent)
parser = argparse.ArgumentParser(description='Retreive Wallpapers from Reddit')
parser.add_argument('-t', '--top', default='day', choices=['hour', 'day', 'week', 'year', 'alltime'], help='Choice time-frame for top submissions')
parser.add_argument('-s', '--subreddit', nargs='+', help='Add subreddits to search') 
parser.add_argument('-v', '--verbosity', action='store_true', help='Print the changelog')
args = parser.parse_args()
verbose = args.verbosity
if args.subreddit != None:
    SUBREDDIT.update(args.subreddit)

submissions = []
for sub in SUBREDDIT:
    submissions += time.get(args.top, 'day')(reddit.get_subreddit(sub))
scores = [post.score for post in submissions]
scores.sort()
# Median score determines the minimum score to retrieve images
median_score = scores[len(scores) / 2] if len(scores) % 2 == 1 else (scores[(len(scores) / 2) - 1] + scores[len(scores) / 2]) / 2
posts = [post for post in submissions if post.score >= median_score]
# Remove the certain characters that cannot be included in file names
is_bad_char = lambda x: x in [':', ';', '<', '>', '"', '\\', '/', '|', '?', '*']
post_titles = map(lambda p: "".join(['' if is_bad_char(l) else l for l in list(p.title)]), posts)
i = 0
while i < len(post_titles):
    # Store new name into the post object and encode in utf8
    posts[i].title = post_titles[i].encode('utf8')
    i += 1
files = map(lambda x: x[0], [urlretrieve(post.url.encode('utf8'), '{}{}.png'.format(DEFAULT_DIRECTORY, post.title)) for post in posts])
for file in files:
    try:
        f = open(file, 'rb')
        image = Image.open(f)
        dimension = image.size
        f.close()
        width, height = dimension
        ratio = width * 1.0 / height
        # Make sure that the image has good ratio to be put on a Desktop Wallpaper
        if not (MIN_RATIO < ratio < MAX_RATIO):
            if verbose:
                print 'Rejected: {}'.format(file)
            rejected_file = '{}{}.png'.format(FAIL_DIRECTORY, file[38:])
            if os.path.isfile(rejected_file):
                os.remove(rejected_file)
            os.rename(file, rejected_file)
        else:
            if verbose:
                print 'Passed: {}'.format(file)
    except IOError:
        f.close()
        os.remove(file)
        if verbose:
            print 'Removed: {}'.format(file)
