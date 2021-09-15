#In[]
from bs4 import BeautifulSoup
import time
from Common import Common

class Stress(Common):
    def __init__(self,url,sec_times,stop_times,host=""):
        super().__init__(sec_times,stop_times)
        self.url = url
        self.Ip_list = []
        self.host = host

    def return_IP(self,r):# 抓取 response的 IP
        html = BeautifulSoup(r.text,'lxml')# type為 bs4類型
        taglist = html.find_all('tr')
        for trtag in taglist:  
            tdlist = trtag.find_all('td')
            if tdlist[1].text == "":
                continue
            return(tdlist[1].text)
    
    def Url(self):# 請求 URL  func
        if  self.host == '':
            r = self.session.get(self.url,timeout=10)
        else:
            self.headers['Host'] = self.host
            r = self.session.get(self.url,timeout=10,headers=self.headers)
        url = self.return_IP(r)
        self.Ip_list.append(url)
    
    def count_list(self,IP_list):# 計算 獲得IP count
        a = set(IP_list)#重複濾掉,就不用每個都loop
        for i in a:
            num = IP_list.count(i)
            print('%s : %s'%(i,num))

    
    def return_loading_balance(self):
        self.threads()  
        self.count_list(IP_list = self.Ip_list )
        print('total: %s'%len(self.Ip_list) )
        str_end =  time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.time_end ))
        print('end: %s'%str_end)
        print('time cost',self.time_end -self.time_start,'s')

#In[]
'''
主程式執行
參數說明:  
sec_times: 併發, stop_times: 幾秒後結束, host: 可加可不加
'''
stess_ini = Stress(url= 'http://ismart.l0099.ti4one.com/whoami.aspx',
sec_times= 5, stop_times = 1).return_loading_balance()





