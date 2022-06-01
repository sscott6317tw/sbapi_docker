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

    def get_Chrome_version(self,split=True):#取得local Chrome version
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Google\Chrome\BLBeacon')
        version, types = winreg.QueryValueEx(key, 'version')
        if split == True:
            local_version = version.split('.')[0]
        else:
            local_version = version
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
        try:
            local_driver = self.get_Driver_version()
        except:
            log.info('資料夾內無 Chrome driver')
            local_driver = '0'
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
                    try:
                        if 'IP' in  tdlist[0].text:
                            return(tdlist[1].text)
                    except:
                        import re
                        whoamiIP = re.findall('([0-9]+.[0-9]+.[0-9]+.[0-9]+)',str(html))[0]
                        return whoamiIP
                
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
        if type(sport) != str:
            if {'gameid': sport} in game_dict.values():
                return list(game_dict.keys())[list(game_dict.values()).index({'gameid': sport})]
        else:
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
        
        'desktop': {'W88' : 'https://alicantemkt.w2sports.com/onelogin.aspx',
            'Happy8':'http://mkt.m4080.com/onelogin.aspx',
            'ECLBET': 'https://p4b0ob.258088.net/onelogin.aspx', '12Bet': 'https://mkt.12bet.com/onelogin.aspx',
            '11Bet': 'http://l9j7ob.pg5688.com/onelogin.aspx', 'Alog': 'https://prices.dafabet.com/onelogin.aspx',
            'Ae88': 'https://u022ob.ofje104.com/onelogin.aspx' , '24AVIA':  'https://y530ob.ofje104.com/onelogin.aspx',
            'Yibo': 'https://e7b8ob.258088.net/onelogin.aspx' , 
            'Xtu168': 'https://g5a1ob.ofje104.com/onelogin.aspx' , 
            'Sm88': 'https://x3g8ob.258088.net/onelogin.aspx', 'FB88CV': 'https://e143ob.258088.net/onelogin.aspx',
            'FB88': 'https://j1f9ob.258088.net/onelogin.aspx' , '368Cash': 'https://b8d6ob.ofje104.com/onelogin.aspx',   
            'A1game': 'https://b9p1ob.ofje104.com/onelogin.aspx',  'Haifa': 'http://mkt.sbsportplay.net/onelogin.aspx',
            'Macaubet': 'http://www.macaubetonline.com', 'AsiaBet88': 'https://sports.fahuathuat.com/onelogin.aspx',
            'ABcasino': 'https://g110ob.258088.net/onelogin.aspx'
            },
        } 
        #'Haifa' & 12Bet opensports 抓不到 Ms2 Url，觀察後發現 MS2 Url 格式皆為 'agnj3.' + self.url.split('.')[1] + '.com'，先寫死

    def Allure_Report(self):# 跑完生成allure json檔後, 執行該方式 去生成報告
        popen_path = 'allure generate reports -o allure_report/ --clean'
        self.log.info(popen_path)
        p = subprocess.Popen(popen_path,stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
        shell=True, universal_newlines=True)
        self.log.info( p.communicate())
        return p.communicate()

class NoTestException(Exception):
    pass


