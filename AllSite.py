
#In[]
import Api_Object,  datetime , time
from Common import Env
from  Logger import create_logger 
from Sql_Con import DataBaseInfo
from Common import Common


log = create_logger(r"\AutoTest", 'test')

class Site_Api(Env):
    def __init__(self):
        super().__init__()
        self.site_dict = {}# key 為 site , value 為 response_dict
        self.lets_talk = {} #記錄訊息用 

        # key 為 api , value 為一個 二為陣列
        self.response_time_dict = { 'Login':[], 'UserProfile': [] ,
        'Balance': [] , 'ShowAllOdds': [], 'GetTickets': [] , 'GetMarket': [] , 'ProcessBet':[], 
        'JSResourceApi' : []   , 'GetContirbutetor': [] , 'Running_GetEarly': [], 'Running_GetRunning': [],
        'Statement_GetStatement': [] , 'Statement_GetAllStatement': [] , 
             }
 
    
        self.log = log

        #print( self.url_dict)

    def retrun_2d_list(self ,site_name,  api_name , request_time): #回傳每次執行api 的 一個二為陣列 ,用來統計用
        new_list = [site_name]
        new_list.append(request_time)# 一個 陣列 [site, 秒數]
        self.response_time_dict[api_name].append(new_list)
    
    def site_api_betting_process(self , site ,device = 'mobile'):
        self.login_site = '%s - %s'%(device, site)
        self.response_dict = {}
        
        # 登入
        try:
            if site in ['Xtu168','Senibet', 'Yibo', 'Alog', 'Fun88', '11Bet','Bbin']:
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
            
            self.retrun_2d_list(site_name = site , api_name = 'Login' , request_time = api.request_time )

        
        except:
            self.log.error(' %s login fail '%self.login_site )

            response_data = self.return_data(url =  api.url , response = api.error_msg ) 
            
            self.response_dict['Login'] = response_data


            '''
            這邊用意是把 剩下的 case 加到資料結構
            '''
            for case in  self.response_time_dict:
                self.response_dict[case] = self.return_data()
            
            return False

        
        #切換 odds type
        try:
        
            api.set_odds_type(odds_type = 'Dec')

            response_data = self.return_data(url =  api.req_url , response = 'OK' , 
            request_time= api.request_time ) 

            self.response_dict['UserProfile'] = response_data
            self.retrun_2d_list(site_name = site , api_name = 'UserProfile' , request_time = api.request_time )
        
        except:
            self.log.error(' %s set_odds_type fail '%self.login_site ) 
            
            response_data = self.return_data(url =  api.req_url , response = 'False'  ) 

            self.response_dict['UserProfile'] = response_data

            


        # balance
        try:
        
            api.balance()

            response_data = self.return_data(url =  api.req_url , response = api.error_msg  , 
            request_time= api.request_time ) 

            self.response_dict['Balance'] = response_data
            self.retrun_2d_list(site_name = site , api_name = 'Balance' , request_time = api.request_time )
        
        except Exception as e:
            self.log.error(' %s balance fail : %s '%(self.login_site ,e )) 
            
            response_data = self.return_data(url =  api.req_url , response = 'False' ) 

            self.response_dict['Balance'] = response_data

        # JSResourceApi
        try:
        
            api.JSResourceApi()

            response_data = self.return_data(url =  api.req_url , response = api.error_msg  , 
            request_time= api.request_time ) 

            self.response_dict['JSResourceApi'] = response_data
            self.retrun_2d_list(site_name = site , api_name = 'JSResourceApi' , 
                request_time = api.request_time )


        except Exception as e:
            self.log.error(' %s JSResourceApi fail : %s '%(self.login_site ,e )) 
            
            response_data = self.return_data(url =  api.req_url , response = 'False' ) 

            self.response_dict['JSResourceApi'] = response_data


        # Running_GetEarly
        try:
        
            api.Running_GetEarly()

            response_data = self.return_data(url =  api.req_url , response = api.error_msg  , 
            request_time= api.request_time ) 

            self.response_dict['Running_GetEarly'] = response_data
            self.retrun_2d_list(site_name = site , api_name = 'Running_GetEarly' , 
                request_time = api.request_time )


        except Exception as e:
            self.log.error(' %s Running_GetEarly fail : %s '%(self.login_site ,e )) 
            
            response_data = self.return_data(url =  api.req_url , response ='False'  ) 

            self.response_dict['Running_GetEarly'] = response_data

        # Running_GetRunning
        try:
        
            api.Running_GetRunning()

            response_data = self.return_data(url =  api.req_url , response = api.error_msg  , 
            request_time= api.request_time ) 

            self.response_dict['Running_GetRunning'] = response_data
            self.retrun_2d_list(site_name = site , api_name = 'Running_GetRunning' , 
                request_time = api.request_time )


        except Exception as e:
            self.log.error(' %s Running_GetRunning fail : %s '%(self.login_site ,e )) 
            
            response_data = self.return_data(url =  api.req_url , response ='False'  ) 

            self.response_dict['Running_GetRunning'] = response_data

        # Statement_GetStatement
        try:
        
            api.Statement_GetStatement()

            response_data = self.return_data(url =  api.req_url , response = api.error_msg  , 
            request_time= api.request_time ) 

            self.response_dict['Statement_GetStatement'] = response_data
            self.retrun_2d_list(site_name = site , api_name = 'Statement_GetStatement' , 
                request_time = api.request_time )


        except Exception as e:
            self.log.error(' %s Statement_GetStatement fail : %s '%(self.login_site ,e )) 
            
            response_data = self.return_data(url =  api.req_url , response ='False'  ) 

            self.response_dict['Statement_GetStatement'] = response_data

        # Statement_GetAllStatement
        try:
        
            api.Statement_GetAllStatement()

            response_data = self.return_data(url =  api.req_url , response = api.error_msg  , 
            request_time= api.request_time ) 

            self.response_dict['Statement_GetAllStatement'] = response_data
            self.retrun_2d_list(site_name = site , api_name = 'Statement_GetAllStatement' , 
                request_time = api.request_time )


        except Exception as e:
            self.log.error(' %s Statement_GetAllStatement fail : %s '%(self.login_site ,e )) 
            
            response_data = self.return_data(url =  api.req_url , response ='False'  ) 

            self.response_dict['Statement_GetAllStatement'] = response_data

        # get_contirbutetor
        try:
        
            api.get_contirbutetor()

            response_data = self.return_data(url =  api.req_url , response = api.error_msg  , 
            request_time= api.request_time ) 

            self.response_dict['GetContirbutetor'] = response_data
            self.retrun_2d_list(site_name = site , api_name = 'GetContirbutetor' , 
                request_time = api.request_time )


        except Exception as e:
            self.log.error(' %s GetContirbutetor fail : %s '%(self.login_site ,e )) 
            
            response_data = self.return_data(url =  api.req_url , response = 'False'  ) 

            self.response_dict['GetContirbutetor'] = response_data
        
        
        try:
            api.ShowAllOdds( )

            response_data = self.return_data(url =  api.req_url , response = 'OK' , 
            request_time= api.request_time ) 

            self.response_dict['ShowAllOdds'] = response_data

            self.retrun_2d_list(site_name = site , api_name = 'ShowAllOdds' , request_time = api.request_time )

        except:
            self.log.error(' %s ShowAllOdds fail '%self.login_site ) 

            response_data = self.return_data(url =  api.req_url , response = 'False' ) 

            self.response_dict['ShowAllOdds'] = response_data

            


        
        try:
  
            api.New_GetMarkets()
            response_data = self.return_data(url =  api.req_url , response = 'OK' , 
            request_time= api.request_time ) 

            self.response_dict['GetMarket'] = response_data
            self.retrun_2d_list(site_name = site , api_name = 'GetMarket' , request_time = api.request_time )
        except:

            self.log.error(' %s GetMarket fail '%self.login_site ) 
            response_data = self.return_data(url =  api.req_url , response = 'False' ) 

            self.response_dict['GetMarket'] = response_data
            


        try:# betting 接口 , 裡面包含  get ticket 的 接口
            result = api.DoplaceBet()
            
            
            if result == 'GetTickets False':#get ticket 如果有誤 , 就先不 做betting
                
                response_data = self.return_data(url =  api.req_url[0] , response = api.error_msg  ) 

                self.response_dict['GetTickets'] = response_data

            else:# get ticket ok 
                response_data = self.return_data(url = api.req_url[0] , response = 'OK' , 
                request_time= api.req_list[0] ) 
                
                self.response_dict['GetTickets'] = response_data

                self.retrun_2d_list(site_name = site , api_name = 'GetTickets' , request_time = api.req_list[0])
                
                if result['TransId_Cash'] == '0' or result['TransId_Cash'] is None:
                    processbet_re =  result['Message']
                else:
                    processbet_re =  result['TransId_Cash']
                
                response_data = self.return_data(url =  api.req_url[1] , response = processbet_re  , 
                request_time= api.req_list[1] ) 

                self.response_dict['ProcessBet'] = response_data
                self.retrun_2d_list(site_name = site , api_name = 'ProcessBet' , request_time = api.req_list[1] )
            
        except:
            self.log.error(' %s ProcessBet fail '%self.login_site ) 
            self.log.error('error_msg %s  '%api.error_msg  ) 
            response_data = self.return_data(url =  api.req_url[1] , response = api.error_msg  ) 
            self.response_dict['ProcessBet'] = response_data
        
        #self.Api_Status()# 回傳 該site 的 staus邏輯
        return True

    def return_data(self, url='', response='', request_time= ''):
        response_status = {'url': url , 'response': response , 'request_time' : request_time }
        return response_status
    
    
    
    '''
    status  0:  All Pass , 1: Api Fail (接口登入錯誤) , 2: ProcessBet msg 投注沒成功 
    '''
    def Api_Status(self,site):# 針對 各監site 回傳 status 邏輯
        
        try:
            if self.response_dict['Login']['response'] != 'OK':#  Api Fail (接口登入錯誤)
                self.response_dict['Status'] = '1'
                self.lets_talk[site] = 'Error'
            
            elif self.site_dict[site]['ProcessBet']['response'].isdigit() is False: # process bet 回傳的 string 不是 訂單 (全為數字)
                self.response_dict['Status'] = '2'
            else:# 登入 成功, process bet 也有訂單號回傳
                for other_api in self.response_dict.keys():
                    if other_api in ['Login','ProcessBet']:
                        continue
                    if self.response_dict[other_api]['response'] == 'False':
                        self.response_dict['Status'] = '1'
                        self.lets_talk[site] = 'Error'
                        return 'Done'
                    else:
                        continue
                self.response_dict['Status'] = '0'
            
            return 'Done'
        except Exception as e:
            self.log.error('Api_Status : %s'%e)
            if 'isdigit' in str(e):# 這是 betting 問題
                self.response_dict['Status'] = '2'
                pass
            else:
                self.lets_talk[site] = 'Error'

    
    # 用來排序 每個 api 此次執行的時間 快/慢
    def sort_req_time(self):
        #scores  = sorted(scores, key = lambda s: s[1])
        print('開始排序 :')
        for api_name in self.response_time_dict.keys():
            sorted_list = sorted(self.response_time_dict[api_name], key = lambda s: s[1])
            print('%s 接口: %s 執行最快 回應時間: %s , %s 執行最慢 : %s'%(api_name,
            sorted_list[0][0],  sorted_list[0][1],          
            sorted_list[-1][0],  sorted_list[-1][1],  )  )
        print('排序完成')
    
    def ava_api_time(self):# 統計 該api 回復平均時間

        self.ava_api_site = {}# 存放 api  , 統計 平均 時間 

        for api_key in self.response_time_dict.keys():# 把該次 執行all site 的api 取出
            api_list = self.response_time_dict[api_key] #該 api 執行 所有 site的 時間 list
            total = round(sum(map(lambda x: float(x[1]), api_list   ))  ,4)# 該 api 執行時間的總和
            len_api_time = len(api_list)# 該api 多少 site
            ave = round(total / len_api_time,4)# 平均時間
            self.ava_api_site[api_key] = ave
        
        self.log.info('ava_api_site: %s'%self.ava_api_site)       



