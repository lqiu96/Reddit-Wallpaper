import praw
import os
import os.path
import argparse
import requests
import shutil
from urllib.request import urlopen
from PIL import Image
from bs4 import BeautifulSoup

DEFAULT_DIRECTORY = r'C:\Users\Lawrence\Pictures\Wallpapers\\'
FAIL_DIRECTORY = r'C:\Users\Lawrence\Pictures\Rejected Wallpapers\\'
MIN_RATIO, MAX_RATIO = 1.15, 1.6
FILE_LENGTH_LIMIT = 200
time = {
    'hour': lambda x, y: x.get_top_from_hour(limit=y),
    'day': lambda x, y: x.get_top_from_day(limit=y),
    'week': lambda x, y: x.get_top_from_week(limit=y),
    'month': lambda x, y: x.get_top_from_month(limit=y),
    'year': lambda x, y: x.get_top_from_year(limit=y),
    'all': lambda x, y: x.get_top_from_all(limit=y)
}


def is_bad_char(x):
    return x in [':', ';', '<', '>', '"', '\\', '/', '|', '?', '!', '*']


def get_files(posts):
    files = []
    for post in posts:
        # Certain imgur links do not open directly to the image
        if post.url.startswith('http://imgur.com'):
            page = urlopen(post.url)
            soup = BeautifulSoup(page.read(), 'html.parser')
            page_element = soup.find('div', {'class': 'post-image'})
            # Sometimes the link does inlcude i.imgur but opens to i.imgur
            if page_element == None:
                page_element = soup.find('img', {'class': 'shrinkToFit'})
                if page_element == None:
                    print('Could not do: {}:'.format(post.url))
                    continue
                else:
                    post.url = page_element['src']
            else:
                rank = page_element.a.img
                post.url = 'https:' + rank['src']
        print(post.url)
        r = requests.get(post.url, stream=True)
        file_name = post.title[:FILE_LENGTH_LIMIT] if len(post.title) > FILE_LENGTH_LIMIT else post.title
        file_location = '{}{}.png'.format(DEFAULT_DIRECTORY, file_name)
        with open(file_location, 'wb') as out_file:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, out_file)
        files.append(file_location)
    return files


def reject_files(files, verbose):
    for file in files:
        try:
            f = open(file, 'rb')
            image = Image.open(f)
            dimension = image.size
            f.close()
            width, height = dimension
            ratio = width * 1.0 / height
            # Make sure that the image has good ratio to be put on a Desktop Wallpaper
            if MIN_RATIO < ratio < MAX_RATIO:
                if verbose:
                    print('Passed: {}'.format(file))
            else:
                if verbose:
                    print('Rejected: {}'.format(file))
                rejected_file = '{}{}'.format(FAIL_DIRECTORY, file[39:])
                if len(rejected_file) > FILE_LENGTH_LIMIT:
                    rejected_file = rejected_file[:FILE_LENGTH_LIMIT] + '.png'
                if os.path.exists(rejected_file):
                    os.remove(rejected_file)
                os.rename(file, rejected_file)
        except IOError as e:
            f.close()
            os.remove(file)
            if verbose:
                print('Removed: {}'.format(file))


if __name__ == '__main__':
    default_subreddits = {'earthporn', 'spaceporn', 'skyporn', 'waterporn'}
    user_agent = 'Wallpaper Retreiver 1.1 by /u/burstoflight'
    reddit = praw.Reddit(user_agent=user_agent)
    parser = argparse.ArgumentParser(description='Retrieve Wallpapers from Reddit')
    parser.add_argument('-t', '--top', default='day', choices=['hour', 'day', 'week', 'month', 'year', 'all'],
                        help='Choice time-frame for top submissions')
    parser.add_argument('-n', '--num', type=int, default=25, help='Submission limit')
    parser.add_argument('-s', '--subreddit', nargs='+', help='Add subreddits to search')
    parser.add_argument('-v', '--verbosity', action='store_true', help='Print the changelog')
    args = parser.parse_args()
    verbose = args.verbosity
    if args.subreddit is not None:
        default_subreddits.update(args.subreddit)

    submissions = []
    for sub in default_subreddits:
        submissions += time.get(args.top, lambda x, y: x.get_top_from_day(limit=y))(reddit.get_subreddit(sub), args.num)
    scores = [post.score for post in submissions]
    scores.sort()
    # Median score determines the minimum score to retrieve images
    median_score = scores[len(scores) // 2] if len(scores) % 2 == 1 else (scores[(len(scores) // 2) - 1] + scores[
        len(scores) // 2]) // 2
    posts = list(filter(lambda x: x.score >= median_score, submissions))
    # Remove the certain characters that cannot be included in file names
    post_titles = list(map(lambda p: "".join(['' if is_bad_char(l) else l for l in list(p.title)]), posts))
    i = 0
    while i < len(post_titles):
        posts[i].title = post_titles[i]
        i += 1
    reject_files(get_files(posts), args.verbosity)
