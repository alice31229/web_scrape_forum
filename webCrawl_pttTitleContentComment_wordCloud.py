import re
#import os
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# import threading # when there is need to return variable 


# webCrawl
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.keys import Keys 

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


# wordCloud
#from ckiptagger import data_utils, construct_dictionary, WS, POS, NER
import jieba
import jieba.analyse
from PIL import Image 
import imageio
from wordcloud import WordCloud
import matplotlib.pyplot as plt

my_headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
             'cookie': 'over18=1;'}

# 日期 關鍵字 
# 文章標題 內文 留言串

# salary_url = 'https://www.ptt.cc/bbs/Salary/index.html'

# response = requests.get(salary_url, headers = my_headers)
# response.encoding = 'utf-8' #轉換編碼至UTF-8
# soup = BeautifulSoup(response.text, features="lxml")

# # 找到特定的div
# target_div = soup.find('div', class_='r-list-sep')

# ###
# # 找到特定div之前的所有class=title的div
# previous_divs = target_div.find_all_previous('div', class_='title')

# # 打印所有div
# lst = []
# lst_url = []
# deleted_article = '本文已被刪除'
# for div_i in range(len(previous_divs)):

#     div_title = previous_divs[div_i].text.replace('\n','')
#     if deleted_article not in div_title:

#         lst.append(div_title)

#         div_url = 'https://www.ptt.cc'+previous_divs[div_i].find('a')['href']
#         lst_url.append(div_url)

#     else:

#         lst.append(div_title)
#         lst_url.append('Deleted url')

# data = {'title':lst, 'articleURL':lst_url}
# df_lst = pd.DataFrame(data)



# -------------------------------------------------------
# ptt Brain 可查找個版面的關鍵字標題文章
brain_url = 'https://www.pttbrain.com/'

# 第一步 取得關鍵字文章標題與url
options = Options()
options.add_argument('disable-infobars')
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-extensions")
options.add_argument("--profile-directory=Default")
options.add_argument("--incognito")
options.add_argument("--disable-plugins-discovery")
options.add_argument("--start-maximized")
options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')
#options.add_argument('cookie=over18=1')
options.chrome_executable_path='../webCrawl/chromedriver'
driver=webdriver.Chrome(options=options)

# date = []
# title = []
# url = []
# forum = []

# title
def article_title_link(scrolls, keywords):

    date = []
    title = []
    url = []
    forum = []
    
    # 每滑到底多增10筆文章
    pttBrain = f'https://www.pttbrain.com/search?platform=ptt&q={keywords}'

    driver.get(pttBrain)
    time.sleep(np.random.randint(5, 20))

    number = 1

    while number<=scrolls:
        
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(np.random.randint(5, 20))
        number+=1

    articles_urls = driver.find_elements(By.CLASS_NAME,'summary')
    forums = driver.find_elements(By.CSS_SELECTOR,'.ui.teal.small.label')
    
    for a in articles_urls:
        date.append(a.find_element(By.CLASS_NAME, 'date').text)
        title.append(a.find_element(By.TAG_NAME,'span').text)
        url.append(a.find_element(By.TAG_NAME,'a').get_attribute('href'))
        
    for f in forums:
        forum.append(f.text)
    
    articles_df = pd.DataFrame({
        'date':date,
        'forum':forum,
        'title':title,
        'articleURL':url
    }) 
    
    articles_df['date'] = pd.to_datetime(articles_df['date'])
    
    # 一週內 文章
    # 计算日期范围：一週內
    end_date = pd.Timestamp(datetime.now().date())
    start_date = end_date - timedelta(days=7)

    # 使用条件筛选根据日期范围筛选DataFrame
    articles_df = articles_df[(articles_df['date'] >= start_date) & (articles_df['date'] <= end_date)]
    
    driver.close()
    
    return articles_df


# comment
# driver=webdriver.Chrome(options=options)
#driver_original=webdriver.Chrome(options=options)

# date = []
# topic = []
# floor = []
# person = []
# comment = []
# forum = []

