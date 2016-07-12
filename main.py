# -*- coding: utf-8 -*-

import argparse
from Crawing import Crawer
import logging
import logging.handlers

log_formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')

parser = argparse.ArgumentParser(prog='main.py', usage='%(prog)s [options]')
parser.add_argument('-k', dest = 'key', type = str, nargs = '?', help='search key : goods, no=number, id=user_id(default), url')
parser.add_argument('-v', dest = 'value', type = str, nargs = '?', help = 'search value')
parser.add_argument('-p', dest = 'post_url', type = str, nargs = '?', help = 'destination url for post method')
parser.add_argument('-l', dest = 'log_level', type = str, nargs = '?', help = 'log level : i=info(default), d=debug')

if __name__ == "__main__":
    args = parser.parse_args()

    logger = logging.getLogger('main logger')

    if str(args.log_level) == 'd':
        logger.setLevel(logging.DEBUG)
        log_level = 'debug'
    elif str(args.log_level) == 'i':
        logger.setLevel(logging.INFO)
        log_level = 'info'
    else:
        logger.setLevel(logging.DEBUG)
        log_level = 'debug'

    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(log_formatter)

    logger.addHandler(streamHandler)

    if str(args.key) == 'goods':
        key = 'goods'
    elif str(args.key) == 'no': # goods_no
        key = 'goods_no'
    elif str(args.key) == 'id': # user_id
        key = 'user_id'
    elif str(args.key) == 'url':  # url
        key = 'url'
    else:
        key = 'user_id'  #default

    post_url = str(args.post_url)

    if args.value == None:
        logger.info('invalid uer input')

    else:
        value = args.value

        logger.debug('key[' + key + ']')
        logger.debug('value[' + value + ']')

        crawer = Crawer(key, value, post_url, log_level)

        if key == 'url':
            crawer.crawl_url(value)
        else:
            crawer.crawl_total_pages()