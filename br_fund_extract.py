import re
import time
import urllib
import requests
from bs4 import BeautifulSoup
from os import path
from selenium import webdriver
import pandas as pd
from datetime import datetime

# try:
# except:
#     i = input("hello?")


def strip_all(s):
    """
    strip all characters except numbers (and , . for representation）
    :param s: input string to be stripped
    :return: stripped string
    """
    return re.sub(r"[^\d.,]", "", s)


def open_page(url):
    options = webdriver.ChromeOptions()  # suppress chrome popping
    options.add_argument('-headless')
    options.add_argument('--no-sandbox') # Bypass OS security model
    options.add_argument('--disable-gpu')
    browser = webdriver.Chrome(options=options)
    browser.get(url)
    time.sleep(5)  # conservative waiting for web loading
    soup = BeautifulSoup(browser.page_source, features="html.parser")
    browser.quit()
    return soup


def logfile(log_info):
    log_path = path.join(path.dirname(path.abspath(__file__)),'log.txt') # though the directory is relative, better use the absolute
    with open(log_path, "a") as file:
        file.write(log_info + '\n')  # append file


def br_save_info(fund_name,fund_url,dis_fund_url):
    """
    Save the information of blackrock fund daily
    :param fund_name:  ticker of fund
    :param fund_url:  url of fund page. Notice in some case, part of URL indicate private invector visiting. Important to add that
    :param dis_fund_url: since all fund selected are Accumulation class, to find corresponding distribution yield, immportant to give url
    of corresponding distribution class
    :return:
    """
    base = "https://www.blackrock.com/"  # use for pdf download link
    today = datetime.today().date()  # use for saved data
    year_month = str(today)[:7]  # use for saved file

    # load the web page
    soup = open_page(fund_url)
    soup_dist = open_page(dis_fund_url) # distribution class url

    # update log
    logfile('logging' + fund_name)

    # search and save fact sheet
    file_name = year_month + fund_name + '.pdf'
    file_path = path.join('factsheet', file_name)  # join with folder
    file_path = path.join(path.dirname(path.abspath(__file__)), file_path)  # join with absolute path

    # if fact sheet this month not yet saved, download it
    if not path.exists(file_path):
        try:
            fact_sheet_tag = soup.find(href=re.compile('fact-sheet-en'))
            if fact_sheet_tag is None:
                raise Exception('No fact sheet found')
            fact_sheet_url = urllib.parse.urljoin(base, fact_sheet_tag['href'])
            r = requests.get(fact_sheet_url, allow_redirects=True)
            with open(file_path, "wb") as file:
                file.write(r.content)  # save as binary file
                logfile('fact sheet saved')  # update log
        except Exception as e:
            print("file saving error ", e)
    else:
        print('file exist')

    # search and save other data
    # Fund size
    net_asset_string = soup.find_all(string=re.compile('Net Assets'))  # the string contains net assets
    # print(net_asset_string)
    net_asset_value = net_asset_string[0].find_next(class_='data')  # the next element with USD/GBP string
    net_asset_fund_value = net_asset_string[1].find_next(class_='data')
    net_asset = strip_all(str(net_asset_value))
    net_asset_fund = strip_all(str(net_asset_fund_value))
    # print("net asset ", net_asset, " net asset of fund ", net_asset_fund)

    # distribution yield
    distribution_yield_string = soup_dist.find_all(string=re.compile('Distribution Yield'))  # the string contains net assets
    try:
        distribution_yield_value = distribution_yield_string[0].find_next(class_='data')
        distribution_yield = distribution_yield_value.string.strip()
    except Exception as e:
        print("distribution yield finding error", e)
        distribution_yield = '-'

    # YTM
    YTM_string = soup.find_all(string=re.compile('YTM'))  # the string contains net assets
    try:
        YTM_value = YTM_string[0].find_next(class_='data')
        YTM = YTM_value.string.strip()
        # print(YTM)
    except Exception as e:
        print("YTM finding error", e)
        YTM = '-'

    # nav
    NAV_string = soup.find_all(string=re.compile('NAV as of'))  # the string contains net assets
    try:
        NAV_value = NAV_string[0].find_next(class_='header-nav-data')
        NAV = strip_all(NAV_value.string)
        print(NAV)
    except Exception as e:
        print("NAV finding error", e)
        NAV = "-"

    # share out standing
    share_string = soup.find_all(string=re.compile('Shares Outstanding'))  # the string contains net assets
    try:
        share_value = share_string[0].find_next(class_='data')
        share = share_value.string.strip()
        print(share)
    except Exception as e:
        print("share out standing finding error", e)
        share = "-"

    # consolidate the data, append to existing csv file
    csv_path = path.join(path.dirname(path.abspath(__file__)),'br_data2.csv') # though the directory is relative, better use the absolute
    df = pd.read_csv(csv_path)
    df = df.drop(df.columns[[0]], axis=1)
    new_data = {"Date": today, "Ticker": fund_name,  "NAV": NAV, "Share out standing": share, "Asset of class": net_asset, "Asset of fund": net_asset_fund,
                "Distribution yield": distribution_yield, "YTM": YTM}
    df = df.append(new_data, ignore_index=True)
    print(df)  # print to console
    df.to_csv(csv_path)
    logfile('data saved to csv')  # update log


# This script can be start by double clicking the py file, therefore must be tested under cmd first.
# Under normal run, window would be popped, and disappear after all tasks done.
try:
    logfile('program started on ' + str(datetime.today()))  # update log

    # stored link
    br_dict = dict()
    br_dict['EIMI'] = ['https://www.blackrock.com/lu/individual/products/264659/', 'https://www.ishares.com/uk/individual/en/products/295689/ishares-core-msci-em-imi-ucits-etf-fund?switchLocale=y&siteEntryPassthrough=true']
    br_dict['IWDA'] = ['https://www.blackrock.com/lu/individual/products/251882/ishares-msci-world-ucits-etf-acc-fund','https://www.ishares.com/uk/individual/en/products/287737/ishares-core-msci-world-ucits-etf-fund?switchLocale=y&siteEntryPassthrough=true']
    br_dict['DPYA'] = ['https://www.blackrock.com/lu/individual/products/297188/ishares-developed-markets-property-yield-ucits-etf-fund','https://www.blackrock.com/lu/individual/products/251801/ishares-developed-markets-property-yield-ucits-etf']
    br_dict['LQDA'] = ['https://www.blackrock.com/lu/individual/products/287338/ishares-corp-bond-ucits-etf-usd-acc-fund#/','https://www.blackrock.com/lu/individual/products/251832/ishares-corporate-bond-ucits-etf']
    br_dict['EMCA'] = ['https://www.blackrock.com/lu/individual/products/297673/ishares-j-p-morgan-em-corp-bond-ucits-etf-fund','https://www.blackrock.com/lu/individual/products/251847/ishares-emerging-markets-corporate-bond-ucits-etf']
    br_dict['IUAA'] = ['https://www.blackrock.com/lu/individual/products/287339/','https://www.blackrock.com/lu/individual/products/251750/ishares-us-aggregate-bond-ucits-etf']

    # excute the recording function for each fund
    for k, v in br_dict.items():
        br_save_info(k,v[0],v[1])


except Exception as e:
    logfile('program error on' + str(datetime.today()) + str(e))  # update log


finally:
    logfile('program finished on' + str(datetime.today()))  # update log



