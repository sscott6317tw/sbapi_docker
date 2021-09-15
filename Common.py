import requests
from selenium import webdriver
import threading,time

class Common:
    '''
    sec_times: 併發, stop_times: 幾秒後結束
    '''
    def __init__(self,sec_times,stop_times):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        self.session = requests.Session()
        self.sec_times = sec_times
        self.stop_times = stop_times
   
    def get_driver(self):
        while True:
            try:
                chrome_options = webdriver.ChromeOptions()
                chrome_options.add_argument("--headless") #無頭模式
                driver = webdriver.Chrome(chrome_options = chrome_options,
                executable_path= "chromedriver.exe")
                self.dr = driver
                return self.dr
            except :
                time.sleep(1)

    def threads(self):# 併發邏輯
        print('同時併發: %s次, %s 秒鐘後結束'%(self.sec_times,self.stop_times ) )
        self.time_start = time.time() #開始計時
        self.time_end = time.time()
        str_time= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.time_start))
        print('start: %s'%str_time)
        while self.time_end - self.time_start <= self.stop_times:# 當程式執行超過指定時間 ,就break
            threads = []
            for i in range(self.sec_times):
                t  = threading.Thread(target= self.Url)
                threads.append(t)
            for i in threads:
                i.start()
            for i in threads:
                i.join()
            self.time_end  = time.time() #開始計時

    def game_mapping(self, sport):# 丟sport 參數, 回傳 gameid . 給 ShowAllOdds 街口使用
        game_dict = {'Cricket': {'gameid': 50} ,'Soccer': {'gameid': 1} , 'Basketball': {'gameid': 2}
            }
        return game_dict[sport]['gameid']


    def Odds_Tran(self, odds):# Marlay 轉 Dec Odds  , 在betting 時會用
        if float(odds) < 0:# 小於0, 跟china一樣, 只是多加1
            confirm_odds = round(abs(  int(1/ float(odds)*100))+100)   /100  
        else:# odds +1 
            confirm_odds = round(float(odds) * 100 + 100) / 100
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
