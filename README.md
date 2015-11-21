Indiegogo Camapign Monitor
=========

This script monitors your Indiegogo campaign and sends notifications to your [Slack](https://slack.com/) and [IFTTT](https://ifttt.com/) if something happens (e.g. new contributions, new comments, etc.).
In fact, it can monitor any Indiegogo campaign, not only yours!

I made it to share [my campaign information](https://www.indiegogo.com/projects/microbot-push-a-robotic-finger-for-your-buttons#/) with my team (I love automation). I hope you find it useful.
![Screenshot](https://raw.githubusercontent.com/thpark/indiegogo-to-ifttt/master/imgs/slack.png)

You can also integrate with IFTTT, which opens up a new world of possibilities.
* [![Indiegogo to Google Drive recipe](https://raw.githubusercontent.com/thpark/indiegogo-to-ifttt/master/imgs/ifttt-drive.png)](https://ifttt.com/recipes/343362-record-all-indiegogo-comments-to-google-drive)
* [![Indiegogo to Tweeter recipe](https://raw.githubusercontent.com/thpark/indiegogo-to-ifttt/master/imgs/ifttt-tweeter.png)](https://ifttt.com/recipes/343055-tweet-if-indiegogo-campaign-reaches-a-goal)
* [![Indiegogo to SMS recipe](https://raw.githubusercontent.com/thpark/indiegogo-to-ifttt/master/imgs/ifttt-sms.png)](https://ifttt.com/recipes/343099-send-me-sms-on-new-indiegogo-contribution)


# Use it as a web service
Please [visit here](http://official.myprota.com/#indiegogo).


# Use it on your computer (for advanced users)

## How to Set Up
Before you start, you will need Python on your computer (Python 2.7 or above), but you may not need to download it. If it's missing, you can [download Python here](https://www.python.org/downloads/release/python-2710/).
If your Python version is 2.7.9 or higher, pip must be installed on your computer already. If it's not, you can follow [the instruction here](http://pip.readthedocs.org/en/stable/installing/) to install it yourself.

Once you have Python and pip ready, go ahead and clone this repository or [download the archive](https://github.com/thpark/indiegogo-to-ifttt/archive/master.zip) and unzip it.

To configure, open a terminal window (or a command prompt on Windows) on the directory, and type in

    pip install -r requirements.txt
    python igg.py

If you don't know how to use a terminal, you can just double-click on one of the helper scripts (start.command for Mac, start.sh for others) to start it.

Once it's running, it will ask you to enter whatever is needed (e.g. API token, ID/PW, etc.) to monitor your campaign. I included some instructions on where and how to get them below.

### Indiegogo API Token
This is essential to make any request to the Indiegogo servers. You can get yours at [Indiegogo Developer Portal](http://developer.indiegogo.com/). I'm not sure if I can share mine, which is included in the script, so use it at your own risk.

### Slack URL
This is an [incoming webhook URL of your Slack channel](https://my.slack.com/services/new/incoming-webhook/). If you don't use Slack, leave it blank.

### IFTTT Maker Key
You will need this key to integrate with IFTTT. It's very straightforward to [create one here](https://ifttt.com/maker). Your key will be shown in the page.

![Screenshot](https://raw.githubusercontent.com/thpark/indiegogo-to-ifttt/master/imgs/ifttt-connect.png)
![Screenshot](https://raw.githubusercontent.com/thpark/indiegogo-to-ifttt/master/imgs/ifttt-connected.png)

### Campaign ID
Your campaign ID is sort of hidden, so you need to find it by yourself. This script helps you find your campaign by keywords. If you don't see yours there, you will have to contact [Indiegogo Support](https://support.indiegogo.com/).


## How to Use
To run it, just type in

    python igg.py

Once configuration is completed, you can execute/pause the script anytime (to stop it, CTRL-c). It will keep track of changes, so even if you stop it for a while, it will catch up when started.


### IFTTT Events
This script provides the following Maker events.

| EventName         | Ingredients | Description                     |
| ----              | :-------:   | ---------                       |
| igg-comments      | Value1      | Comment text                    |
|                   | Value2      | Direct link to the comment      |
|                   | Value3      | Commenter's avatar URL          |
| igg-contributions | Value1      | Message text - including perk label and contributor name   |
|                   | Value2      | Direct link to the contribution |
|                   | Value3      | Contributor's avatar URL        |
| igg-status        | Value1      | Status message text                |
|                   | Value2      | Preview URL of the campaign     |
|                   | Value3      | Campaign's thumbnail image URL  |
| igg-perks-status  | Value1      | Status message text                 |
|                   | Value2      | Preview URL of the campaign     |
|                   | Value3      | Campaign's thumbnail image URL  |

Note the `igg-status` will be triggered whenever your campaign reaches certain percentages (e.g. 30%, 100%, 200%, etc.). `igg-perks-status` will be triggered whenever one or more perks are running out or completely sold out.


### Example (IF new comment, THEN email to everyone)
1. Select EventName ([IFTTT Events])

    ![Screenshot](https://raw.githubusercontent.com/thpark/indiegogo-to-ifttt/master/imgs/ifttt-eventname.png)

2. Fill out email fields

    ![Screenshot](https://raw.githubusercontent.com/thpark/indiegogo-to-ifttt/master/imgs/ifttt-email-fields.png)

3. Done

    ![Screenshot](https://raw.githubusercontent.com/thpark/indiegogo-to-ifttt/master/imgs/ifttt-recipe.png)


## How to Reset
Just remove all json files.

    rm *.json


## Did you find it useful? [Maybe you can help us, too!](https://www.indiegogo.com/projects/microbot-push-a-robotic-finger-for-your-buttons#/)
Please let me know if you have any questions.
Good luck with your campaign!
