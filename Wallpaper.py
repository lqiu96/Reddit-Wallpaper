import praw
import os
from urllib import urlretrieve
from PIL import Image

SUBREDDIT = ['earthporn', 'spaceporn']
DEFAULT_DIRECTORY = r'C:\Users\Lawrence\Pictures\Wallpapers\\'
FAIL_DIRECTORY = r'C:\Users\Lawrence\Pictures\Rejected Wallpapers\\'
MIN_RATIO, MAX_RATIO = 1.15, 1.6
user_agent = 'Wallpaper Retreiver 1.0 by /u/burstoflight'
reddit = praw.Reddit(user_agent=user_agent)

submissions = []
for sub in SUBREDDIT:
    submissions += reddit.get_subreddit(sub).get_top(limit=10)
posts = [post for post in submissions if post.score > 1000]
is_bad_char = lambda x: x in [':', ';', '<', '>', '"', '\\', '/', '|', '?', '*']
files = map(lambda x: x[0],
            [urlretrieve(post.url, '{}{}.png'.format(DEFAULT_DIRECTORY, filter(lambda x: not is_bad_char(x), post.title))) for post in posts])
for file in files:
    try:
        f = open(file, 'rb')
        image = Image.open(f)
        dimension = image.size
        f.close()
        width, height = dimension
        if not (MIN_RATIO < width * 1.0 / height < MAX_RATIO):
            file_name = file.replace(DEFAULT_DIRECTORY, '')
            os.rename(file, '{}{}.png'.format(FAIL_DIRECTORY, file_name))        
    except IOError:
        f.close()
        os.remove(file)
        print 'Removed: {}'.format(file)
