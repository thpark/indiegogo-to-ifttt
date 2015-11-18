# -*- coding: utf-8 -*-
#  __    _ _______ ______   _______ __    _
# |  |  | |   _   |    _ | |   _   |  |  | |
# |   |_| |  |_|  |   | || |  |_|  |   |_| |
# |       |       |   |_||_|       |       |
# |  _    |       |    __  |       |  _    |
# | | |   |   _   |   |  | |   _   | | |   |
# |_|  |__|__| |__|___|  |_|__| |__|_|  |__|


"""Indiegogo notifier (Slack & IFTTT).

Author: Taehyun Park (taehyun@thenaran.com)
"""


import logging
import requests
import json
from tinydb import TinyDB, where
import time
import iso8601
import getpass
import subprocess


BASE_URL = 'https://api.indiegogo.com/1.1'
DB = TinyDB('data.json')

try:
    # Read configurations
    with open('config.json', 'r') as f:
        CONFIGS = json.loads(f.read())
except:
    CONFIGS = {}


def get_campaign_info():
    payload = {'api_token': CONFIGS['api_key'],
               'access_token': CONFIGS['access_token'],
              }
    resp = requests.get(
        '{base}/campaigns/{ident}.json'.format(base=BASE_URL,
                                               ident=CONFIGS['campaign_id']),
        params=payload)
    result = json.loads(resp.text)
    return result['response']


def get_perks_info():
    payload = {'api_token': CONFIGS['api_key'],
               'access_token': CONFIGS['access_token'],
               }
    resp = requests.get(
        '{base}/campaigns/{ident}/perks.json'.format(base=BASE_URL,
                                                     ident=CONFIGS['campaign_id']),
        params=payload)
    result = json.loads(resp.text)
    return result['response']


def new_comments(last_ts):
    page = 1
    go = True
    while go:
        payload = {'api_token': CONFIGS['api_key'],
                   'access_token': CONFIGS['access_token'],
                   'page': page}
        page += 1
        logging.info("comments on page %s", page)
        resp = requests.get(
            '{base}/campaigns/{ident}/comments.json'.format(base=BASE_URL,
                                                            ident=CONFIGS['campaign_id']),
            params=payload)
        result = json.loads(resp.text)
        if not result['response']:
            break
        for comment in result['response']:
            created_ts = _convert_to_ts(comment['created_at'])
            if last_ts >= created_ts:
                go = False
                break
            yield comment


def new_contribs(last_ts):
    page = 1
    go = True
    while go:
        payload = {'api_token': CONFIGS['api_key'],
                   'access_token': CONFIGS['access_token'],
                   'page': page}
        page += 1
        resp = requests.get(
            '{base}/campaigns/{ident}/contributions.json'.format(base=BASE_URL,
                                                                 ident=CONFIGS['campaign_id']),
            params=payload)
        result = json.loads(resp.text)
        if not result['response']:
            break
        for contrib in result['response']:
            created_ts = _convert_to_ts(contrib['created_at'])
            if last_ts >= created_ts:
                go = False
                break
            yield contrib


def all_campaigns():
    page = 1
    while True:
        payload = {'api_token': CONFIGS['api_key'],
                   'access_token': CONFIGS['access_token'],
                   'page': page}
        logging.info("On page %s.", page)
        page += 1
        resp = requests.get('{base}/campaigns.json'.format(base=BASE_URL), params=payload)
        result = json.loads(resp.text)
        if not result['response']:
            break
        for campaign in result['response']:
            yield campaign


def search_campaigns(terms, max_page=10, only_mine=True):
    page = 1
    while True:
        payload = {'api_token': CONFIGS['api_key'],
                   'access_token': CONFIGS['access_token'],
                   'title': terms,
                   'sort': only_mine and 'new' or 'popular_all',
                   'page': page
                   }
        logging.info("On page %s.", page)
        page += 1
        if page > max_page:
            break
        resp = requests.get('{base}/search/campaigns.json'.format(base=BASE_URL), params=payload)
        result = json.loads(resp.text)
        if not result['response']:
            break
        for campaign in result['response']:
            for member in campaign['team_members']:
                if not only_mine or member['account_id'] == CONFIGS['account_id']:
                    yield campaign
                    break


def get_current_account():
    payload = {'api_token': CONFIGS['api_key'],
               'access_token': CONFIGS['access_token']
               }
    resp = requests.get('{base}/me.json'.format(base=BASE_URL), params=payload)
    result = json.loads(resp.text)
    return result['response']


