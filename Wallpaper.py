import praw
import os
import os.path
import argparse
import requests
import shutil
from urllib.request import urlopen
from PIL import Image

DEFAULT_DIRECTORY = 'C:\\Users\\Lawrence\\Pictures\\Wallpapers\\'
FAIL_DIRECTORY = 'C:\\Users\\Lawrence\\Pictures\\Rejected Wallpapers\\'
MIN_RATIO, MAX_RATIO = 1.15, 1.6
FILE_LENGTH_LIMIT = 200
TIME = {
    'hour': lambda x, y: x.get_top_from_hour(limit=y),
    'day': lambda x, y: x.get_top_from_day(limit=y),
    'week': lambda x, y: x.get_top_from_week(limit=y),
    'month': lambda x, y: x.get_top_from_month(limit=y),
    'year': lambda x, y: x.get_top_from_year(limit=y),
    'all': lambda x, y: x.get_top_from_all(limit=y)
}


def is_bad_char(x):
    """Function that checks if a character cannot exist inside a file name

    Args:
    x: Char inside the file name

    Returns:
    True/ False if x contains a character that cannot be in a file name

    """
    return x in [':', ';', '<', '>', '"', '\\', '/', '|', '?', '!', '*']


def get_files(posts):
    """Function that that iterates through all the posts and downloads
    the image from the url. Each image from a post url is intially
    downloaded to the default directory.

    Args:
    posts: List of post objects containing the title and url of the post

    Returns:
    List of file names where the images are downloaded to

    """
    files = []
    for post in posts:
        # Certain imgur links do not open directly to the image
        if post.url.startswith('http://imgur.com') or post.url.startswith('https://imgur.com'):
            post.url += '.jpg'
        r = requests.get(post.url, stream=True)
        file_location = '{}{}.png'.format(DEFAULT_DIRECTORY, post.title)
        with open(file_location, 'wb') as out_file:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, out_file)
        files.append(file_location)
    return files


def reject_files(files, verbose):
    """Function that iterates through the location of each file and checks
    if the ration of the file's dimension match the required ratio. For desktop
    wallpapers, the default ratio is set between 1.15 and 1.6. If the file's ratio
    does not fall between the ration bounds, it moves the file to the rejected folder

    Args:
    files: List of file locations
    verbose: Bool to tell if program needs to print out when a file is rejected or passed

    Returns:
    None

    """
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
                rejected_file = '{}{}'.format(FAIL_DIRECTORY, file[38:])
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
    user_agent = 'Wallpaper Retreiver 1.2 by /u/burstoflight'
    reddit = praw.Reddit(user_agent=user_agent)
    parser = argparse.ArgumentParser(description='Retrieve Wallpapers from Reddit')
    parser.add_argument('-t', '--top', default='day', choices=['hour', 'day', 'week', 'month', 'year', 'all'],
                        help='Choice time-frame for top submissions')
    parser.add_argument('-n', '--num', type=int, default=25, help='Submission limit')
    parser.add_argument('-s', '--subreddit', nargs='+', help='Add subreddits to search')
    parser.add_argument('-v', '--verbosity', action='store_true', help='Print the changelog')
    parser.add_argument('-c', '--check', help='Check through the files to make sure each is within the ratio')
    parser.add_argument('-p', '--passdir', help='Directory where passed wallpapers go')
    parser.add_argument('-f', '--faildir', help='Directory where failed wallpapers go')
    args = parser.parse_args()
    verbose = args.verbosity
    # Adds any additional subreddits not already suggested
    if args.subreddit is not None:
        default_subreddits.update(args.subreddit)
    if args.passdir is not None and os.path.isdir(args.passdir):
        DEFAULT_DIRECTORY = args.passdir
    if args.faildir is not None and os.path.isdir(args.faildir):
        FAIL_DIRECTORY = args.faildir

    submissions = []
    for sub in default_subreddits:
        submissions += TIME.get(args.top, lambda x, y: x.get_top_from_day(limit=y))(reddit.get_subreddit(sub), args.num)
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
        posts[i].title = post_titles[i][:FILE_LENGTH_LIMIT]
        i += 1
    reject_files(get_files(posts), args.verbosity)
    if args.check:
        reject_files(os.listdir(DEFAULT_DIRECTORY), args.verbosity)
