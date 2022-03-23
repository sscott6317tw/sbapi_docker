#In[]
from bs4 import BeautifulSoup
import time
from Common import Common
import requests
import urllib3
from  Logger import create_logger 
from fake_useragent import UserAgent

urllib3.disable_warnings()

class Stress(Common):
    def __init__(self,url,sec_times,stop_times):
        super().__init__(sec_times,stop_times)
        self.url = url
        self.Ip_list = []
        self.log = create_logger(r"\AutoTest", 'test')

        #self.host = host

    

    def Url(self):# 請求 URL  func
        session = requests.Session()
        #ua = UserAgent()
        #fake = ua.random
        self.headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            
             }
           
        r = session.get(self.url,timeout=10,headers=self.headers,verify=False)
        

        url = self.return_IP(r)
        
        self.Ip_list.append(url)
    
    def count_list(self,IP_list):# 計算 獲得IP count
        a = set(IP_list)#重複濾掉,就不用每個都loop
        combo_ip = len(a)# 多少種不同ip
        for i in a:
            num = IP_list.count(i)
            print('%s : %s'%(i,num))
            if 'response 有誤' in i:
                combo_ip = combo_ip - 1

        self.log.info('%s 個不同IP'%combo_ip )

    
    def return_loading_balance(self):

        self.log.info('url: %s'%self.url)
        self.threads( [self.Url] ) 
        #self.log.info('ip 解析 device : %s'%self.Parsing)
        self.count_list(IP_list = self.Ip_list )
        
        self.log.info('執行次數: %s'%len(self.Ip_list) )
 

#In[]
'''
主程式執行
參數說明:  
sec_times: 併發, stop_times: 幾秒後結束,
'''
stess_ini = Stress(url= 'http://fbw.oriental-game.com/whoami.aspx?key=9527',
sec_times= 1 , stop_times = 1 ).return_loading_balance()





