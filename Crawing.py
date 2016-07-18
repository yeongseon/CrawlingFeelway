# -*- coding: utf-8 -*-

from urllib.request import urlopen
from bs4 import BeautifulSoup
import simplejson
import re
import urllib.parse
import urllib.request

import logging
import logging.handlers
import time

log_formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')

default_url = 'http://www.feelway.com/list.php?{}'
css_tag_goods = 'a[href^="list.php?f_key_goods={}&goods_page="]'
css_tag_gno = 'a[href^="list.php?f_key_g_no={}&goods_page="]'
css_tag_uid = 'a[href^="list.php?key_id={}&f_key_u_id={}&goods_page="]'

class Crawer(object):

    def __init__(self, key, value, post_url, log_level):
        self.key = key
        self.value = value
        self.post_url = post_url
        self.count = 1

        self.logger = logging.getLogger('crawer logger')
        if log_level == 'debug':
            self.logger.setLevel(logging.DEBUG)
        elif log_level == 'info':
            self.logger.setLevel(logging.INFO)

        filename = 'server.log'
        streamHandler = logging.FileHandler(filename)
        streamHandler.setFormatter(log_formatter)

        self.logger.addHandler(streamHandler)
        return

    def get_url(self, key, value):
        """
        This function intended to return the url
        :param key:
        :param value:
        :return:
        """
        url = ''
        if key == 'goods':
            query = 'f_key_goods=' + value
        elif key == 'goods_no':
            query = 'f_key_g_no=' + value
        elif key == 'user_id':
            query = 'f_key_u_id=' + value
        url = default_url.format(query)
        return url

    def get_total_pages(self, key, value):
        '''
        This function intended to return the total page
        :param key:
        :param value:
        :return:
        '''
        total_pages = 0
        url = self.get_url(key, value)

        self.logger.debug('url[' + url + ']')

        page = urlopen(url).read()
        soup = BeautifulSoup(page, 'lxml')

        tds = soup.findAll('td', attrs={'align':'center'})

        for td in tds:
            if 'Total' in td.text:
                total_pages = int(td.text.split('Total')[1].split('page')[0])

        # print('Total page[' + str(total_pages) + ']')
        if total_pages == 0:
            css_tag = ''
            if key == 'goods':
                css_tag = css_tag_goods.format(value)
            elif key == 'goods_no':
                css_tag = css_tag_gno.format(value)
            elif key == 'user_id':
                css_tag = css_tag_uid.format(value, value)
            total_pages = len(soup.select(css_tag))

            # print('Total page[' + str(total_pages) + ']')
            if total_pages != 1:
                total_pages -= 1

        # print('Total page[' + str(total_pages) + ']')
        return total_pages

    def crawl_total_pages(self):
        '''
        This function intended to crawl total web page
        :return:
        '''
        total_pages = int(self.get_total_pages(self.key, self.value))


        for i in range(1, total_pages+1):
            url = self.get_url(self.key, self.value) + '&goods_page={}'.format(str(i))
            self.crawl_page(url)
            time.sleep(30)
        return

    def crawl_url(self, url):
        '''
        This function intended to craw the one goods
        :param url:
        :return:
        '''
        self.logger.debug('goods count[' + str(self.count) + ']')
        json_data = self.make_json(url)
        self.post_json(self.post_url, json_data)

    def crawl_page(self, url):
        '''
        This function intended to craw the one page
        :param url:
        :return:
        '''
        goods_list = self.get_goods_url_list(url)

        for url in goods_list:
            # print(url)

            self.logger.debug('goods count[' + str(self.count) + ']')

            json_data = self.make_json(url)
            if len(json_data) != 0 :
                self.post_json(self.post_url, json_data)
                self.count += 1

    def get_goods_url_list(self, url):
        '''
        This function intended to return the goods list
        :param url:
        :return: goods_url
        '''
        # url(http://www.feelway.com/list.php?f_key_goods=bag&goods_page=1)
        page = urlopen(url).read()
        soup = BeautifulSoup(page, 'lxml', from_encoding='utf-8')

        goods_list = []
        goods = soup.findAll('td', attrs={'class':'lb5'})

        for good in goods:
            goods_list.append(good.findAll('a')[0]['href'])

        # remove gl_XXXX.html
        del goods_list[0:6]

        plus_goods = soup.findAll("td", attrs={'background': 'http://icon.feelway.com/feel_image_02/bg03.gif'})

        plus_goods_len = 0
        if len(plus_goods) == 0:
            plus_goods_len = 0
        else:
            plus_goods_len = int(len(plus_goods[1].findAll("a"))/3)

        self.logger.debug('plus_goods_len[' + str(plus_goods_len) + ']')

        # remove plus goods
        del goods_list[0:plus_goods_len]

        return goods_list

    def make_json(self, url):
        '''
        This function intended to make json which includes goods information
        :param url:
        :return:
        '''
        page = urlopen(url).read()
        soup = BeautifulSoup(page, 'lxml', from_encoding='utf-8')

        try:
            temp_str = soup.findAll('td', attrs={'class': 'mail'})[0].text
            # om2653465472 : 《럭스보이》16SS★포켓 폴로카라넥 MJP022C 00047 117
        except IndexError:
            data = {}
            data['soldout_yn'] = 'Y'
            # self.logger.debug('product_number[' + product_number + ']')
            self.logger.debug('soldout_yn[Y]')
            json_data = {}
            # json_data[product_number] = data
            return json_data

        # print(temp_str)

        split_idx = temp_str.find(':')
        product_number = temp_str[:split_idx ].lstrip().rstrip()
        product_name = temp_str[split_idx:].lstrip().rstrip()

        tds = soup.findAll("td", attrs={'align':'center'})
        for td in tds:
            if '일시품절' in td.text:
                data = {}
                data['soldout_yn'] = 'Y'
                self.logger.debug('product_number[' + product_number + ']')
                self.logger.debug('soldout_yn[Y]')
                json_data = {}
                json_data[product_number] = data
                return json_data
            if '판매가 종료' in td.text:
                data = {}
                data['soldout_yn'] = 'Y'
                self.logger.debug('product_number[' + product_number + ']')
                self.logger.debug('soldout_yn[Y]')
                json_data = {}
                json_data[product_number] = data
                return json_data

        try:
            temp_str = soup.findAll('tr', attrs={'bgcolor':'#E3E1DA'})[0].findAll('td')[-1].text
        except IndexError:
            data = {}
            data['soldout_yn'] = 'Y'
            self.logger.debug('product_number[' + product_number + ']')
            self.logger.debug('soldout_yn[Y]')
            json_data = {}
            json_data[product_number] = data
            return json_data
        # product_name = temp_str.split('-')[-1].lstrip().rstrip()

        global brand
        global seller_id

        for form in soup.findAll("input", attrs={'type': 'hidden'}):
            if form['name'] == 'brand_name':
                brand = form['value']
            elif form['name'] == 'seller_id':
                seller_id = form['value']

        self.logger.debug('product_number[' + product_number + ']')
        self.logger.debug('brand[' + brand + ']')
        self.logger.debug('product_name[' + product_name + ']')
        self.logger.debug('seller_id[' + seller_id + ']')

        categorys = ['여성슈즈', '남성슈즈', '가방/핸드백', '지갑/벨트', '악세서리',
                     '여성의류', '남성의류', '화장품/향수', '선글래스/안경', '시계', '패션잡화',
                     'KIDS', '기타']

        index = 0
        found = 0
        for link2 in soup.findAll('td', attrs={'class': 'link2'}):
            for category in categorys:
                if category in link2.text:
                    found = 1
                    # print(index, link2.text)
                    break;
            if found:
                break;
            index += 1

        # print(index)
        temp_str = soup.findAll('td', attrs={'class':'link2'})[index].findAll('a')[-1].text
        # print(temp_str)
        category = temp_str.split('-')[-1]
        print(category)
        self.logger.debug('category[' + category + ']')

        index = 0
        index_price = 2
        index_size = 3
        for temp in soup.findAll('tr', attrs={'bgcolor': 'E3E1DA'}):
            if '가격/배송' in temp.text:
                index_price = index
            elif '사이즈' in temp.text:
                index_size = index
            index += 1

        self.logger.debug('index_price[' +  str(index_price) + ']')
        self.logger.debug('index_size[' +  str(index_size) + ']')

        temp_str = soup.findAll('tr', attrs={'bgcolor': 'E3E1DA'})[index_price].text
        # 가격 / 배송
        # 633, 000        원　
        # 카드결제가능
        # 배송방법: 택배   　배송비: 무료배송
        # print(temp_str)
        price = temp_str.split('원')[0].split('배송')[-1].lstrip().rstrip()
        dlv_method = temp_str.split('배송비 ')[0].split(':')[-1].lstrip().rstrip()
        self.logger.debug('price [' + price + ']')
        self.logger.debug('dlv_method[' + dlv_method + ']')

        if '예상비용' in temp_str:
            dlv_method2 = temp_str.split('예상비용 ')[0].split(':')[-1].lstrip().rstrip()
            dlv_price = temp_str.split('예상비용 :')[-1].lstrip().rstrip()
        else:
            dlv_method2 = temp_str.split('배송비 :')[-1].lstrip().rstrip()
            dlv_price = '0'

        self.logger.debug('dlv_method2[' + dlv_method2 + ']')
        self.logger.debug('dlv_price[' + dlv_price + ']')

        temp_str = soup.findAll('tr', attrs={'bgcolor': 'E3E1DA'})[index_size].findAll('td')[-1].text
        # 상세설명참조　/　이태리
        # print(temp_str)

        size = temp_str.split('/')[0].lstrip().rstrip()
        wonsanji= temp_str.split('/')[1].lstrip().rstrip()

        self.logger.debug('size[' + size + ']')
        self.logger.debug('wonsanji[' + wonsanji + ']')

        temp_str = soup.findAll('table', attrs={'cellpadding': '5'})[1].text
        detail_desc = temp_str.split('상품정보제공')[0].lstrip().rstrip()
        # self.logger.debug('detail_desc[' + detail_desc + ']')

        temp_str = soup.findAll("td", attrs={'bgcolor': '#FFFFFF'})[0]
        img_len = len(temp_str.findAll('img'))
        # print('img_len[' + str(img_len) + ']')

        data = {}
        img_names = ['img1', 'img2', 'img3', 'img4', 'img5', 'img6', 'img7', 'img8', 'img9', 'img10']
        j = 0
        for i in temp_str.findAll("img"):
            if j < 10:
                data[img_names[j]] = i['src']
            j += 1

        data['soldout_yn'] = 'N'
        data['category'] = category
        data['brand'] = brand
        data['product_name'] = product_name
        data['seller_id'] = seller_id
        data['price'] = price
        data['dlv_method'] = dlv_method
        data['dlv_method2'] = dlv_method2
        data['dlv_price'] = dlv_price
        data['size'] = size
        data['wonsanji'] = wonsanji
        data['detail_desc'] = detail_desc
        data['url'] = url

        json_data = {}
        json_data[product_number] = data

        return json_data

    def post_json(self, post_url, data):
        '''
        This function intended to post json
        :param post_url:
        :param data:
        :return:
        '''
        # url = 'http://yongmangu105.cafe24.com/crawling/addTmpProduct_feelway'
        # url = 'http://yongmangu105.cafe24.com/crawling/printJSON'
        params = simplejson.dumps(data).encode('utf-8')
        # header = {"Content-Type":"application/octet-stream"}
        header = {'content-type': 'application/json'}
        req = urllib.request.Request(post_url, data=params, headers=header)
        response = urllib.request.urlopen(req)
        # self.logger.debug('response[' + response.read().decode('utf-8') + ']')
