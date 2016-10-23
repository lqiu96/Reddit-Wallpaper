import praw
import os
import os.path
import argparse
import requests
import shutil
from urllib.request import urlopen
from PIL import Image
from bs4 import BeautifulSoup

SUBREDDIT = {'earthporn'} #,'spaceporn', 'skyporn', 'waterporn'}
DEFAULT_DIRECTORY = r'C:\Users\Lawrence\Pictures\Wallpapers\\'
FAIL_DIRECTORY = r'C:\Users\Lawrence\Pictures\Rejected Wallpapers\\'
MIN_RATIO, MAX_RATIO = 1.15, 1.6
time = {
    'hour': lambda x, y: x.get_top_from_hour(limit=y),
    'day': lambda x, y: x.get_top_from_day(limit=y),
    'week': lambda x, y: x.get_top_from_week(limit=y),
    'month': lambda x, y: x.get_top_from_month(limit=y),
    'year': lambda x, y: x.get_top_from_year(limit=y),
    'all': lambda x, y: x.get_top_from_all(limit=y)
}

user_agent = 'Wallpaper Retreiver 1.0 by /u/burstoflight'
reddit = praw.Reddit(user_agent=user_agent)
parser = argparse.ArgumentParser(description='Retreive Wallpapers from Reddit')
parser.add_argument('-t', '--top', default='day', choices=['hour', 'day', 'week', 'month', 'year', 'all'], help='Choice time-frame for top submissions')
parser.add_argument('-n', '--num', type=int, default=25, help='Submission limit')
parser.add_argument('-s', '--subreddit', nargs='+', help='Add subreddits to search') 
parser.add_argument('-v', '--verbosity', action='store_true', help='Print the changelog')
args = parser.parse_args()
verbose = args.verbosity
if args.subreddit != None:
    SUBREDDIT.update(args.subreddit)

submissions = []
for sub in SUBREDDIT:
    submissions += time.get(args.top, 'day')(reddit.get_subreddit(sub), args.num)
scores = [post.score for post in submissions]
scores.sort()
# Median score determines the minimum score to retrieve images
median_score = scores[len(scores) // 2] if len(scores) % 2 == 1 else (scores[(len(scores) // 2) - 1] + scores[len(scores) // 2]) // 2
posts = list(filter(lambda x: x.score >= median_score, submissions))
# Remove the certain characters that cannot be included in file names
is_bad_char = lambda x: x in [':', ';', '<', '>', '"', '\\', '/', '|', '?', '!', '*']
post_titles = list(map(lambda p: "".join(['' if is_bad_char(l) else l for l in list(p.title)]), posts))
i = 0
while i < len(post_titles):
    # Store new name into the post object and encode in utf8
    posts[i].title = post_titles[i]
    i += 1
files = []
for post in posts:
    if post.url.startswith('http://imgur.com'):
        page = urlopen(post.url)
        soup = BeautifulSoup(page.read(), 'html.parser')
        rank = soup.find('div', {'class': 'post-image'}).a.img
        post.url = 'https:' + rank['src']
    print(post.url)
    r = requests.get(post.url, stream=True)
    file_name = post.title[:250] if len(post.title) > 250 else post.title
    file_location = '{}{}.png'.format(DEFAULT_DIRECTORY, file_name)
    with open(file_location, 'wb') as out_file:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, out_file)
    files.append(file_location)
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
                print('Rejected: {}'.format(file))
            rejected_file = '{}{}'.format(FAIL_DIRECTORY, file[39:])
            if len(rejected_file) > 250:
                rejected_file = rejected_file[:250] + '.png'
            if os.path.exists(rejected_file):
                os.remove(rejected_file)
            os.rename(file, rejected_file)
        else:
            if verbose:
                print('Passed: {}'.format(file))
    except IOError as e:
        print(e.errno)
        f.close()
        os.remove(file)
        if verbose:
            print('Removed: {}'.format(file))
