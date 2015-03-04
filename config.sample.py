# Configuration for RedditStoryBot

# This value determines whether the bot will actually post, or just log what it
# would have posted to the console. Change this to True only when you're happy
# with the bot's output.
actuallyPost = False

# The name of the subreddit that the bot will run on:
subreddit = u"bottesting"

# How many posts in /r/subreddit/new will the bot go back, every time it runs?
newLimit = 20

# Username and password that the bot will use to log in to reddit:
username = u"username"
password = u"password"

# The user agent that the bot will identify itself as:
userAgent = "RedditStoryBot"

# Names for the bot's log and database files (change these if you plan to
# run multiple bots in the same folder):
logFile = "RedditStoryBot.log"
databaseFile = "RedditStoryBot.db"

# The identifier the bot will use when logging events
logId = "RedditStoryBot"

# How long the bot should sleep between runs (in seconds). (600 = 10 minutes)
sleepTime = 600

# A list of flairs which the bot will ignore. Include None if you want the bot
# to ignore unflaired posts too. Leave this empty if the bot should handle all
# posts.
flairsToIgnore = ()

# The templates for the bot's response. It should be a list of possible response
# formats, one of which (randomly chosen) will be posted by the bot. Each
# response format must include the following formatting placeholders:
#
# {list} - will be replaced by the actual list of posts
# {author} - will be replaced by the author's username
#
# In this example, there is only one template.
responseTemplates = [u"""**Previous stories by /u/{author}:**

{list}

**[Search for more by {author}](http://www.reddit.com/r/""" + subreddit + u"""/search?q=author%3A{author}&sort=new&restrict_sr=on)**

---
^(Hello. I am """ + username + u""". For more information about me, please send me a) ^[message](/u/""" + username +""")."""]


# The template for each entry in the list of recent posts.
#
# {title} - will be replaced with the post's title.
# {permalink} - will be replaced with the post's URL.
# {score:d} - will be replaced with the posts's current score
responseEntry = u"* [{title}]({permalink}) ^(({score:d} points)^)"


# The templates for the bot's response to submitters with no prior posts. This
# works the same as responseTemplates above, except that the {list} placeholder
# is not used.
#
# In this example, there is only one template.
newSubmitterResponseTemplates = [u"""**/u/{author} has no previous stories right now**. If you're from the future, you can **[search for more by {author}](http://www.reddit.com/r/""" + subreddit + u"""/search?q=author%3A{author}&sort=new&restrict_sr=on)**

---
^(Hello. I am """ + username + u""". For more information about me, please send me a) ^[message](/u/""" + username +""")."""]
