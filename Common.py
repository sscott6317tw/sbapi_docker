#In[]
import requests,subprocess
from selenium import webdriver
import threading,time, configparser
import winreg , os , requests , zipfile
from Logger import create_logger
from bs4 import BeautifulSoup
log = create_logger(r"\AutoTest", 'test')




class Common:
    '''
    sec_times: 併發, stop_times: 幾秒後結束
    '''
    def __init__(self,sec_times='',stop_times=''):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            
            }
        
        self.session = requests.Session()
        self.sec_times = sec_times
        self.stop_times = stop_times

    def get_Chrome_version(self):#取得local Chrome version
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Google\Chrome\BLBeacon')
        version, types = winreg.QueryValueEx(key, 'version')
        local_version = version.split('.')[0]
        log.info('local Chrome version : %s'%local_version)
        return local_version

    def get_Driver_version(self):
        '''查询系统内的Chromedriver版本'''
        local_driver_version = os.popen('chromedriver --version').read().split(' ')[1].split('.')[0]
        log.info('local driver version : %s'%local_driver_version)
        return local_driver_version


    def get_server_chrome_versions(self, version):# version 需帶 數字,去抓去 網站上有的 chromedriver
        '''return all versions list'''

        #down_ver_list = []# 存放 有mapping 到的 chromedriver version
        url="https://registry.npmmirror.com/-/binary/chromedriver/"
        rep = requests.get(url).json()# list 裡麵包字典
        for dict_ in rep:
            split_version = dict_['name'].split('.')[0]# # 抓取 name 並把 他取出 70.0.3538.97/ > 70
            if version == split_version:
                down_url = dict_['url']
                log.info('抓到 對應的 driver 版本 : %s'%dict_['name'])
                return down_url+ 'chromedriver_win32.zip'

    def download_driver(self, download_url):
        '''下载文件'''
        file = requests.get(download_url)
        with open("chromedriver.zip", 'wb') as zip_file:        # 保存文件到脚本所在目录
            zip_file.write(file.content)
        new_driver = self.get_Chrome_version()
        log.info('新driver: %s 下载成功'%new_driver)


    def unzip_driver(self):
        '''解压Chromedriver压缩包到指定目录'''
        f = zipfile.ZipFile("chromedriver.zip",'r')
        for file in f.namelist():
            f.extract(file, '.')
        log.info('解壓縮成功')

    def get_driver(self):
        local_chrome = self.get_Chrome_version()
        local_driver = self.get_Driver_version()
        if local_chrome == local_driver:
            log.info('local chrome version 和 driver version 一致 , 無須 下載')
        else:
            down_url = self.get_server_chrome_versions(local_chrome)
            self.download_driver(down_url)
            self.unzip_driver()

        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless") #無頭模式
            driver = webdriver.Chrome(chrome_options = chrome_options,
            executable_path= "chromedriver.exe")
            self.dr = driver
            return self.dr
        except Exception as e :
            print('get driver :%s'%e)
            time.sleep(1)

    def return_IP(self,r):# 抓取 response的 IP
        try:
            respone = r.text
            #self.log.info('回復: %s'%respone)
            html = BeautifulSoup(respone,'lxml')# type為 bs4類型
            
            table_ = html.find_all('table',class_= 'table')
            if len(table_) == 0:# desktop 沒有 table 元素 
                taglist = html.find_all('body')
                if 'Server IP:' in respone:
                    self.Parsing = 'Desktop 0'#解析方式
                    for trtag in taglist:
                        a = (trtag.text)
                    return  (a.split('Server IP:')[1].split('Key:')[0].split(':')[0]  )
                elif 'IP' not in respone:
                    self.Parsing = 'Desktop no IP to 解析'
                    for trtag in taglist:
                        a = (trtag.text)
                    return a
                else:
                    self.Parsing = 'Desktop 1'
                    for trtag in taglist:
                        a = (trtag.text)
                    return (a.split('Server IP :')[1].split('Port')[0]   )

            else:# mobile 有 table 屬性
                self.Parsing = 'Moble'
                taglist = html.find_all('tr')
                for trtag in taglist:  
                    tdlist = trtag.find_all('td')
        
                    if 'IP' in  tdlist[0].text:
                        return(tdlist[1].text)
                
        except Exception as e:
            log.error('%s 有誤 :%s'%(self.url, e))
            log.error('%s'%respone)
            return '回復 response 有誤'

    def threads(self, func_name_list ):# 併發邏輯
        print('同時併發: %s次, %s 秒鐘後結束'%(self.sec_times,self.stop_times ) )
        self.time_start = time.time() #開始計時
        self.time_end = time.time()
        str_time= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.time_start))
        #print('start: %s'%str_time)
        #self.time_end   會 再while 迴圈一值變動
        while self.time_end - self.time_start <= self.stop_times:# 當程式執行超過指定時間 ,就break
            threads = []
            for i in range(self.sec_times):
                for func_name in func_name_list:
                    t  = threading.Thread(target= func_name )
                    #print (self.headers)
                    threads.append(t)
            for i in threads:
                i.start()
            for i in threads:
                i.join()
            self.time_end  = time.time() #開始計時
        str_time= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.time_end))
        #print('end: %s'%str_time)
        print('time cost',self.time_end -self.time_start,'s')

    def game_mapping(self, sport):# 丟sport 參數, 回傳 gameid . 給 ShowAllOdds 街口使用
        game_dict = {'Soccer': {'gameid': 1},'Saba_Soccer': {'gameid': 997},'Basketball': {'gameid': 2},'Football': {'gameid': 3},'Ice_Hockey': {'gameid': 4},'Tennis': {'gameid': 5},'Volleyball': {'gameid': 6}\
            ,'Snooker/Pool': {'gameid': 7},'Baseball': {'gameid': 8},'Badminton': {'gameid': 9},'Golf': {'gameid': 10},'Motorsports': {'gameid': 11},'Swimming': {'gameid': 12},\
            'Politics': {'gameid': 13},'Water_Polo': {'gameid': 14},'Diving': {'gameid': 15},'Boxing/MMA': {'gameid': 16},'Archery': {'gameid': 17},'Table_Tennis': {'gameid': 18},\
            'Weightlifting': {'gameid':19},'Canoeing': {'gameid': 20},'Gymnastics': {'gameid': 21},'Athletics': {'gameid': 22},'Equestrian': {'gameid': 23},'Handball': {'gameid': 24},\
            'Darts': {'gameid': 25},'Rugby': {'gameid': 26},'Field_Hockey': {'gameid': 28},'Winter_Sports': {'gameid': 29},'Squash': {'gameid': 30},'Entertainment': {'gameid': 31},'Netball': {'gameid': 32},\
            'Cycling': {'gameid': 33},'Fencing': {'gameid': 34},'Judo': {'gameid': 35},'M.Pentathlon': {'gameid': 36},'Rowing': {'gameid': 37},'Sailing': {'gameid': 38},\
            'Shooting': {'gameid': 39},'Taekwondo': {'gameid': 40},'Triathlon': {'gameid': 41},'Wrestling': {'gameid': 42},'E-Sports': {'gameid': 43},'Muay_Thai': {'gameid': 44},\
            'Beach_Volleyball': {'gameid': 45},'Unknown_sport(Thai_sport)': {'gameid':46},'Kabaddi': {'gameid': 47},'Sepak_Takraw': {'gameid': 48},'Futsal': {'gameid': 49},\
            'Cricket': {'gameid': 50},'Beach_Soccer': {'gameid': 51},'Poker': {'gameid': 52},'Chess': {'gameid': 53},'Olympics': {'gameid': 54},'Finance': {'gameid': 55},\
            'Lotto': {'gameid': 56},'Other_Sports': {'gameid': 99},'Soccer Euro Cup': {'gameid': 197},'Soccer Champions Cup': {'gameid': 196},'Soccer Asian Cup': {'gameid': 194},\
            'Soccer League': {'gameid': 190},'Soccer World Cup': {'gameid': 192},'Soccer Nation': {'gameid': 191},'Virtual Soccer': {'gameid': 180},\
            'Virtual Basketball': {'gameid': 193},'Virtual Tennis': {'gameid': 186},'Number Game': {'gameid': 161},'Turbo Number Game': {'gameid': 161},'Happy 5': {'gameid': 164}
            }
        return game_dict[sport]['gameid']


    def Odds_Tran(self, odds,odds_type='Dec'):# Marlay 轉 Dec Odds  , 在betting 時會用
        if odds_type == 'Dec':
            if float(odds) < 0:# 小於0, 跟china一樣, 只是多加1
                confirm_odds = round(abs(int(1/ float(odds)*100))+100)/100  
            else:# odds+1
                if float(odds) > 1:# 如果拿到 dec odds 值已經大於1 ,　就不用轉換
                    confirm_odds = float(odds)
                else:
                    confirm_odds = round(float(odds) * 100 + 100) / 100
        elif odds_type in ['US','Indo'] :
            if float(odds) < 0:
                if float(odds) >= 0.79:# 大於等於 0.79無條件進位
                    confirm_odds = int(-1/ float(odds)*100+ 1)/100
                else:# 跟china一樣
                    confirm_odds = abs(int(1/ float(odds)*100)/100)
            else:# 大於 0
                if float(odds) <= 0.79:# 小於等於 0.79無條件進位
                    confirm_odds = (int(-1/ float(odds)*100)-1)/100
                else:# -1去除
                    confirm_odds = int(-1/ float(odds)*100)/100
            if odds_type == 'US':
                confirm_odds = round(confirm_odds * 100,2)
        elif odds_type == 'CN':
            if float(odds) < 0:# 小於0 , 需用 1去除 
                confirm_odds = abs(int(1/ float(odds)*100)/100)
            else:# 大於0 就是 一樣的odds
                confirm_odds = float(odds)
        elif odds_type == 'MY':
            confirm_odds = float(odds)
        confirm_odds = f'{confirm_odds:.2f}'# 0.1 轉乘 0.10
        return confirm_odds


    def set_list(dict_):# 回傳 目前有做過的 bettype 
        list_= [] # 二微陣列  再包list
        for i in dict_.values():# i 為list
            for b in i:# 再把所列表所有元素 丟到 list_ ,去做set
                list_.append(b)
        print(list_)
        #print(list_)
        s = set(list_)
        return(list(s))

    def get_config(self):
        # 建立 ConfigParser
        config = configparser.ConfigParser(comment_prefixes='/', allow_no_value=True)
        config.read('config.ini', encoding="utf-8")
        return config
    
    def get_node_type(self):# 0 為本地, 1 為 remote
        node_type = self.get_config()['config']['node_type']

        return node_type


