import praw
import os
from urllib import urlretrieve
from PIL import Image

SUBREDDIT = 'earthporn'
DEFAULT_DIRECTORY = 'C:\Users\Lawrence\Pictures\Saved Pictures\\'
MIN_RATIO, MAX_RATIO = 1.25, 1.5
user_agent = 'Wallpaper Retreiver 1.0 by /u/burstoflight'
reddit = praw.Reddit(user_agent=user_agent)
submissions = reddit.get_subreddit(SUBREDDIT).get_top(limit=5)
urls = [str(post.url) for post in submissions if post.score > 1000]
files = map(lambda x: x[0],
            [urlretrieve(url, '{}{}.png'.format(DEFAULT_DIRECTORY, i + 1)) for i, url in enumerate(urls)])
for file in files:
    dimension = Image.open(file).size
    width, height = dimension
    print width, height
    if not (MIN_RATIO < width * 1.0 / height < MAX_RATIO):
        os.remove(file)