def get_comments(target_articles):
    
    date = []
    topic = []
    floor = []
    person = []
    comment = []
    forum = []
    
    for ind in range(len(target_articles['title'])):
        
        driver.get(target_articles['articleURL'][ind])
        time.sleep(np.random.randint(7, 20))
        
        comments = driver.find_elements(By.CLASS_NAME, 'comment')
        
        for c in comments:
            spans = c.find_elements(By.TAG_NAME, 'span')
            author = c.find_element(By.CLASS_NAME, 'author')
            
            date.append(target_articles['date'][ind])
            topic.append(target_articles['title'][ind])
            forum.append(target_articles['forum'][ind])
            
            floor.append(spans[0].text)
            person.append(author.text)
            comment.append(spans[1].text)

    comments_df = pd.DataFrame({'日期':date, '文章標題':topic, '版面':forum, '樓數':floor,
                               '留言人':person, '留言':comment})
    
    # comments cleaning
    comments_df['留言'] = comments_df['留言'].str.replace(r'(https?://\S+)|\n', '', regex=True)
    pattern = re.compile(r'[^\w\s!@#$%^&*()_+\-=\[\]{};\'\\:"|<,./<>?`~]')
    comments_df['留言'] = comments_df['留言'].apply(lambda x: re.sub(pattern, '', x))
    comments_df = comments_df[comments_df['留言'] != '']
    comments_df = comments_df.drop_duplicates()
    
    driver.close()
                
    return comments_df


# content
# date = []
# forum = []
# topic = []
# content = []


def get_contents(target_articles):

    date = []
    forum = []
    topic = []
    content = []
    
    for ind in range(len(target_articles['title'])):
        
        driver.get(target_articles['articleURL'][ind])
        time.sleep(np.random.randint(7, 20))
        
        contents = driver.find_elements(By.TAG_NAME, 'p')
            
        #topic.append(target_articles['title'][ind])
        
        content_txt = ''
        for c in contents:
            if '\n' not in c.text:
                content_txt+=c.text
            else:
                content_txt+=c.text.replace('\n','')
                
        print(content_txt)
        
        date.append(target_articles['date'][ind])
        topic.append(target_articles['title'][ind])
        forum.append(target_articles['forum'][ind])
        
        content.append(content_txt)

    print(len(date), len(topic), len(forum), len(content))
    contents_df = pd.DataFrame({'日期':date, '文章標題':topic, '版面':forum, 
                                '文章內容':content})
    
    # comments cleaning
    contents_df['文章內容'] = contents_df['文章內容'].str.replace(r'(https?://\S+)|\n', '', regex=True)
    contents_df['文章內容'] = contents_df['文章內容'].str.replace(r'原文連結/ptt/article/M\.\d+\.\w+\.\w+', '', regex=True)
    pattern = re.compile(r'[^\w\s!@#$%^&*()_+\-=\[\]{};\'\\:"|<,./<>?`~]')
    contents_df['文章內容'] = contents_df['文章內容'].apply(lambda x: re.sub(pattern, '', x))
    contents_df = contents_df[contents_df['文章內容'] != '']
    contents_df = contents_df.drop_duplicates()
    
    driver.close()
                
    return contents_df


# title wordCloud
STOP_content2 = open("./stop_words_ch_filer.txt")# 匯入停用字字典 
with STOP_content2 as f:
    STOP_ch2 = f.read().split('\n')

stop2 = pd.DataFrame()
stop2['stop_word'] = STOP_ch2

stop_txt = pd.read_csv('stopwords.txt',sep='\n',names=['stop_word'])

combine_stop = pd.concat([stop2,stop_txt])
combine_stop = combine_stop.drop_duplicates()
combine_stop = combine_stop['stop_word'].to_list()

# ptt hot
#stops = ['新聞','情報','問卦','BOX','Live','請益']

# gamer job
#stops = ['討論','快訊','公告','閒聊','心得','問題','情報']