class Env:
    def __init__(self):
        self.api_url_dict = { 'mobile': {'W88':  'https://ismart.w2sports.com/apilogin' , 
        'Happy8':'http://ismart.zjc988.com/apilogin', 
        'ECLBET': 'http://p4b0mb.258088.net/apilogin', '12Bet': 'http://ismart.12bet.com/apilogin',
        '11Bet': 'http://l9j7mb.pg5688.com/apilogin', 'Alog': 'https://ismart.dafabet.com/apilogin',
        'Ae88': 'http://u022mb.fx9888.com/apilogin' , '24AVIA':  'http://y530mb.ofje104.com/apilogin',
        'Yibo': 'http://e7b8mb.pg5688.com/apilogin' , 
        'Xtu168': 'http://g5a1mb.fx9888.com/apilogin' , 
        'Sm88': 'http://x3g8mb.pg5688.com/apilogin', 'FB88CV': 'http://e143mb.258088.net/apilogin',
        'FB88': 'http://j1f9mb.pg5688.com/apilogin' , '368Cash': 'http://b8d6mb.fx9888.com/apilogin', 
        'A1game': 'http://b9p1mb.fx9888.com/apilogin', 'Haifa': 'https://ismart.playbooksb.com/apilogin',
        'Macaubet': 'http://smart.macaubetonline.com/', 'AsiaBet88': 'http://ismart.fun88.com/apilogin',
        'ABcasino': 'http://g110mb.258088.net/apilogin'
        
          },
        
        
        'desktop': {'W88' : 'https://alicantemkt.w2sports.com/onelogin.aspx'}
        }

    def Allure_Report(self):# 跑完生成allure json檔後, 執行該方式 去生成報告
        popen_path = 'allure generate reports -o allure_report/ --clean'
        self.log.info(popen_path)
        p = subprocess.Popen(popen_path,stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
        shell=True, universal_newlines=True)
        self.log.info( p.communicate())
        return p.communicate()

class NoTestException(Exception):
    pass
