
#In[]
import Api_Object
from collections import defaultdict
from Common import Env
from  Logger import create_logger 
from Sql_Con import DataBaseInfo


class Site_Api(Env):
    def __init__(self):
        super().__init__()
        #self.response_dict = {} #defaultdict(list)#  用來存放 各site 各api 請求的 回復
        self.site_dict = {}# key 為 site , value 為 response_dict
        #self.response_status = {'url':'','status': '200', 'response': ''}
        self.log = create_logger(r"\AutoTest", 'test')
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
            if api is False:
                assert False
            #self.response_status['url'] = api.url

            self.response_dict['Login'] = 'OK'
        
        except:
            self.log.error(' %s login fail '%self.login_site ) 
            self.response_dict['Login'] = 'False'

            return False

        try:
            api.set_odds_type(odds_type = 'Dec')
            self.response_dict['UserProfile'] = 'OK'

        
        except Exception as e:
            print(e)
            self.log.error(' %s set_odds_type fail '%self.login_site ) 
            self.response_dict['UserProfile'] = 'False'

            
            return False
        
        
        try:
            api.ShowAllOdds( )

            self.response_dict['ShowAllOdds'] = 'OK'

        except Exception as e:
            print(e)
            self.log.error(' %s ShowAllOdds fail '%self.login_site ) 
            self.response_dict['ShowAllOdds'] = 'False'

            
            return False

        try:
            api.GetMarket()
            self.response_dict['GetMarket'] = 'OK'
        except:

            self.log.error(' %s GetMarket fail '%self.login_site ) 
            self.response_dict['GetMarket'] = 'False'
            
            return False

        try:
            result = api.DoplaceBet()
            if result == 'GetTickets False':#get ticket 如果有誤 , 就先不 做betting
                self.response_dict['GetTickets'] = 'False'
                return False
                #self.response_dict['ProcessBet'] = 'False'

            else:
                self.response_dict['GetTickets'] = 'OK'
                if result['TransId_Cash'] == '0' or result['TransId_Cash'] is None:
                    processbet_re =  result['Message']
                else:
                    processbet_re =  result['TransId_Cash']
                self.response_dict['ProcessBet'] = processbet_re
            
        except:
            self.log.error(' %s ProcessBet fail '%self.login_site ) 
            #self.response_status['status'] = 'False'
            self.response_dict['ProcessBet'] = 'False'

        #self.log.info('site: %s'% self.site_dict)
        return True




log = create_logger(r"\AutoTest", 'test')

site_list = list(Env().api_url_dict['mobile'].keys())


#site_list = ['Alog']
site_api_test = Site_Api()
#In[]
for site in site_list:
    log.info('site : %s'%site)
    site_api_test.site_api_betting_process(site = site  )

log.info('all site : %s'%site_api_test.site_dict)


#con = DataBaseInfo()
#con.mysql_insert(Data =  site_api_test.site_dict  )
    #site_api_test.response_dict