def get_account_info(ident):
    payload = {'api_token': CONFIGS['api_key'],
               'access_token': CONFIGS['access_token']
               }
    url = '{base}/accounts/{ident}.json'.format(base=BASE_URL, ident=ident)
    resp = requests.get(url, params=payload)
    result = json.loads(resp.text)
    return result['response']


def check_now():
    try:
        _check_comments()
    except KeyboardInterrupt:
        raise
    except:
        logging.exception("Failed to check comments.")
    try:
        _check_contribs()
    except KeyboardInterrupt:
        raise
    except:
        logging.exception("Failed to check contributions.")
    try:
        _check_campaign_status()
    except KeyboardInterrupt:
        raise
    except:
        logging.exception("Failed to check campaign status.")
    try:
        _check_perks_status()
    except KeyboardInterrupt:
        raise
    except:
        logging.exception("Failed to check perks status.")


def write_to_slack(pretext, text, color, fields=None):
    """Write the text to the Slack channel.
    """
    if 'slack_url' not in CONFIGS or not CONFIGS['slack_url']:
        logging.info("Slack URL not configured.")
        return
    payload = {
        'pretext': pretext,
        'text': text,
        'color': color,
        'fields': fields,
        'parse': 'full'
    }
    try:
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        requests.post(CONFIGS['slack_url'], data=json.dumps(payload), headers=headers)
    except:
        logging.info("Failed to write to slack.", exc_info=True)


def notify_ifttt(event, text, link, image):
    """Make a HTTP request to the IFTTT Maker channel.
    """
    if 'ifttt_maker_key' not in CONFIGS:
        logging.info("IFTTT not configured.")
        return
    payload = {
        'value1': text,
        'value2': link,
        'value3': image
    }
    url = 'https://maker.ifttt.com/trigger/{event}/with/key/{key}'.format(
        event=event,
        key=CONFIGS['ifttt_maker_key'])
    try:
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        requests.post(url, data=json.dumps(payload), headers=headers)
    except:
        logging.info("Failed to notify IFTTT.", exc_info=True)


def start():
    """Start monitoring the Indiegogo campaign.
    """
    # Retrieve the current campaign information
    campaign = get_campaign_info()
    CONFIGS['slug'] = campaign['slug']
    CONFIGS['campaign_id'] = campaign['id']
    CONFIGS['campaign_preview_url'] = campaign['preview_url']
    CONFIGS['campaign_thumbnail_image_url'] = campaign['thumbnail_image_url']
    # Initialize timestamps
    last_comment_ts = DB.search(where('type') == 'comment')
    if not last_comment_ts:
        DB.insert({'ts': 0, 'type': 'comment'})
    last_contrib_ts = DB.search(where('type') == 'contrib')
    if not last_contrib_ts:
        DB.insert({'ts': 0, 'type': 'contrib'})
    # Insert markers for each campaign goal
    goal = campaign['goal']
    funds = campaign['collected_funds']
    achieved = int(funds * 100 / goal)
    for i in [30, 70, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]:
        # notify at each achievement
        p = 'p' + str(i)
        marker = DB.search(where('type') == p)
        if not marker and achieved >= i:
            DB.insert({'ts': time.time(), 'type': p})
    update_interval = CONFIGS['update_interval']
    print "Start monitoring..."
    try:
        while True:
            check_now()
            time.sleep(update_interval)
    except:
        pass
    print "Monitoring stopped."


def ftl():
    """Initializer.
    """
    print "Indiegogo Campaign Monitor v0.1 (by taehyun@thenaran.com)"
    print
    api_key = raw_input("Enter your Indiegogo API key [press enter to use the default]: ")
    if not api_key:
        api_key = 'ce450f4a26ed1b72136d58cd73fd38441e699f90aee8b7caacd0f144ad982a98'
    slack_url = raw_input("Enter your Slack URL (default: none): ")
    ifttt_maker_key = _prompt_required("Enter your IFTTT maker key (required): ", "Please enter valid one: ")
    update_interval = raw_input("Input update interval in seconds [default: 60]: ")
    try:
        update_interval = int(update_interval)
    except:
        logging.warn("Setting the update interval to 60 seconds.")
        update_interval = 60

    # Sync configurations
    data = {
        'api_key': api_key,
        'slack_url': slack_url,
        'ifttt_maker_key': ifttt_maker_key,
        'update_interval': update_interval
    }
    CONFIGS.update(data)

    print
    authenticate()

    print
    print "Please enter a campaign ID. If you don't know what it is, type in keywords which would find the campaign."
    campaign_id = _prompt_required("Input campaign ID or keywords: ", "Please enter valid one: ")
    try:
        campaign_id = int(campaign_id)
    except:
        only_mine = _prompt_yes_no("Is it your campaign", default_yes=False)
        terms = campaign_id
        found = False
        while not found:
            for campaign in search_campaigns(terms, max_page=10, only_mine=only_mine):
                print
                print '[{title}]'.format(title=campaign['title'])
                yes = _prompt_yes_no("Select this one", default_yes=False)
                if yes:
                    campaign_id = campaign['id']
                    found = True
                    break
            if not found:
                print
                terms = _prompt_required("Please use different keywords: ", "Please enter valid one: ")
                only_mine = _prompt_yes_no("Is it your campaign", default_yes=False)
    CONFIGS['campaign_id'] = campaign_id
    data['campaign_id'] = campaign_id
    s = json.dumps(data)
    with open('config.json', 'w') as f:
        f.write(s)

    print
    print "Do you want to sync all comments and contributions from the beginning? If no, it will ignore existing ones and only start keeping track of them from now on. The campaign status and the perks status will be synced regardless of the choice."
    yes = _prompt_yes_no("Do you want to sync them", default_yes=False)
    if not yes:
        # Insert the current timestamp so that it would ignore the existing comments and contributions.
        DB.insert({'ts': time.time(), 'type': 'comment'})
        DB.insert({'ts': time.time(), 'type': 'contrib'})


