import praw
import logging
import time
import random
import requests
import yaml
from pathlib import Path
from .version import __version__
from . import db, exceptions


USER_AGENT = "StoryBot " + __version__
REDDIT_MAX_POST_LENGTH = 10000

class StoryBot:
    """A reddit bot to post links to previous submissions by a user, intended
    for use on 'story' subreddits.

    This bot was written for /r/gametales, and took inspiration from
    https://github.com/Bakkes/BeetusBot/.
    """

    def __init__(self, post_mode: bool, config_file: Path):
        """Initialise the bot"""

        self.post_mode = post_mode

        # Set up logging to the console

        self.logger = logging.getLogger(__file__)
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logging.DEBUG)
        consoleHandler.setFormatter(formatter)
        self.logger.addHandler(consoleHandler)

        self.logger.info("Initialising bot")

        # Load config
        with open(config_file) as cf:
            self.config = yaml.safe_load(cf)

        # Do some sanity checks on config values
        assert len(self.config["new_submitter_response_templates"]) > 0
        assert len(self.config["response_templates"]) > 0

        # Get our data path
        self.data_path = Path(self.config["data_path"])
        assert self.data_path.is_dir()

        # Connect to the submission tracker
        self.handled_submissions = db.HandledItemTracker(self.data_path / 'handled.db')

        # Connect to reddit
        self.reddit = praw.Reddit(client_id=self.config["client_id"],
                                  client_secret=self.config["client_secret"],
                                  password=self.config["password"],
                                  user_agent=USER_AGENT,
                                  username=self.config["username"])

        self.subreddit = self.reddit.subreddit(self.config["subreddit"])

    def run(self):
        """The main loop. Runs all of the bot's actions at the configured
        interval.
        """
        while True:
            try:
                self.check_new_submissions()
            except requests.exceptions.HTTPError:
                self.logger.exception("Failed to check for new submissions")

            self.logger.info(f"Finished; sleeping for {self.config['sleep_time']} minute(s)")
            time.sleep(self.config["sleep_time"] * 60)

    def check_new_submissions(self):
        """Check the given subreddit for new posts which haven't yet been
        handled, and handles any that are found.
        """

        self.logger.info(f"Checking newest {self.config['new_limit']} submissions in {self.subreddit}...")

        recent_submissions = list(self.subreddit.new(limit=self.config["new_limit"]))

        for i, s in enumerate(recent_submissions):
            self.logger.info(f"({i+1}/{len(recent_submissions)}) https://redd.it/{s.id}: '{s.title}' by {s.author}")
            try:
                self.handle_submission(s)
            except exceptions.PostIgnored as e:
                self.logger.info(f"Submission ignored: {e}")
            except praw.exceptions.APIException:
                self.logger.exception("Failure when handling submission")

    def handle_submission(self, submission) -> None:
        """Handle a submission and respond to it"""

        # Ignore submission if flair is in the ignore list
        if submission.link_flair_css_class in self.config["flairs_to_ignore"]:
            raise exceptions.PostIgnored(f"flair {submission.link_flair_css_class} is ignored")

        # Ignore submission if it's marked as handled
        if submission.id in self.handled_submissions:
            raise exceptions.PostIgnored("already handled")

        # Ignore submission if we have already responded
        if any(c.author == self.reddit.user.me() for c in submission.comments):
            raise exceptions.PostIgnored(f"already has a response from /u/{self.reddit.user.me()}")

        # Search for other submissions by the same author
        other_stories = [self.config["response_entry"].format(title=s.title, permalink=s.permalink, score=s.score)
                         for s in self.get_other_submissions(submission.author, submission.id)]

        self.logger.info(f"Found {len(other_stories)} other post(s) by {submission.author}")

        # Prepare subsitution values for template variables
        substitutions = {
            "author": str(submission.author),
            "botname": self.config["username"],
            "subreddit": self.config["subreddit"]
        }

        # Pick a template and substitute in the list of other submissions
        if other_stories:
            template = random.choice(self.config["response_templates"])
        else:
            template = random.choice(self.config["new_submitter_response_templates"])

        # Set up random selections for any custom responses in the template
        for key, value in self.config["response_substitutions"].items():
            if type(value) in (tuple, list):
                value = random.choice(value)
            substitutions[key] = value

        # Make the substitutions and post
        substitutions['list'] = "\n".join(other_stories)

        reply = template.format(**substitutions)

        removed_count = 0
        while len(reply) > REDDIT_MAX_POST_LENGTH:
            # We have a problem; this is too long to post. Remove a story and try again.
            try:
                other_stories.pop()
            except IndexError:
                raise exceptions.PostIgnored("my comment was too long for reddit, even after all stories were removed")
            removed_count += 1
            substitutions['list'] = "\n".join(other_stories) + "\n" + self.config['response_too_long'].format(count=removed_count)
            reply = template.format(**substitutions)

        self.logger.debug(reply)

        if self.post_mode:
            # Send our reply
            comment = submission.reply(reply)
            self.logger.info(f"Response posted at {comment.permalink}")

            # Mark submission as handled
            self.handled_submissions.add(submission.id)

        else:
            self.logger.info("Response not posted because --post was not specified at startup")


    def get_other_submissions(self, author, original_id):
        """Returns a generator which yields all submissions by the given author, excluding the one with id = original_id
        """

        return (s for s in self.subreddit.search(f"author:{author}", limit=None)
                if s.link_flair_css_class not in self.config["flairs_to_ignore"] and s.id != original_id)
