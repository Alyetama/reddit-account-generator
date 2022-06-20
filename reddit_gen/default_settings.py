#!/usr/bin/env python
# coding: utf-8


class ResetSettings:
    reset = False


class DefaultSettings:
    lang = "en"
    no_profanity = True  # hide images for NSFW/18+ content
    video_autoplay = False  # Autoplay Reddit videos on the desktop comments
    # page
    newwindow = False  # open links in a new window
    show_trending = False  # show trending subreddits on the home feed
    clickgadget = False  # show me links I've recently viewed
    compress = False  # compress the link display
    domain_details = False  # show additional details in the domain text
    # when available
    hide_ups = False  # don't show me submissions after I've upvoted them
    hide_downs = False  # don't show me submissions after I've downvoted them
    min_link_score = -4  # leave blank to show all
    numsites = 25  # [10, 25, 50, 100]
    ignore_suggested_sort = False  # ignore suggested sorts
    highlight_controversial = False  # show a dagger (†) on comments voted
    # controversial
    min_comment_score = -4  # leave blank to show all
    num_comments = 200  # 1-500
    default_comment_sort = "best (recommended)"  # sort comments by
    threaded_messages = True  # show message conversations in the inbox
    collapse_read_messages = False  # collapse messages after I've read them
    mark_messages_read = True  # mark messages as read when I open my inbox
    monitor_mentions = True  # notify me when people say my username
    send_welcome_messages = False  # receive welcome messages from
    # moderators when I join a community
    threaded_modmail = False  # enable threaded modmail display
    live_orangereds = False  # send message notifications in my browser
    disable_browser_notifs = True  # disable all browser notifications
    email_messages = False  # send messages as emails
    email_digests = False  # send email digests
    email_unsubscribe_all = True  # unsubscribe from all emails
    show_stylesheets = False  # allow subreddits to show me custom themes
    show_flair = False  # show user flair
    show_link_flair = True  # show link flair
    legacy_search = False  # show legacy search page
    over_18 = True  # I am over eighteen years old and willing to view adult
    # content
    label_nsfw = True  # label posts that are not safe for work (NSFW)
    search_include_over_18 = True  # include not safe for work (NSFW) search
    # results in searches
    private_feeds = False  # enable private RSS feeds
    public_votes = False  # make my votes public
    research = False  # allow my data to be used for research purposes
    hide_from_robots = True  # don't allow search engines to index my user
    # profile
    allow_clicktracking = False  # allow reddit to log my outbound clicks
    # for personalization
    show_presence = False  # let others see my online status
    beta = False  # I would like to beta test features for reddit
    in_redesign_beta = False  # Use new Reddit as my default experience