betteam_trans = {
    381 : {'odds1a': 's', 'odds2a': 'm'}, 
    382 : {'odds1a': 's', 'odds2a': 'm'},
    390 : {'odds1a': 'y', 'odds2a': 'n'}, 
    479 : {'odds1a': 'y', 'odds2a': 'n'}, 
    481 : {'odds1a': 'y', 'odds2a': 'n'}, 
    714 : {'odds1a': 'y', 'odds2a': 'n'}, 
    9073 : {'odds1a': 'y', 'odds2a': 'n'}, 
    9075 : {'odds1a': 'y', 'odds2a': 'n'}, 
    9087 : {'odds1a': 'y', 'odds2a': 'n'},
    8104 : {'odds1a': 'mo', 'odds2a': 'me'}, 
    8101 : {'odds1a': 'b', 'odds2a': 's'}, 
    184 : {'odds1a': 'o', 'odds2a': 'e'}, 
    393 : {'odds1a': 'o', 'odds2a': 'e'}, 
    394 : {'odds1a': 'o', 'odds2a': 'e'}, 
    400 : {'odds1a': 'o', 'odds2a': 'e'}, 
    428 : {'odds1a': 'o', 'odds2a': 'e'}, 
    470 : {'odds1a': 'o', 'odds2a': 'e'}, 
    471 : {'odds1a': 'o', 'odds2a': 'e'}, 
    472 : {'odds1a': 'o', 'odds2a': 'e'}, 
    611 : {'odds1a': 'o', 'odds2a': 'e'}, 
    706 : {'odds1a': 'o', 'odds2a': 'e'}, 
    710 : {'odds1a': 'o', 'odds2a': 'e'}, 
    8102 : {'odds1a': 'o', 'odds2a': 'e'}, 
    9005 : {'odds1a': 'o', 'odds2a': 'e'}, 
    9061 : {'odds1a': 'o', 'odds2a': 'e'}, 
    9071 : {'odds1a': 'o', 'odds2a': 'e'}, 
    9078 : {'odds1a': 'o', 'odds2a': 'e'}, 
    9079 : {'odds1a': 'o', 'odds2a': 'e'}, 
    9080 : {'odds1a': 'o', 'odds2a': 'e'}, 
    9081 : {'odds1a': 'o', 'odds2a': 'e'}, 
    9082 : {'odds1a': 'o', 'odds2a': 'e'}, 
    9083 : {'odds1a': 'o', 'odds2a': 'e'}, 
    9084 : {'odds1a': 'o', 'odds2a': 'e'}, 
    9085 : {'odds1a': 'o', 'odds2a': 'e'}, 
    9086 : {'odds1a': 'o', 'odds2a': 'e'},
    228 : {'odds1a': 'o', 'odds2a': 'u'},
    18 : {'odds1a': 'o', 'odds2a': 'u'},
    156 : {'odds1a': 'o', 'odds2a': 'u'}, 
    386 : {'odds1a': 'o', 'odds2a': 'u'}, 
    387 : {'odds1a': 'o', 'odds2a': 'u'}, 
    388 : {'odds1a': 'o', 'odds2a': 'u'}, 
    389 : {'odds1a': 'o', 'odds2a': 'u'}, 
    401 : {'odds1a': 'o', 'odds2a': 'u'}, 
    402 : {'odds1a': 'o', 'odds2a': 'u'}, 
    403 : {'odds1a': 'o', 'odds2a': 'u'}, 
    404 : {'odds1a': 'o', 'odds2a': 'u'}, 
    610 : {'odds1a': 'o', 'odds2a': 'u'}, 
    615 : {'odds1a': 'o', 'odds2a': 'u'}, 
    616 : {'odds1a': 'o', 'odds2a': 'u'}, 
    702 : {'odds1a': 'o', 'odds2a': 'u'}, 
    705 : {'odds1a': 'o', 'odds2a': 'u'}, 
    709 : {'odds1a': 'o', 'odds2a': 'u'}, 
    9003 : {'odds1a': 'o', 'odds2a': 'u'}, 
    9009 : {'odds1a': 'o', 'odds2a': 'u'}, 
    9013 : {'odds1a': 'o', 'odds2a': 'u'}, 
    9019 : {'odds1a': 'o', 'odds2a': 'u'}, 
    9025 : {'odds1a': 'o', 'odds2a': 'u'}, 
    9029 : {'odds1a': 'o', 'odds2a': 'u'}, 
    9035 : {'odds1a': 'o', 'odds2a': 'u'}, 
    9041 : {'odds1a': 'o', 'odds2a': 'u'}, 
    9047 : {'odds1a': 'o', 'odds2a': 'u'}, 
    9053 : {'odds1a': 'o', 'odds2a': 'u'}, 
    9058 : {'odds1a': 'o', 'odds2a': 'u'}, 
    9060 : {'odds1a': 'o', 'odds2a': 'u'}, 
    9070 : {'odds1a': 'o', 'odds2a': 'u'}, 
    9074 : {'odds1a': 'o', 'odds2a': 'u'},
    4 : {'cs00': '0:0', 'cs01': '0:1', 'cs02': '0:2', 'cs03': '0:3', 'cs04': '0:4', 'cs05': '0:5', 'cs10': '1:0', 'cs11': '1:1', 'cs12': '1:2', 'cs13': '1:3', 'cs14': '1:4', 'cs20': '2:0', 'cs21': '2:1', 'cs22': '2:2', 'cs23': '2:3', 'cs24': '2:4', 'cs30': '3:0', 'cs31': '3:1', 'cs32': '3:2', 'cs33': '3:3', 'cs34': '3:4', 'cs40': '4:0', 'cs41': '4:1', 'cs42': '4:2', 'cs43': '4:3', 'cs44': '4:4', 'cs50': '5:0'},
    5 : {"com1" : "1","com2" : "2","comx" : "x"},
    22 : {'com1': '1', 'com2': '2', 'comx': 'x'},
    28 : {'com1': '1', 'com2': '2', 'comx': 'x'},
    164 : {'com1': '1', 'com2': '2', 'comx': 'x'},
    167 : {'com1': '1', 'com2': '2', 'comx': 'x'},
    176 : {'com1': '1', 'com2': '2', 'comx': 'x'},
    177 : {'com1': '1', 'com2': '2', 'comx': 'x'},
    180 : {'com1': '1', 'com2': '2', 'comx': 'x'},
    430 : {'com1': '1', 'com2': '2', 'comx': 'x'},
    453 : {'com1': '1', 'com2': '2', 'comx': 'x'},
    477 : {'com1': '1', 'com2': '2', 'comx': 'x'},
    478 : {'com1': '1', 'com2': '2', 'comx': 'x'},
    2802 : {'com1': '1', 'com2': '2', 'comx': 'x'},
    6 : {'cs00': '0-1', 'cs01': '2-3', 'cs10': '4-6', 'cs11': '7-over'},
    13 : {'cs11': 'hy', 'cs10': 'hn', 'cs21': 'ay', 'cs20': 'an'},
    14 : {'cs00': '0:0', 'cs11': '1:1', 'cs21': '2:1', 'cs12': '1:2', 'cs22': '2:2'},
    127 : {'cs00': '0:0', 'cs11': '1:1', 'cs21': '2:1', 'cs12': '1:2', 'cs22': '2:2'},
    16 : {'cs11': '1:1', 'cs10': '1:0', 'cs12': '1:2', 'cs01': '0:1', 'cs00': '0:0', 'cs02': '0:2', 'cs21': '2:1', 'cs20': '2:0', 'cs22': '2:2'},
    24 : {'com1': '1x', 'comx': '12', 'com2': '2x'},
    186: {'cs10': 'hd', 'cs00': 'da', 'cs20': 'ha'},
    431 : {'cs10': 'hd', 'cs00': 'da', 'cs20': 'ha'},
    26 : {'com1': 'o', 'comx': 'n', 'com2': 'b'},
    30 : {'cs00': '0:0', 'cs01': '0:1', 'cs02': '0:2', 'cs03': '0:3', 'cs04': '0:4', 'cs10': '1:0', 'cs11': '1:1', 'cs12': '1:2', 'cs13': '1:3', 'cs20': '2:0', 'cs21': '2:1', 'cs22': '2:2', 'cs23': '2:3', 'cs30': '3:0', 'cs31': '3:1', 'cs32': '3:2', 'cs33': '3:3', 'cs40': '4:0'},
    121 : {'odds1a': 'x', 'odds2a': 'a'},
    122 : {'odds1a': 'h', 'odds2a': 'x'},
    126 : {'cs00': '0-1', 'cs01': '2-3', 'cs10': '4-over'},
    128 : {'cs11': 'oo', 'cs12': 'oe', 'cs21': 'eo', 'cs22': 'ee'},
    133 : {'com1': 'y', 'com2': 'n'},
    134 : {'com1': 'y', 'com2': 'n'},
    135 : {'com1': 'y', 'com2': 'n'},
    145 : {'com1': 'y', 'com2': 'n'},
    146 : {'com1': 'y', 'com2': 'n'},
    147 : {'com1': 'y', 'com2': 'n'},
    148 : {'com1': 'y', 'com2': 'n'},
    149 : {'com1': 'y', 'com2': 'n'},
    150 : {'com1': 'y', 'com2': 'n'},
    433 : {'com1': 'y', 'com2': 'n'},
    436 : {'com1': 'y', 'com2': 'n'},
    437 : {'com1': 'y', 'com2': 'n'},
    438 : {'com1': 'y', 'com2': 'n'},
    439 : {'com1': 'y', 'com2': 'n'},
    440 : {'com1': 'y', 'com2': 'n'},
    441 : {'com1': 'y', 'com2': 'n'},
    140 : {'cs10': '1h', 'cs20': '2h', 'cs00': 'tie'},
    141 : {'cs10': '1h', 'cs20': '2h', 'cs00': 'tie'},
    142 : {'cs10': '1h', 'cs20': '2h', 'cs00': 'tie'},
    442 : {'cs10': '1h', 'cs20': '2h', 'cs00': 'tie'},
    443 : {'cs10': '1h', 'cs20': '2h', 'cs00': 'tie'},
    444 : {'cs10': '1h', 'cs20': '2h', 'cs00': 'tie'},
    496 : {'cs10': '1h', 'cs20': '2h', 'cs00': 'tie'},
    410 : {'cs10': '1x', 'cs20': '2x', 'cs00': '12'},
    151 : {'cs10': '1x', 'cs20': '2x', 'cs00': '12'},
    159 : {'cs01': 'g0', 'cs02': 'g1', 'cs03': 'g2', 'cs04': 'g3', 'cs10': 'g4', 'cs20': 'g5', 'cs30': 'g6'},
    406 : {'cs01': 'g0', 'cs02': 'g1', 'cs03': 'g2', 'cs04': 'g3', 'cs10': 'g4', 'cs20': 'g5', 'cs30': 'g6'},
    161 : {'cs00': 'g0', 'cs01': 'g1', 'cs02': 'g2', 'cs03': 'g3'},
    162 : {'cs00': 'g0', 'cs01': 'g1', 'cs02': 'g2', 'cs03': 'g3'},
    181 : {'cs00': 'g0', 'cs01': 'g1', 'cs02': 'g2', 'cs03': 'g3'},
    182 : {'cs00': 'g0', 'cs01': 'g1', 'cs02': 'g2', 'cs03': 'g3'},
    407 : {'cs00': 'g0', 'cs01': 'g1', 'cs02': 'g2', 'cs03': 'g3'},
    409 : {'cs00': 'g0', 'cs01': 'g1', 'cs02': 'g2', 'cs03': 'g3'},
    143 : {'cs01': 'ho', 'cs00': 'hu', 'cs03': 'do', 'cs02': 'du', 'cs05': 'ao', 'cs04': 'au'},
    144 : {'cs01': 'ho', 'cs00': 'hu', 'cs03': 'do', 'cs02': 'du', 'cs05': 'ao', 'cs04': 'au'},
    163 : {'cs01': 'ho', 'cs00': 'hu', 'cs03': 'do', 'cs02': 'du', 'cs05': 'ao', 'cs04': 'au'},
    165 : {'cs00': '0:0', 'cs01': '1:0', 'cs02': '2:0', 'cs03': '0:1', 'cs04': '1:1', 'cs05': '0:2'},
    166 : {'cs21': '0:0', 'cs12': '1:0', 'cs20': '2:0', 'cs02': '3:0', 'cs30': '0:1', 'cs03': '1:1', 'cs31': '2:1', 'cs13': '0:2', 'cs32': '1:2', 'cs23': '0:3'},
    169 : {'cs01': '1-15', 'cs02': '16-30', 'cs03': '31-45', 'cs04': '46-60', 'cs10': '61-75', 'cs20': '76-90', 'cs30': 'none'},
    193 : {'cs01': '1-15', 'cs02': '16-30', 'cs03': '31-45', 'cs04': '46-60', 'cs10': '61-75', 'cs20': '76-90', 'cs30': 'none'},
    171 : {'cs01': 'h1', 'cs02': 'h2', 'cs03': 'h3', 'cs10': 'a1', 'cs20': 'a2', 'cs30': 'a3', 'cs00': 'ng', 'cs04': 'd'},
    408 : {'cs01': 'h1', 'cs02': 'h2', 'cs03': 'h3', 'cs10': 'a1', 'cs20': 'a2', 'cs30': 'a3', 'cs00': 'ng', 'cs04': 'd'},
    172 : {'cs01': 'hh', 'cs02': 'dh', 'cs03': 'ah', 'cs04': 'ha', 'cs10': 'da', 'cs20': 'aa', 'cs30': 'no'},
    415 : {'cs01': 'hh', 'cs02': 'dh', 'cs03': 'ah', 'cs04': 'ha', 'cs10': 'da', 'cs20': 'aa', 'cs30': 'no'},
    173 : {'odds1a': 'y', 'odds2a': 'n'},
    174 : {'odds1a': 'y', 'odds2a': 'n'},
    188 : {'odds1a': 'y', 'odds2a': 'n'},
    189 : {'odds1a': 'y', 'odds2a': 'n'},
    190 : {'odds1a': 'y', 'odds2a': 'n'},
    210 : {'odds1a': 'y', 'odds2a': 'n'},
    211 : {'odds1a': 'y', 'odds2a': 'n'},
    212 : {'odds1a': 'y', 'odds2a': 'n'},
    213 : {'odds1a': 'y', 'odds2a': 'n'},
    214 : {'odds1a': 'y', 'odds2a': 'n'},
    215 : {'odds1a': 'y', 'odds2a': 'n'},
    427 : {'odds1a': 'y', 'odds2a': 'n'},
    434 : {'odds1a': 'y', 'odds2a': 'n'},
    435 : {'odds1a': 'y', 'odds2a': 'n'},
    175 : {'cs00': 'hr', 'cs01': 'he', 'cs02': 'hp', 'cs03': 'ar', 'cs04': 'ae', 'cs05': 'ap'},
    179 : {'cs00': 'g0', 'cs11': 'g1', 'cs12': 'g2', 'cs21': 'g3', 'cs22': 'g4'},
    25 : {'odds1a': 'h', 'odds2a': 'a'},
    27 : {'odds1a': 'h', 'odds2a': 'a'},
    168 : {'odds1a': 'h', 'odds2a': 'a'},
    185 : {'odds1a': 'h', 'odds2a': 'a'},
    191 : {'odds1a': 'h', 'odds2a': 'a'},
    411 : {'odds1a': 'h', 'odds2a': 'a'},
    432 : {'odds1a': 'h', 'odds2a': 'a'},
    635 : {'odds1a': 'h', 'odds2a': 'a'},
    636 : {'odds1a': 'h', 'odds2a': 'a'},
    187 : {'cs10': 'g0', 'cs20': 'g1', 'cs00': 'g2'},
    192 : {'cs21': '1-10', 'cs12': '11-20', 'cs20': '21-30', 'cs02': '31-40', 'cs30': '41-50', 'cs03': '51-60', 'cs31': '61-70', 'cs13': '71-80', 'cs32': '81-90', 'cs23': 'none'},
    195 : {'cs00': '0-2', 'cs01': '3-4', 'cs02': '5-6', 'cs03': '7-over'},
    196 : {'cs00': '0-2', 'cs01': '3-4', 'cs02': '5-6', 'cs03': '7-over'},
    178 : {'odds1a': 'o', 'odds2a': 'u'},
    197 : {'odds1a': 'o', 'odds2a': 'u'},
    198 : {'odds1a': 'o', 'odds2a': 'u'},
    204 : {'odds1a': 'o', 'odds2a': 'u'},
    205 : {'odds1a': 'o', 'odds2a': 'u'},
    200 : {'cs00': '0-1', 'cs01': '2', 'cs02': '3', 'cs03': '4-over'},
    201 : {'cs00': '0-1', 'cs01': '2', 'cs02': '3', 'cs03': '4-over'},
    202 : {'cs10': '0-4', 'cs20': '5-6', 'cs00': '7-over'},
    206 : {'cs10': 'h', 'cs20': 'a', 'cs00': 'n'},
    207 : {'cs10': 'h', 'cs20': 'a', 'cs00': 'n'},
    208 : {'cs10': 'h', 'cs20': 'a', 'cs00': 'n'},
    209 : {'cs10': 'h', 'cs20': 'a', 'cs00': 'n'},
    221 : {'cs01': '2', 'cs10': '-2', 'cs02': '4', 'cs20': '-4', 'cs03': '8', 'cs30': '-8', 'cs04': '16', 'cs40': '-16', 'cs05': '32', 'cs50': '-32'},
    222 : {'cs01': '2', 'cs10': '-2', 'cs02': '4', 'cs20': '-4', 'cs03': '8', 'cs30': '-8', 'cs04': '16', 'cs40': '-16', 'cs05': '32', 'cs50': '-32', 'cs13': '128'},
    223 : {'cs00': '1', 'cs01': '2', 'cs02': '4', 'cs03': '8', 'cs04': '16', 'cs05': '32'},
    224 : {'cs00': '1', 'cs01': '2', 'cs02': '4', 'cs12': '64', 'cs13': '128'},
    225 : {'cs00': '1', 'cs01': '44'},
    226 : {'cs01': '26', 'cs02': '36', 'cs00': '1'},
    227 : {'cs01': '194', 'cs02': '4', 'cs00': '1'},
    383 : {'cs00': 'h', 'cs01': 'a'},
    384 : {'com1': 'o', 'com2': 'b', 'comx': 'n'},
    385 : {'com1': '1', 'com2': '2', 'comx': 'x'},
    391 : {'cs00': 'g4', 'cs01': 'g5', 'cs10': 'g6', 'cs11': 'g7', 'cs02': 'g8', 'cs12': 'g9+'},
    392 : {'cs10': '1-0', 'cs20': '2-0', 'cs21': '2-1', 'cs30': '3-0', 'cs31': '3-1', 'cs32': '3-2', 'cs41': '4-1', 'cs42': '4-2', 'cs43': '4-3', 'cs53': '5-3', 'cs54': '5-4', 'cs01': '0-1', 'cs02': '0-2', 'cs12': '1-2', 'cs03': '0-3', 'cs13': '1-3', 'cs23': '2-3', 'cs14': '1-4', 'cs24': '2-4', 'cs34': '3-4', 'cs35': '3-5', 'cs45': '4-5'},
    395 : {'cs10': 's', 'cs00': 'h', 'cs22': 'p', 'cs12': 'fk', 'cs02': 'og', 'cs21': 'ng'},
    396 : {'com1': '1', 'com2': '2', 'comx': 'x'},
    397 : {'cs01': 'h1', 'cs02': 'h2', 'cs03': 'h3+', 'cs04': 'd', 'cs10': 'a1', 'cs20': 'a2', 'cs30': 'a3+', 'cs00': 'ng'},
    398 : {'com1': '1x', 'com2': '2x', 'comx': '12'},
    399 : {'cs10': '1-0', 'cs20': '2-0', 'cs21': '2-1', 'cs30': '3-0', 'cs31': '3-1', 'cs01': '0-1', 'cs02': '0-2', 'cs12': '1-2', 'cs03': '0-3', 'cs00': '0-0', 'cs11': '1-1', 'cs22': '2-2'},
    405 : {'cs00': '0:0', 'cs01': '0:1', 'cs02': '0:2', 'cs03': '0:3', 'cs10': '1:0', 'cs11': '1:1', 'cs12': '1:2', 'cs13': '1:3', 'cs20': '2:0', 'cs21': '2:1', 'cs22': '2:2', 'cs23': '2:3', 'cs30': '3:0', 'cs31': '3:1', 'cs32': '3:2', 'cs33': '3:3', 'cs99': 'aos'},
    414 : {'cs00': '0:0', 'cs01': '0:1', 'cs02': '0:2', 'cs03': '0:3', 'cs10': '1:0', 'cs11': '1:1', 'cs12': '1:2', 'cs13': '1:3', 'cs20': '2:0', 'cs21': '2:1', 'cs22': '2:2', 'cs23': '2:3', 'cs30': '3:0', 'cs31': '3:1', 'cs32': '3:2', 'cs33': '3:3', 'cs99': 'aos'},
    412 : {'cs00': '0', 'cs01': '1', 'cs10': '2', 'cs11': '3-over'},
    413 : {'cs00': '0:0', 'cs01': '0:1', 'cs02': '0:2', 'cs03': '0:3', 'cs04': '0:4', 'cs10': '1:0', 'cs11': '1:1', 'cs12': '1:2', 'cs13': '1:3', 'cs14': '1:4', 'cs20': '2:0', 'cs21': '2:1', 'cs22': '2:2', 'cs23': '2:3', 'cs24': '2:4', 'cs30': '3:0', 'cs31': '3:1', 'cs32': '3:2', 'cs33': '3:3', 'cs34': '3:4', 'cs40': '4:0', 'cs41': '4:1', 'cs42': '4:2', 'cs43': '4:3', 'cs44': '4:4'},
    31 : {'winodds': '31', 'placeodds': '32'},
    417 : {'cs11': 'YH', 'cs12': 'YA', 'cs10': 'YD', 'cs01': 'NH', 'cs02': 'NA', 'cs30': 'ND'},
    456 : {'cs11': 'YH', 'cs12': 'YA', 'cs10': 'YD', 'cs01': 'NH', 'cs02': 'NA', 'cs30': 'ND'},
    418 : {'cs01': 'YO', 'cs02': 'YU', 'cs30': 'NO', 'cs03': 'NU'},
    457 : {'cs01': 'YO', 'cs02': 'YU', 'cs30': 'NO', 'cs03': 'NU'},
    473 : {'cs00': '0-5', 'cs01': '6-8', 'cs10': '9-11', 'cs11': '12-14', 'cs02': '15+'},
    474 : {'cs00': '0-2', 'cs01': '3-4', 'cs10': '5-6', 'cs11': '7+'},
    458 : {'com1': '1', 'com2': '2', 'comx': 'X'},
    459 : {'com1': '1', 'com2': '2', 'comx': 'X'},
    419 : {'cs10': '1H', 'cs20': '2H', 'cs11': 'N'},
    420 : {'cs10': '1H', 'cs20': '2H', 'cs11': 'N'},
    421 : {'cs10': '1H', 'cs20': '2H', 'cs11': 'N'},
    422 : {'cs00': 'H', 'cs01': 'A', 'cs11': 'N'},
    423 : {'cs00': 'H', 'cs01': 'A', 'cs11': 'N'},
    424 : {'cs10': 'S', 'cs00': 'H', 'cs22': 'P', 'cs12': 'FK', 'cs02': 'OG', 'cs21': 'NG'},
    426 : {'cs00': 'H1', 'cs01': 'H2+', 'cs11': 'D', 'cs02': 'A1', 'cs12': 'A2+', 'cs21': 'NG'},
    429 : {'cs22': '0', 'cs00': '1', 'cs10': '2', 'cs11': '3-over'},
    445 : {'cs11': 'YY', 'cs12': 'YN', 'cs21': 'NY', 'cs22': 'NN'},
    446 : {'cs11': 'YY', 'cs12': 'YN', 'cs21': 'NY', 'cs22': 'NN'},
    447 : {'cs11': 'YY', 'cs12': 'YN', 'cs21': 'NY', 'cs22': 'NN'},
    448 : {'cs11': 'H', 'cs01': 'A', 'cs00': 'NG'},
    449 : {'cs01': '1XO', 'cs00': '1XU', 'cs03': '12O', 'cs02': '12U', 'cs05': '2XO', 'cs04': '2XU'},
    450 : {'cs01': 'OO', 'cs02': 'OU', 'cs30': 'EO', 'cs03': 'EU'},
    451 : {'cs11': 'Y1X', 'cs12': 'Y12', 'cs10': 'Y2X', 'cs01': 'N1X', 'cs02': 'N12', 'cs30': 'N2X'},
    452 : {'cs00': '1H', 'cs01': '2H'},
    497 : {'cs00': '1H', 'cs01': '2H'},
    454 : {'cs02': '1XH', 'cs03': '12H', 'cs04': '2XH', 'cs10': '1XA', 'cs20': '12A', 'cs30': '2XA', 'cs00': 'NG'},
    455 : {'cs30': '1-10', 'cs01': '11-20', 'cs10': '21-30', 'cs11': '31-40', 'cs02': '41-50', 'cs12': '51-60', 'cs22': '61-70', 'cs21': '71-80', 'cs20': '81-90', 'cs00': 'NG'},
    460 : {'cs00': 'h', 'cs01': 'a'},
    486 : {'com1': 'H', 'com2': 'A', 'comx': 'N'},
    487 : {'com1': 'H', 'com2': 'A', 'comx': 'N'},
    601 : {'cs01': 'H1-2', 'cs02': 'H3-6', 'cs03': 'H7-9', 'cs04': 'H10-13', 'cs05': 'H14-16', 'cs11': 'H17-20', 'cs12': 'H21+', 'cs13': 'A1-2', 'cs14': 'A3-6', 'cs21': 'A7-9', 'cs22': 'A10-13', 'cs23': 'A14-16', 'cs24': 'A17-20', 'cs30': 'A21+'},
    602 : {'cs01': 'H1-5', 'cs02': 'H6-10', 'cs03': 'H11-15', 'cs04': 'H16-20', 'cs05': 'H21-25', 'cs11': 'H26+', 'cs12': 'A1-5', 'cs13': 'A6-10', 'cs14': 'A11-15', 'cs21': 'A16-20', 'cs22': 'A21-25', 'cs23': 'A26+'},
    608 : {'cs01': 'H1-5', 'cs02': 'H6-10', 'cs03': 'H11-15', 'cs04': 'H16-20', 'cs05': 'H21-25', 'cs11': 'H26+', 'cs12': 'D', 'cs13': 'A1-5', 'cs14': 'A6-10', 'cs21': 'A11-15', 'cs22': 'A16-20', 'cs23': 'A21-25', 'cs24': 'A26+'},
    614 : {'cs01': 'H1-4', 'cs02': 'H5-8', 'cs03': 'H9+', 'cs04': 'D', 'cs05': 'A1-4', 'cs11': 'A5-8', 'cs12': 'A9+'},
    618 : {'cs01': '0', 'cs02': '1', 'cs03': '2', 'cs04': '3', 'cs05': '4', 'cs11': '5', 'cs12': '6', 'cs13': '7', 'cs14': '8', 'cs21': '9'},
    619 : {'cs01': '0', 'cs02': '1', 'cs03': '2', 'cs04': '3', 'cs05': '4', 'cs11': '5', 'cs12': '6', 'cs13': '7', 'cs14': '8', 'cs21': '9'},
    620 : {'cs01': '0', 'cs02': '1', 'cs03': '2', 'cs04': '3', 'cs05': '4', 'cs11': '5', 'cs12': '6', 'cs13': '7', 'cs14': '8', 'cs21': '9'},
    621 : {'cs01': '0', 'cs02': '1', 'cs03': '2', 'cs04': '3', 'cs05': '4', 'cs11': '5', 'cs12': '6', 'cs13': '7', 'cs14': '8', 'cs21': '9'},
    622 : {'cs01': '0', 'cs02': '1', 'cs03': '2', 'cs04': '3', 'cs05': '4', 'cs11': '5', 'cs12': '6', 'cs13': '7', 'cs14': '8', 'cs21': '9'},
    623 : {'cs01': '0', 'cs02': '1', 'cs03': '2', 'cs04': '3', 'cs05': '4', 'cs11': '5', 'cs12': '6', 'cs13': '7', 'cs14': '8', 'cs21': '9'},
    624 : {'cs01': '0', 'cs02': '1', 'cs03': '2', 'cs04': '3', 'cs05': '4', 'cs11': '5', 'cs12': '6', 'cs13': '7', 'cs14': '8', 'cs21': '9'},
    625 : {'cs01': '0', 'cs02': '1', 'cs03': '2', 'cs04': '3', 'cs05': '4', 'cs11': '5', 'cs12': '6', 'cs13': '7', 'cs14': '8', 'cs21': '9'},
    626 : {'cs01': '0', 'cs02': '1', 'cs03': '2', 'cs04': '3', 'cs05': '4', 'cs11': '5', 'cs12': '6', 'cs13': '7', 'cs14': '8', 'cs21': '9'},
    627 : {'cs01': '0', 'cs02': '1', 'cs03': '2', 'cs04': '3', 'cs05': '4', 'cs11': '5', 'cs12': '6', 'cs13': '7', 'cs14': '8', 'cs21': '9'},
    628 : {'cs01': '0', 'cs02': '1', 'cs03': '2', 'cs04': '3', 'cs05': '4', 'cs11': '5', 'cs12': '6', 'cs13': '7', 'cs14': '8', 'cs21': '9'},
    629 : {'cs01': '0', 'cs02': '1', 'cs03': '2', 'cs04': '3', 'cs05': '4', 'cs11': '5', 'cs12': '6', 'cs13': '7', 'cs14': '8', 'cs21': '9'},
    630 : {'com1': '1', 'comx': 'X', 'com2': '2'},
    631 : {'cs10': 'hd', 'cs02': 'da', 'cs12': 'ha'},
    632 : {'cs00': 'oooo', 'cs01': 'oooe', 'cs02': 'ooeo', 'cs03': 'oeoo', 'cs04': 'eooo', 'cs05': 'eeee', 'cs10': 'eeeo', 'cs11': 'eeoe', 'cs12': 'eoee', 'cs13': 'oeee', 'cs14': 'ooee', 'cs24': 'oeoe', 'cs30': 'eoeo', 'cs21': 'eeoo', 'cs22': 'eooe', 'cs23': 'oeeo'},
    633 : {'cs11': 'hh', 'cs10': 'hd', 'cs12': 'ha', 'cs01': 'dh', 'cs00': 'dd', 'cs02': 'da', 'cs21': 'ah', 'cs23': 'ad', 'cs22': 'aa'},
    634 : {'cs11': 'hh', 'cs10': 'hd', 'cs12': 'ha', 'cs01': 'dh', 'cs00': 'dd', 'cs02': 'da', 'cs21': 'ah', 'cs23': 'ad', 'cs22': 'aa'},
    640 : {'cs00': '0', 'cs01': '1'},
    637 : {'odds1a': 'h', 'odds2a':'a'},
    9400 : {'odds1a': 'h', 'odds2a': 'a'},
    9401 : {'odds1a': 'h', 'odds2a': 'a'},
    9442 : {'odds1a': 'h', 'odds2a': 'a'},
    9443 : {'odds1a': 'h', 'odds2a': 'a'},
    638 : {'odds1a': 'o', 'odds2a': 'u'},
    639 : {'odds1a': 'o', 'odds2a': 'u'},
    641 : {'odds1a': 'o', 'odds2a': 'u'},
    9404 : {'odds1a': 'o', 'odds2a': 'u'},
    9405 : {'odds1a': 'o', 'odds2a': 'u'},
    9406 : {'odds1a': 'o', 'odds2a': 'u'},
    9407 : {'odds1a': 'o', 'odds2a': 'u'},
    9408 : {'odds1a': 'o', 'odds2a': 'u'},
    9409 : {'odds1a': 'o', 'odds2a': 'u'},
    9410 : {'odds1a': 'o', 'odds2a': 'u'},
    9411 : {'odds1a': 'o', 'odds2a': 'u'},
    9412 : {'odds1a': 'o', 'odds2a': 'u'},
    9413 : {'odds1a': 'o', 'odds2a': 'u'},
    9414 : {'odds1a': 'o', 'odds2a': 'u'},
    9415 : {'odds1a': 'o', 'odds2a': 'u'},
    9416 : {'odds1a': 'o', 'odds2a': 'u'},
    9417 : {'odds1a': 'o', 'odds2a': 'u'},
    9418 : {'odds1a': 'o', 'odds2a': 'u'},
    9419 : {'odds1a': 'o', 'odds2a': 'u'},
    9420 : {'odds1a': 'o', 'odds2a': 'u'},
    9421 : {'odds1a': 'o', 'odds2a': 'u'},
    9422 : {'odds1a': 'o', 'odds2a': 'u'},
    9423 : {'odds1a': 'o', 'odds2a': 'u'},
    9428 : {'odds1a': 'o', 'odds2a': 'u'},
    9429 : {'odds1a': 'o', 'odds2a': 'u'},
    9430 : {'odds1a': 'o', 'odds2a': 'u'},
    9431 : {'odds1a': 'o', 'odds2a': 'u'},
    9432 : {'odds1a': 'o', 'odds2a': 'u'},
    9433 : {'odds1a': 'o', 'odds2a': 'u'},
    9446 : {'odds1a': 'o', 'odds2a': 'u'},
    9447 : {'odds1a': 'o', 'odds2a': 'u'},
    9449 : {'odds1a': 'o', 'odds2a': 'u'},
    9450 : {'odds1a': 'o', 'odds2a': 'u'},
    9452 : {'odds1a': 'o', 'odds2a': 'u'},
    9453 : {'odds1a': 'o', 'odds2a': 'u'},
    9454 : {'odds1a': 'o', 'odds2a': 'u'},
    9455 : {'odds1a': 'o', 'odds2a': 'u'},
    9460 : {'odds1a': 'o', 'odds2a': 'u'},
    9461 : {'odds1a': 'o', 'odds2a': 'u'},
    9604 : {'odds1a': 'o', 'odds2a': 'u'},
    9607 : {'odds1a': 'o', 'odds2a': 'u'},
    9608 : {'odds1a': 'o', 'odds2a': 'u'},
    9609 : {'odds1a': 'o', 'odds2a': 'u'},
    9610 : {'odds1a': 'o', 'odds2a': 'u'},
    9611 : {'odds1a': 'o', 'odds2a': 'u'},
    9612 : {'odds1a': 'o', 'odds2a': 'u'},
    9613 : {'odds1a': 'o', 'odds2a': 'u'},
    9614 : {'odds1a': 'o', 'odds2a': 'u'},
    9490 : {'cs01': '0', 'cs02': '1', 'cs03 ': '2', 'cs04 ': '3', 'cs05 ': '4', 'cs11 ': 'ao'},
    9491 : {'cs01': '0', 'cs02': '1', 'cs03 ': '2', 'cs04 ': '3', 'cs05 ': '4', 'cs11 ': 'ao'},
    9496 : {'odds1a': 'o', 'odds2a': 'e'},
    9497 : {'odds1a': 'o', 'odds2a': 'e'},
    9498 : {'odds1a': 'o', 'odds2a': 'e'},
    9499 : {'odds1a': 'o', 'odds2a': 'e'},
    9500 : {'odds1a': 'o', 'odds2a': 'e'},
    9501 : {'odds1a': 'o', 'odds2a': 'e'},
    9502 : {'odds1a': 'o', 'odds2a': 'e'},
    9503 : {'odds1a': 'o', 'odds2a': 'e'},
    9504 : {'odds1a': 'o', 'odds2a': 'e'},
    9505 : {'odds1a': 'o', 'odds2a': 'e'},
    9506 : {'odds1a': 'o', 'odds2a': 'e'},
    9507 : {'odds1a': 'o', 'odds2a': 'e'},
    9508 : {'odds1a': 'o', 'odds2a': 'e'},
    9509 : {'odds1a': 'o', 'odds2a': 'e'},
    9510 : {'odds1a': 'o', 'odds2a': 'e'},
    9511 : {'odds1a': 'o', 'odds2a': 'e'},
    9512 : {'odds1a': 'o', 'odds2a': 'e'},
    9513 : {'odds1a': 'o', 'odds2a': 'e'},
    9514 : {'odds1a': 'o', 'odds2a': 'e'},
    9515 : {'odds1a': 'o', 'odds2a': 'e'},
    9516 : {'odds1a': 'o', 'odds2a': 'e'},
    9517 : {'odds1a': 'o', 'odds2a': 'e'},
    9518 : {'odds1a': 'o', 'odds2a': 'e'},
    9519 : {'odds1a': 'o', 'odds2a': 'e'},
    9527 : {'odds1a': 'o', 'odds2a': 'e'},
    9528 : {'odds1a': 'o', 'odds2a': 'e'},
    9530 : {'odds1a': 'o', 'odds2a': 'e'},
    9532 : {'odds1a': 'o', 'odds2a': 'e'},
    9533 : {'odds1a': 'o', 'odds2a': 'e'},
    9605 : {'odds1a': 'o', 'odds2a': 'e'},
    9538 : {'cs01': '1b', 'cs02': 'xb', 'cs03 ': '2b', 'cs04 ': '1l', 'cs05 ': 'xl', 'cs11 ': '2l'},
    9539 : {'cs01': 'hb', 'cs02': 'hl', 'cs03 ': 'ab', 'cs04 ': 'al'},
    9540 : {'cs01': 'hb', 'cs02': 'hl', 'cs03 ': 'ab', 'cs04 ': 'al'},
    642 : {'cs00': 'h12', 'cs01': 'h13', 'cs02': 'h14', 'cs03': 'h23', 'cs04': 'h24', 'cs05': 'h34', 'cs10': 'a12', 'cs11': 'a13', 'cs12': 'a14', 'cs13': 'a23', 'cs14': 'a24', 'cs21': 'a34', 'cs22': 'aos12', 'cs23': 'aos13', 'cs24': 'aos14', 'cs30': 'aos23', 'cs31': 'aos24', 'cs32': 'aos34'},
    643 : {'cs01': '1q', 'cs02': '2q', 'cs03': '3q', 'cs04': '4q', 'cs00': 'tie'},
    644 : {'cs21': '2:1', 'cs30': '3:0', 'cs31': '3:1', 'cs40': '4:0', 'cs22': '2:2', 'cs12': '1:2', 'cs03': '0:3', 'cs13': '1:3', 'cs04': '0:4', 'cs00': 'aos'},
    645 : {'cs11': 'hh', 'cs10': 'hd', 'cs12': 'ha', 'cs01': 'dh', 'cs02': 'da', 'cs21': 'ah', 'cs23': 'ad', 'cs22': 'aa'},
    703 : {'cs02': '0-2', 'cs12': '1-2', 'cs20': '2-0', 'cs21': '2-1'},
    711 : {'cs01': 'H1-2', 'cs02': 'H3-5', 'cs03': 'H6-8', 'cs04': 'H9+', 'cs05': 'A1-2', 'cs11': 'A3-5', 'cs12': 'A6-8', 'cs13': 'A9+'},
    2808 : {'cs01': 'H1-5', 'cs02': 'H6-10', 'cs03': 'H11+', 'cs12': 'D', 'cs04': 'A1-5', 'cs05': 'A6-10', 'cs11': 'A11+'},
    2807 : {'cs01': 'H1-5', 'cs02': 'H6-10', 'cs03': 'H11+', 'cs04': 'A1-5', 'cs05': 'A6-10', 'cs11': 'A11+'},
    482 : {'odds1a': 'o', 'odds2a': 'u'},
    483 : {'odds1a': 'o', 'odds2a': 'u'},
    484 : {'odds1a': 'o', 'odds2a': 'u'},
    485 : {'odds1a': 'o', 'odds2a': 'u'},
    461 : {'odds1a': 'o', 'odds2a': 'u'},
    462 : {'odds1a': 'o', 'odds2a': 'u'},
    463 : {'odds1a': 'o', 'odds2a': 'u'},
    464 : {'odds1a': 'o', 'odds2a': 'u'},
    2811 : {'odds1a': 'o', 'odds2a': 'u'},
    2812 : {'odds1a': 'o', 'odds2a': 'u'},
    7901 : {'odds1a': 'o', 'odds2a': 'u'},
    475 : {'cs00': 'o', 'cs01': 'e', 'cs10': 'u'},
    476 : {'cs00': 'o', 'cs01': 'e', 'cs10': 'u'},
    494 : {'cs10': '1-0', 'cs20': '2-0', 'cs21': '2-1', 'cs30': '3-0', 'cs31': '3-1', 'cs32': '3-2', 'cs40': '4-0', 'cs41': '4-1', 'cs42': '4-2', 'cs43': '4-3', 'cs50': '5-0', 'cs51': '5-1', 'cs52': '5-2', 'cs53': '5-3', 'cs54': '5-4', 'cs01': '0-1', 'cs02': '0-2', 'cs12': '1-2', 'cs03': '0-3', 'cs13': '1-3', 'cs23': '2-3', 'cs04': '0-4', 'cs14': '1-4', 'cs24': '2-4', 'cs34': '3-4', 'cs05': '0-5', 'cs15': '1-5', 'cs25': '2-5', 'cs35': '3-5', 'cs45': '4-5', 'cs00': '0-0', 'cs11': '1-1', 'cs22': '2-2', 'cs33': '3-3', 'cs44': '4-4', 'cs99': 'aos'},
    495 : {'cs10': '1-0', 'cs20': '2-0', 'cs21': '2-1', 'cs30': '3-0', 'cs31': '3-1', 'cs32': '3-2', 'cs40': '4-0', 'cs41': '4-1', 'cs42': '4-2', 'cs43': '4-3', 'cs50': '5-0', 'cs51': '5-1', 'cs52': '5-2', 'cs53': '5-3', 'cs54': '5-4', 'cs01': '0-1', 'cs02': '0-2', 'cs12': '1-2', 'cs03': '0-3', 'cs13': '1-3', 'cs23': '2-3', 'cs04': '0-4', 'cs14': '1-4', 'cs24': '2-4', 'cs34': '3-4', 'cs05': '0-5', 'cs15': '1-5', 'cs25': '2-5', 'cs35': '3-5', 'cs45': '4-5', 'cs00': '0-0', 'cs11': '1-1', 'cs22': '2-2', 'cs33': '3-3', 'cs44': '4-4', 'cs99': 'aos'},
    8103 : {'cs01': 'sp', 'cs02': 'su', 'cs03': 'au', 'cs04': 'wi'},
    8105 : {'cs01': 'bo', 'cs02': 'be', 'cs11': 'so', 'cs12': 'se'},
    9088 : {'cs00': '0:0', 'cs01': '0:1', 'cs02': '0:2', 'cs03': '0:3', 'cs04': '0:4', 'cs05': '0:5', 'cs10': '1:0', 'cs11': '1:1', 'cs12': '1:2', 'cs13': '1:3', 'cs14': '1:4', 'cs20': '2:0', 'cs21': '2:1', 'cs22': '2:2', 'cs23': '2:3', 'cs24': '2:4', 'cs30': '3:0', 'cs31': '3:1', 'cs32': '3:2', 'cs33': '3:3', 'cs34': '3:4', 'cs40': '4:0', 'cs41': '4:1', 'cs42': '4:2', 'cs43': '4:3', 'cs44': '4:4', 'cs50': '5:0'},
    468 : {'cs10':'h','cs11':'h','cs12':'h','cs13':'h','cs14':'h','cs01':'a','cs02':'a','cs03':'a','cs04':'a','cs05':'a'},
    469 : {'cs10':'h','cs11':'h','cs12':'h','cs13':'h','cs14':'h','cs01':'a','cs02':'a','cs03':'a','cs04':'a','cs05':'a'},
    9712 : {'odds1a': 'n', 'odds2a': 'y'},
    9713 : {'odds1a': 'n', 'odds2a': 'y'},
    9714 : {'odds1a': 'n', 'odds2a': 'y'},
    9715 : {'odds1a': 'n', 'odds2a': 'y'},
    9716 : {'odds1a': 'n', 'odds2a': 'y'},
    9717 : {'odds1a': 'n', 'odds2a': 'y'},
    9718 : {'odds1a': 'n', 'odds2a': 'y'},
    9719 : {'odds1a': 'n', 'odds2a': 'y'},
    9720 : {'odds1a': 'n', 'odds2a': 'y'},
    9721 : {'odds1a': 'n', 'odds2a': 'y'},
    9722 : {'odds1a': 'n', 'odds2a': 'y'},
    9723 : {'odds1a': 'n', 'odds2a': 'y'},
    9724 : {'odds1a': 'n', 'odds2a': 'y'},
    9725 : {'odds1a': 'n', 'odds2a': 'y'},
    9726 : {'odds1a': 'n', 'odds2a': 'y'},
    9727 : {'odds1a': 'n', 'odds2a': 'y'},
    9728 : {'odds1a': 'n', 'odds2a': 'y'},
    9729 : {'odds1a': 'n', 'odds2a': 'y'},
    9541 : {'odds1a': 'n', 'odds2a': 'y'},
    9542 : {'odds1a': 'n', 'odds2a': 'y'},
    9543 : {'odds1a': 'n', 'odds2a': 'y'},
    9544 : {'odds1a': 'n', 'odds2a': 'y'},
    9545 : {'odds1a': 'n', 'odds2a': 'y'},
    9546 : {'odds1a': 'n', 'odds2a': 'y'},
    9547 : {'odds1a': 'n', 'odds2a': 'y'},
    9548 : {'odds1a': 'n', 'odds2a': 'y'},
    9549 : {'odds1a': 'n', 'odds2a': 'y'},
    9550 : {'odds1a': 'n', 'odds2a': 'y'},
    9551 : {'odds1a': 'n', 'odds2a': 'y'},
    9552 : {'odds1a': 'n', 'odds2a': 'y'},
    9559 : {'odds1a': 'n', 'odds2a': 'y'},
    9560 : {'odds1a': 'n', 'odds2a': 'y'},
    9561 : {'odds1a': 'n', 'odds2a': 'y'},
    9562 : {'odds1a': 'n', 'odds2a': 'y'},
    9563 : {'odds1a': 'n', 'odds2a': 'y'},
    9564 : {'odds1a': 'n', 'odds2a': 'y'},
    9566 : {'odds1a': 'n', 'odds2a': 'y'},
    9567 : {'odds1a': 'n', 'odds2a': 'y'},
    9569 : {'odds1a': 'n', 'odds2a': 'y'},
    9570 : {'odds1a': 'n', 'odds2a': 'y'},
    9572 : {'odds1a': 'n', 'odds2a': 'y'},
    9573 : {'odds1a': 'n', 'odds2a': 'y'},
    9574 : {'odds1a': 'n', 'odds2a': 'y'},
    9575 : {'odds1a': 'n', 'odds2a': 'y'},
    9580 : {'odds1a': 'n', 'odds2a': 'y'},
    9581 : {'odds1a': 'n', 'odds2a': 'y'},
    9582 : {'odds1a': 'n', 'odds2a': 'y'},
    9583 : {'odds1a': 'n', 'odds2a': 'y'},
    9584 : {'odds1a': 'n', 'odds2a': 'y'},
    9585 : {'odds1a': 'n', 'odds2a': 'y'},
    9576 : {'odds1a': 'n', 'odds2a': 'y'},
    9577 : {'odds1a': 'n', 'odds2a': 'y'},
    9578 : {'odds1a': 'n', 'odds2a': 'y'},
    9579 : {'odds1a': 'n', 'odds2a': 'y'},
}