def authenticate():
    access_token = DB.search(where('type') == 'access_token')
    if not access_token:
        ident = _prompt_required('Indiegogo ID (email): ', 'Please enter your Indiegogo ID (email): ')
        password = getpass.getpass('Password: ')
        output = subprocess.check_output('curl -ss -X POST -d grant_type=password -d credential_type=email -d email={email} -d password={password} https://auth.indiegogo.com/oauth/token'.format(email=ident, password=password), shell=True)
        tokens = json.loads(output)
        DB.insert({'value': tokens['access_token'], 'type': 'access_token'})
        DB.insert({'value': tokens['refresh_token'], 'type': 'refresh_token'})
        CONFIGS['access_token'] = tokens['access_token']
        CONFIGS['refresh_token'] = tokens['refresh_token']
        print "Authentication successful."
    else:
        CONFIGS['access_token'] = access_token[0]['value']
        refresh_token = DB.search(where('type') == 'refresh_token')
        CONFIGS['refresh_token'] = refresh_token[0]['value']
    me = get_current_account()
    CONFIGS['account_id'] = me['id']


def _check_comments():
    last_comment_ts = DB.search(where('type') == 'comment')[0]['ts']
    comments = [c for c in new_comments(last_comment_ts)]
    if len(comments) > 0:
        comment_ts = _convert_to_ts(comments[0]['created_at'])
        if last_comment_ts != comment_ts:
            DB.update({'ts': comment_ts}, where('type') == 'comment')
        for comment in reversed(comments):
            # notify in slack
            write_to_slack('New comment',
                           comment['text'].replace('\n', '\\n').replace('\r', ''),
                           'warn')
            # notify IFTTT:
            #   value1 : comment text
            #   value2 : direct link to the comment
            #   value3 : avatar url of the commenter
            notify_ifttt('igg-comments',
                         comment['text'],
                         _build_comments_url(comment['id']),
                         comment['account']['avatar_url'])
    else:
        logging.info("No new comments.")


def _check_contribs():
    last_contrib_ts = DB.search(where('type') == 'contrib')[0]['ts']
    contribs = [c for c in new_contribs(last_contrib_ts)]
    if len(contribs) > 0:
        contrib_ts = _convert_to_ts(contribs[0]['created_at'])
        if last_contrib_ts != contrib_ts:
            DB.update({'ts': contrib_ts}, where('type') == 'contrib')
        for contrib in reversed(contribs):
            if not contrib['perk']:
                # Contributed without selecting any perk
                contrib['perk'] = {'label': 'No perk'}
            # notify in slack
            write_to_slack('New contribution!',
                           contrib['perk']['label'],
                           'good',
                           [
                               {
                                   'title': 'Name',
                                   'value': contrib['by'],
                                   'short': False
                               },
                               {
                                   'title': 'Value',
                                   'value': '$' + str(contrib['amount']),
                                   'short': False
                               }
                           ])
            # notify IFTTT:
            #   value1 : perk text
            #   value2 : direct link to the contributor
            #   value3 : avatar url of the contributor
            notify_ifttt('igg-contributions',
                         '{contrib} claimed by {who} for ${amount}'.format(
                             contrib=contrib['perk']['label'],
                             who=contrib['by'],
                             amount=contrib['amount']),
                         _build_contrib_url(contrib['id']),
                         contrib['avatar_url'])
    else:
        logging.info("No new contributions yet.")