site_list = list(Env().api_url_dict['mobile'].keys())

#site_list = ['W88']
site_api_test = Site_Api()
#In[]
time_start = time.time() #開始計時 
print('開始執行時間 : %s'%datetime.datetime.now().strftime('%Y-%m-%d/%H:%M:%S') )

for site in site_list:
    log.info('site : %s'%site)
    site_api_test.site_api_betting_process(site = site  )# 執行整個 case流程
    site_api_test.Api_Status(site)# 回傳 該site 的 staus邏輯

time_end = time.time()

print('完成時間 : ',  time_end - time_start,'s')
#log.info('all site : %s'%site_api_test.site_dict)
log.info('letstalk : %s'%site_api_test.lets_talk)


if len(site_api_test.lets_talk) != 0:# 不等於 0 代表 Api_Status 有回傳 error
    Status = 0 # insert 狀態  錯誤
    #log.info('All Site Login Fail : %s'%site_api_test.lets_talk)

else:
    log.info('All Site Pass : %s'%site_list )
    log.info('Response Time : %s'%site_api_test.response_time_dict )
    #site_api_test.sort_req_time()
    
    Status = 1

site_api_test.ava_api_time()# 統計 此次 各 api 平均的回覆時間
    
node_type = Common().get_node_type()# 0 local , 1 remote


try:
    con = DataBaseInfo(env_index = int(node_type))
    con.site_data_insert(   Data =  site_api_test.site_dict , Status = Status  )
    log.info(' All site api insert資料 OK' )
except Exception as e:
    log.error('All site site_data_insert db 有誤 : %s'%e )
#con = DataBaseInfo(env_index = int(node_type))
con.site_response_insert(  Data =  site_api_test.ava_api_site   )# 平均時間 insert
history_ava_response = con.site_response_select()# 抓 出 歷史 api 的 回復資料

'''
歷史平均 回覆時間 
history_ava_response 為 list 裡面包每次 執行 all site 的 query (dict)
'''





con.db_con.close()



