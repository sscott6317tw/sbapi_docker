#In[]
import requests,subprocess
from selenium import webdriver
import threading,time

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
   
    def get_driver(self):

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
        game_dict = {'Soccer': {'gameid': 1},'Basketball': {'gameid': 2},'Football': {'gameid': 3},'Ice Hockey': {'gameid': 4},'Tennis': {'gameid': 5},'Volleyball': {'gameid': 6}\
            ,'Snooker/Pool': {'gameid': 7},'Baseball': {'gameid': 8},'Badminton': {'gameid': 9},'Golf': {'gameid': 10},'Motorsports': {'gameid': 11},'Swimming': {'gameid': 12},\
            'Politics': {'gameid': 13},'Water Polo': {'gameid': 14},'Diving': {'gameid': 15},'Boxing/MMA': {'gameid': 16},'Archery': {'gameid': 17},'Table Tennis': {'gameid': 18},\
            'Weightlifting': {'gameid':19},'Canoeing': {'gameid': 20},'Gymnastics': {'gameid': 21},'Athletics': {'gameid': 22},'Equestrian': {'gameid': 23},'Handball': {'gameid': 24},\
            'Darts': {'gameid': 25},'Field Hockey': {'gameid': 28},'Winter Sports': {'gameid': 29},'Squash': {'gameid': 30},'Entertainment': {'gameid': 31},'Netball': {'gameid': 32},\
            'Cycling': {'gameid': 33},'Fencing': {'gameid': 34},'Judo': {'gameid': 35},'M.Pentathlon': {'gameid': 36},'Rowing': {'gameid': 37},'Sailing': {'gameid': 38},\
            'Shooting': {'gameid': 39},'Taekwondo': {'gameid': 40},'Triathlon': {'gameid': 41},'Wrestling': {'gameid': 42},'E-Sports': {'gameid': 43},'Muay Thai': {'gameid': 44},\
            'Beach Volleyball': {'gameid': 45},'Unknown sport (Thai sport)': {'gameid':46},'Kabaddi': {'gameid': 47},'Sepak Takraw': {'gameid': 48},'Futsal': {'gameid': 49},\
            'Cricket': {'gameid': 50},'Beach Soccer': {'gameid': 51},'Poker': {'gameid': 52},'Chess': {'gameid': 53},'Olympics': {'gameid': 54},'Finance': {'gameid': 55},\
            'Lotto': {'gameid': 56},'Other Sports': {'gameid': 99}
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


class Env:
    def __init__(self):
        self.api_url_dict = { 'mobile': {'W88':  'https://ismart.w2sports.com/apilogin' , 
        'Bbin': 'http://ismart.playbooksb.com/apilogin', '12Bet': 'http://ismart.wew77.com/apilogin',
        '11Bet': 'http://l9j7mb.pg5688.com/apilogin', 'Alog': 'https://ismart.dafabet.com/apilogin',
        'Ae88': 'http://u022mb.fx9888.com/apilogin' , 'Senibet':  'http://m2s8mb.fx9888.com/apilogin',
        'Fun88' : 'http://ismart.fun88.com/apilogin', 'Yibo': 'http://e7b8mb.pg5688.com/apilogin' , 
        'Xtu168': 'http://g5a1mb.fx9888.com/apilogin' ,
        
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