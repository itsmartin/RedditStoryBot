#!/usr/bin/env python3

import praw, logging, config, sqlite3, time, random, urllib, requests

class RedditStoryBot:
    """A reddit bot to post links to previous submissions by a user, intended
    for use on 'story' subreddits.

    This bot was written for /r/gametales, and took inspiration from
    https://github.com/Bakkes/BeetusBot/.
    """

    def __init__(self):
        """Initialise the bot"""

        self._initLogging()
        self._initDatabase()
        self._initReddit()


    def _initLogging(self):
        """Create a local logging object which will log to console and file"""

        self.log = logging.getLogger(config.logId)
        self.log.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        fileHandler = logging.FileHandler(config.logFile)
        fileHandler.setLevel(logging.DEBUG)
        fileHandler.setFormatter(formatter)
        self.log.addHandler(fileHandler)

        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logging.ERROR)
        consoleHandler.setFormatter(formatter)
        self.log.addHandler(consoleHandler)

        self.log.info("Initialising bot")


    def _initDatabase(self):
        """Set up a connection to the database, creating it if required"""

        self.database = sqlite3.connect(config.databaseFile)
        c = self.database.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS handled(id TEXT PRIMARY KEY)')
        self.database.commit()


    def _initReddit(self):
        """Set up PRAW objects for reddit and the appropriate subreddit, and
        log in.
        """
        self.reddit = praw.Reddit(user_agent = config.userAgent)
        self.subreddit = self.reddit.get_subreddit(config.subreddit)

        self.reddit.login(config.username,config.password)


    def main(self):
        """The main loop. Runs all of the bot's actions at the configured
        interval.
        """
        while True:
            try:
                self.checkNewSubmissions(self.subreddit)
            except requests.exceptions.HTTPError as err:
                self.log.error("HTTP error occurred: {}".format(str(err)))

            self.log.debug("Sleeping for {} seconds".format(config.sleepTime))
            time.sleep(config.sleepTime)


    def checkNewSubmissions(self, subreddit):
        """Check the given subreddit for new posts which haven't yet been
        handled, and handles any that are found.
        """

        self.log.info("Checking for new submissions in {subreddit}"
                .format(subreddit = subreddit.display_name))

        for submission in subreddit.get_new(limit=config.newLimit):
            self.log.debug(
                    "Found submission {id} ({cssClass}): \"{title}\", by {author}"
                    .format(
                            id = submission.id,
                            cssClass = submission.link_flair_css_class,
                            title = submission.title,
                            author = submission.author.name))

            if submission.link_flair_css_class in config.flairsToIgnore:
                self.log.debug(
                        "Submission {} ignored due to flair"
                        .format(submission.id))

            elif self.checkHandled(submission):
                self.log.debug(
                        "Submission {} already handled"
                        .format(submission.id))

            elif self.checkForBotComment(submission):
                self.log.debug(
                        "Submission {} ignored - bot comment found"
                        .format(submission.id))

            else:
                if self.processSubmission(submission):
                    self.markHandled(submission)


    def checkForBotComment(self, submission):
        """Returns true if the submission has a comment from this bot's
        configured username
        """

        for comment in submission.comments:
            if (comment.author is not None
                    and comment.author.name == config.username):
                return True

        return False


    def processSubmission(self, submission):
        """Process a submission and respond to it."""

        others = self.getOtherSubmissions(
                submission.author.name,
                submission.subreddit,
                submission.id)

        self.log.info("For submission {id} by {author}, I found {n} others".format(
                    id = submission.id,
                    n = len(others),
                    author = submission.author))

        substitutions = {
                'author': submission.author.name,
                'botname': config.username,
                'subreddit': config.subreddit
        }

        if others:
            if len(config.responseTemplates) > 0:
                template = random.choice(config.responseTemplates)

                substitutions['list'] = '\n'.join(
                        [config.responseEntry.format(
                        title = s.title,
                        permalink = s.permalink,
                        score = s.score) for s in others]
                )

            else:
                self.log.info("No template found, not posting.")
                return

        else:
            if len(config.newSubmitterResponseTemplates) > 0:
                template = random.choice(config.newSubmitterResponseTemplates)
            else:
                self.log.info("No template found, not posting.")
                return

        for key, value in config.responseSubstitutions.items():
            if type(value) in (tuple, list):
                value = random.choice(value)
            substitutions[key]=value

        reply = template.format_map(substitutions)

        self.log.info("Posting response to {}".format(submission.id))

        if (config.actuallyPost):
            try:
                submission.add_comment(reply)
                self.log.info("Posted")
                return True
            except praw.errors.RateLimitExceeded:
                self.log.info("Posting failed, rate limit exceeded")
                return False
            except praw.errors.APIException as err:
                if hasattr(err, "error_type") and err.error_type == 'TOO_OLD':
                    self.log.info("APIException: TOO_OLD")
                else:
                    self.log.info("APIException: Other")
                return False
        else:
            print("--- Response to https://redd.it/{} ---\n{}\n\n".format(submission.id, reply))
            return True


    def getOtherSubmissions(self, author, subreddit, originalId):
        """Returns all submissions by the given author in the given
        subreddit, excluding the one with id = originalId
        """

        submissions = []

        for other in subreddit.search("author:" + author,limit=None):
            if other.link_flair_css_class not in config.flairsToIgnore and other.id != originalId:
                submissions.append(other)

        return submissions


    def markHandled(self, submission):
        """Mark the given submission as handled"""

        c = self.database.cursor()
        c.execute("INSERT INTO handled VALUES (?)", (submission.id,))
        self.database.commit()


    def checkHandled(self, submission):
        """Check if the given submission is handled"""

        self.log.debug("Checking if {} is handled".format(submission.id))

        c = self.database.cursor()
        c.execute("SELECT COUNT(*) FROM handled WHERE id=?", (submission.id,))
        (count,) = c.fetchone()

        return count > 0


if __name__ == "__main__":
    RedditStoryBot().main()