# ptt tech job
stops = ['新聞','情報','請益','討論','快訊','問題','Re','下一步','怎麼','只有','vs','最後','請問',
         '關於','一起','下一','一步','問卦','去領','對面','整天','公式','一年','辦法','同款','你給',
         '我學','心去','一家','沒見過','前問','還快','初始','算出','算出來','pujos','lks','昨天',
         '例子','搞錯','運作','會來','多強','厲害','開出來','開得','能面','落到','半部','大差','不離',
         '開頭','做出','僅此','能不能','往下','哈囉','可知','一副','高高','高高在上','JPTT','Xiaomi',
         '2210129SG','喔喔','唉呀','那是','那是爛','時一家','算法','只差','就領','但領','沒差',
         '五六千塊','就能','價就能','三倍','沒作','變多','生活品','變好','衣服','褲子','幾百塊','喵喵',
         '小物','整打整','鞋子','一雙賣','轉賣','直購','下三雙','包色','有夠','爽頭','toastemperor',
         '哪去','光要','二次','超久','幾千','套上','試圖','探出','主角','秤斤','鬼裝','小二','希望',
         '某個價','認知','鐵定','吐司','皇帝','先講','專找','變大','中位','位數','超過','拉到','該不',
         '你娘','ai770116','BePTT','XQ', 'BT52','crazycomet', 'milk7054','Gief','為啥','沒多',
         '大樓','我領','換到','踢踢','August2006','Sougetu','greensaru','key555102','blueskyqoo',
         'Healine','rushfudge','sunsad','kimura0701','blue999','trh123h','很會','earnformoney', 
         'boxmeal','反正','嘻嘻','理由','那麼多','誰領','智障','分給', '追到','這幾年','只會','記得',
         '漲一', '追上','投給', '害死','還不漲', '怎買', '都講','越來越','爆發','無感','老實', '實說', 
         '老實說','發了','業就','偷笑', '白癡','導致','解決', '很會演','裝死', '呆灣', '1aKaKy8A','好笑',
         '八卦板', '懷念','每天多', '幾百','早早', '上班','恭賀', '阿勞','是領', '領比','醒醒','調不調',
         '加不到', '奇文', '共賞','想法', '解釋', '你懂', '我給', '你簽', '夠爽','差不','持續', '很爽',
         '出爐']

for s in stops:
    combine_stop.append(s)

# 標題：title, 內文：文章標題, 留言：留言
df_lst = article_title_link(1, '薪資')

# driver=webdriver.Chrome(options=options)
# comment_df = get_comments(df_lst)

driver=webdriver.Chrome(options=options)
content_df = get_contents(df_lst)


#titleTxtOriList = df_lst['title'].to_list()
titleTxtOriList = content_df['文章內容'].to_list()
#titleTxtOriList = comment_df['留言'].to_list()

titleTxtOriStr = ' '.join(map(str, titleTxtOriList))


# ckip
#ws = WS("./data")


# jieba
jieba.set_dictionary('./dict.txt.big.txt')
titleTxt_jb1 = jieba.cut_for_search(titleTxtOriStr)
titleTxt_jb2 = jieba.cut(titleTxtOriStr, cut_all = True)

titleTxt_jb_list = []
for content in titleTxt_jb1:
    if len(content) > 1: 
        titleTxt_jb_list.append(content)
 # 如果詞的長度小於2就不要
    else:continue   

titleTxt_jb_str = ' '.join(titleTxt_jb_list)

## visualize
wc_titleTxt_jb = WordCloud(
                 background_color='white',
                 font_path="/System/Library/Fonts/Hiragino Sans GB.ttc",
                 stopwords=combine_stop,
                 width=2000, height=1200, relative_scaling=0)

wc_titleTxt_jb.generate(titleTxt_jb_str)

f = plt.figure(figsize=(30,30))
p1 = f.add_subplot(131)
p1.imshow(wc_titleTxt_jb)
p1.axis('off')

# 儲存圖片為.png檔案
output_path = 'titleWordCloud.png'
plt.savefig(output_path, bbox_inches='tight', pad_inches=0)

words = wc_titleTxt_jb.words_.keys()
print(words)

TOKEN = "YOUR_TOKEN"
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
secret = requests.get(url).json()
chat_id = secret['result'][0]['message']['chat']['id']

# text part
t_msg = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={words}"
requests.get(t_msg)

# wordCloud part

# Telegram Bot API 的 sendPhoto 網址
url = f'https://api.telegram.org/bot{TOKEN}/sendPhoto'

# 使用 multipart/form-data 形式傳送圖片
files = {'photo': open(output_path, 'rb')}
data = {'chat_id': chat_id}

response = requests.post(url, files=files, data=data)

# 檢查回傳結果
if response.status_code == 200:
    print('圖片已成功傳送至 Telegram Bot！')
else:
    print('圖片傳送失敗，錯誤訊息:', response.text)


# calculate words frequency
#word_freq = WordCloud().process_text(titleTxt_jb_str)
# word_freq = WordCloud().process_text(wc_titleTxt_jb)
# df_wc = pd.DataFrame({'詞':word_freq.keys(),
#                       '頻率':word_freq.values()})
# df_wc = df_wc.sort_values(by='頻率', ascending=False)
# print(df_wc)
