
#In[]
import Api_Object
from collections import defaultdict
from Common import Env
from  Logger import create_logger 
from Sql_Con import DataBaseInfo


log = create_logger(r"\AutoTest", 'test')

class Site_Api(Env):
    def __init__(self):
        super().__init__()
        #self.response_dict = {} #defaultdict(list)#  用來存放 各site 各api 請求的 回復
        self.site_dict = {}# key 為 site , value 為 response_dict
        
        self.log = log
        #print( self.url_dict)

    def site_api_betting_process(self , site ,device = 'mobile'):
        self.login_site = '%s - %s'%(device, site)
        self.response_dict = {}
        
        # 登入
        try:
            if site in ['Xtu168','Senibet', 'Yibo', 'Alog', 'Fun88', '11Bet']:
                login_user = 'qatest03'
            else:
                login_user = 'twqa09'
            self.site_dict[site] = self.response_dict
            
            api = Api_Object.Login(sec_times = 1 ,stop_times = 1 ).login_api(device = device , user= login_user,
            url = self.api_url_dict[device][site]     ,
            central_account='web.desktop', central_password='1q2w3e4r', site = site )
            

            #self.log.info('login : %s'%api)
            if api.error_msg != '':# 不等於 預設 字串 為 失敗
                assert False
            

            response_data = self.return_data(url =  api.url , response = 'OK' , 
            request_time= api.request_time )
            
            self.response_dict['Login'] = response_data

        
        except:
            self.log.error(' %s login fail '%self.login_site )

            response_data = self.return_data(url =  api.url , response = api.error_msg ) 
            
            self.response_dict['Login'] = response_data
            
            self.Api_Status()# 回傳 該site 的 staus邏輯
            return False

        
        #切換 odds type
        try:
        
            api.set_odds_type(odds_type = 'Dec')

            response_data = self.return_data(url =  api.req_url , response = 'OK' , 
            request_time= api.request_time ) 

            self.response_dict['UserProfile'] = response_data

        
        except:
            self.log.error(' %s set_odds_type fail '%self.login_site ) 
            
            response_data = self.return_data(url =  api.req_url , response = api.error_msg  ) 

            self.response_dict['UserProfile'] = response_data

            return False
        
        
        try:
            api.ShowAllOdds( )

            response_data = self.return_data(url =  api.req_url , response = 'OK' , 
            request_time= api.request_time ) 

            self.response_dict['ShowAllOdds'] = response_data

        except:
            self.log.error(' %s ShowAllOdds fail '%self.login_site ) 

            response_data = self.return_data(url =  api.req_url , response = api.error_msg  ) 

            self.response_dict['ShowAllOdds'] = response_data

            
            return False

        
        try:
            api.GetMarket()
            response_data = self.return_data(url =  api.req_url , response = 'OK' , 
            request_time= api.request_time ) 

            self.response_dict['GetMarket'] = response_data
        except:

            self.log.error(' %s GetMarket fail '%self.login_site ) 
            response_data = self.return_data(url =  api.req_url , response = api.error_msg  ) 

            self.response_dict['GetMarket'] = response_data
            
            return False

        try:# betting 接口 , 裡面包含  get ticket 的 接口
            result = api.DoplaceBet()
            
            
            if result == 'GetTickets False':#get ticket 如果有誤 , 就先不 做betting
                
                response_data = self.return_data(url =  api.req_url , response = api.error_msg  ) 

                self.response_dict['GetTickets'] = response_data

                return False


            else:# get ticket ok 
                response_data = self.return_data(url =  api.req_url , response = 'OK' , 
                request_time= api.request_time ) 
                
                self.response_dict['GetTickets'] = response_data
                
                if result['TransId_Cash'] == '0' or result['TransId_Cash'] is None:
                    processbet_re =  result['Message']
                else:
                    processbet_re =  result['TransId_Cash']
                
                response_data = self.return_data(url =  api.req_url , response = processbet_re  , 
                request_time= api.request_time ) 

                self.response_dict['ProcessBet'] = response_data
            
        except:
            self.log.error(' %s ProcessBet fail '%self.login_site ) 

            response_data = self.return_data(url =  api.req_url , response = api.error_msg  ) 
            self.response_dict['ProcessBet'] = response_data

        self.Api_Status()# 回傳 該site 的 staus邏輯
        return True

    def return_data(self, url, response, request_time= ''):
        response_status = {'url': url , 'response': response , 'request_time' : request_time }
        return response_status
    
    
    
    '''
    status  0:  All Pass , 1: Api Fail (接口登入錯誤) , 2: ProcessBet msg 投注沒成功 
    '''
    def Api_Status(self):# 針對 各監site 回傳 status 邏輯 
        for key_site in self.site_dict.keys():
            if self.site_dict[key_site]['Login']['response'] != 'OK':#  Api Fail (接口登入錯誤)
                self.site_dict[key_site]['Status'] = '1'
                return 'Done'# login 如果有問題 ,後面就不用做了
            elif self.site_dict[key_site]['ProcessBet']['response'].isdigit() is False: # process bet 回傳的 string 不是 訂單 (全為數字)
                self.site_dict[key_site]['Status'] = '2'
            else:# 登入 成功, process bet 也有訂單號回傳
                self.site_dict[key_site]['Status'] = '0'

        return 'Done'





site_list = list(Env().api_url_dict['mobile'].keys())


#site_list = ['Xtu168']
site_api_test = Site_Api()
#In[]
for site in site_list:
    log.info('site : %s'%site)
    site_api_test.site_api_betting_process(site = site  )

log.info('all site : %s'%site_api_test.site_dict)


'''
try:
    con = DataBaseInfo()
    con.mysql_insert(Data =  site_api_test.site_dict  )
except:
    log.info('資料Insert成功')
'''