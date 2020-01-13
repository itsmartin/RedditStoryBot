# RedditStoryBot

This is a simple bot which checks for new submissions to a subreddit, and posts
a comment with a list of the submitter's other posts.

It was originally written to be used in [/r/gametales](http://reddit.com/r/gametales).

## Installation

1. Install PRAW, requests and PyYAML:
```bash
pip install -r requirements.txt
```
2. Create a config file in YAML format (start from `config.sample.yaml`)
3. Create a directory (anywhere you like) for the bot to store its persistent data in, and put the path to this in the
config file (as `data_path`)
4. Run the bot:
```bash
python -m storybot --post /path/to/config.yaml
```

Notes:

- The `--post` flag is required for the bot to actually post responses. If it is omitted then nothing will be posted to reddit; the bot will only output its comments to the console.
- `/path/to/config.yaml` should be replaced with the path to your config file
- You may find it useful to wrap your script call in a small shell script to ensure that it restarts if it crashes for any reason. Alternatively, you could run it in a docker container (see the next section).

## Running in a container

You can use the supplied `Dockerfile` to create a docker image for the package, if you prefer.

1. Build the image:
```bash
docker build --tag storybot .
```
2. Create a volume for the script to keep its database file(s):
```bash
docker volume create storybot_data
```
3. Launch the container:
```bash
# Replace `/path/to/config.yaml`with the path to your config file
docker run -d --name storybot \
    --mount type=volume,src=storybot_data,target=/data/storybot \
    --mount type=bind,src=/path/to/config.yaml,target=/etc/storybot.yaml \
    --restart=on-failure storybot
```