def _check_campaign_status():
    campaign = get_campaign_info()
    goal = campaign['goal']
    funds = campaign['collected_funds']
    achieved = int(funds * 100 / goal)
    for i in [30, 70, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]:
        # notify at each achievement
        p = 'p' + str(i)
        marker = DB.search(where('type') == p)
        if not marker and achieved >= i:
            DB.insert({'ts': time.time(), 'type': p})
            msg = '"{title}" reached {achieved}%: ${funds}'.format(
                title=campaign['title'],
                achieved=achieved,
                funds=funds)
            # notify in slack
            write_to_slack('Campaign updates', msg, 'good')
            # notify IFTTT:
            #   value1 : message
            #   value2 : direct link to the campaign
            #   value3 : thumbnail of the campaign
            notify_ifttt('igg-status',
                         msg,
                         CONFIGS['campaign_preview_url'],
                         CONFIGS['campaign_thumbnail_image_url'])
            return


def _check_perks_status():
    perks = get_perks_info()
    for perk in perks:
        claimed = perk['number_claimed']
        available = perk['number_available']
        if available and claimed != available and claimed + 10 >= available:
            p = 'soldout-' + str(perk['id'])
            marker = DB.search(where('type') == p)
            if not marker:
                DB.insert({'ts': time.time(), 'type': p})
                # notify that it's sold out!
                write_to_slack('Sold-out warning.',
                               perk['label'] + ' is almost sold out. @channel',
                               'danger',
                               [
                                   {
                                       'title': 'Claimed',
                                       'value': perk['number_claimed'],
                                       'short': False
                                   },
                                   {
                                       'title': 'Availability',
                                       'value': perk['number_available'],
                                       'short': False
                                   }
                               ])
                # notify IFTTT:
                #   value1 : message
                #   value2 : direct link to the campaign
                #   value3 : thumbnail of the campaign
                notify_ifttt('igg-perks-status',
                             '{perk} is almost sold out. - {claimed}/{available}'.format(perk=perk['label'],
                                                                                         claimed=perk['number_claimed'],
                                                                                         available=perk['number_available']),
                             CONFIGS['campaign_preview_url'],
                             CONFIGS['campaign_thumbnail_image_url'])
        elif available and claimed >= available:
            p = 'almost-' + str(perk['id'])
            marker = DB.search(where('type') == p)
            if not marker:
                DB.insert({'ts': time.time(), 'type': p})
                # notify that it's almost sold out!
                write_to_slack('Sold-out warning.',
                               perk['label'] + ' is sold out!! @channel',
                               'danger',
                               [
                                   {
                                       'title': 'Claimed',
                                       'value': perk['number_claimed'],
                                       'short': False
                                   },
                                   {
                                       'title': 'Availability',
                                       'value': perk['number_available'],
                                       'short': False
                                   }
                               ])
                # notify IFTTT:
                #   value1 : message
                #   value2 : direct link to the campaign
                #   value3 : thumbnail of the campaign
                notify_ifttt('igg-perks-status',
                             '{perk} is completely sold out. - {claimed}/{available}'.format(perk=perk['label'],
                                                                                         claimed=perk['number_claimed'],
                                                                                         available=perk['number_available']),
                             CONFIGS['campaign_preview_url'],
                             CONFIGS['campaign_thumbnail_image_url'])


def _convert_to_ts(s):
    d = iso8601.parse_date(s)
    return time.mktime(d.timetuple())


def _build_comments_url(ident):
    return 'https://www.indiegogo.com/projects/{slug}/x/{account_id}#/comments?id={ident}'.format(
        slug=CONFIGS['slug'],
        account_id=CONFIGS['account_id'],
        ident=ident)


def _build_contrib_url(ident):
    return 'https://www.indiegogo.com/command_center/{slug}#/contributions/{ident}'.format(
        slug=CONFIGS['slug'],
        ident=ident)


def _prompt_required(msg, retry_msg):
    ret = raw_input(msg)
    while not ret:
        ret = raw_input(retry_msg)
    return ret


def _prompt_yes_no(question, default_yes=True):
    yes = raw_input("{question} {yes_no}? ".format(question=question,
                                                   yes_no=default_yes and '(YES/no)' or '(yes/NO)'))
    yes = yes.strip().lower()
    if yes == 'yes' or yes == 'y':
        return True
    elif yes == 'no' or yes == 'n':
        return False
    else:
        return default_yes


if __name__ == '__main__':
    #logging.getLogger().setLevel(logging.INFO)
    if len(CONFIGS) == 0:
        ftl()
    else:
        authenticate()
    start()
