#In[]
from collections import defaultdict
import Api_Object
from  Logger import create_logger 
import threading , time , random
from functools import reduce
import csv , requests 
from Api_Object import Mobile_Api





'''
針對 所有 All Site 做 壓力測試
需要增加的 參數 , site 名稱 ,  壓力數據

'''

class AllSite_Stress:
    '''
    - use_num  為 指定多少個 user登入 , 空字串 就是預設全部 , 帶指定數量 就是跑多少個用戶 (int)
    - site_name 為指定要那些 site 去執行, 空字串就是全部 , 帶多少間 site執行 (int),  指定部分 site  (list)
    '''
    def __init__(self , user_num = '' , site_name = ""   ):
        
        self.log =  create_logger(r"\AutoTest", 'test')
       
        self.site_url = self.site_csv()# 從excel 取出
        self.user_list = self.assing_user(user_num)# 拿出多少用戶
        self.site_list= self.assign_site(site_name)# 拿出多少 site 
        self.login_error ={} # 紀錄登入有問題
        
        #壓測 會做的 api . key 當api名稱, value 字典 {url : '' , session_type : ''}
        self.api_dict = {
            'UpdateBalance': {'url': '/balance/UpdateBalance' , 'session_type': 'post' ,'data': '', 'headers':'' 
        },
        'GetContributor':{'url': '/main/GetContributor' , 'session_type': 'post', 'data': 'isParlay=false&both=true&defaulteuro=false',
            'headers': ''        
        },
        'TwoCounter': {'url': '/Like/TwoCounter' , 'session_type': 'post', 'data': 'id=6685%2Fvideo.m3u8&action=1',
            'headers': ''        
        },
        'GetStatusCount': {'url': '/MyBets/GetStatusCount' , 'session_type': 'post', 'data': 'currWC=0',
            'headers': ''        
        },
        'GetLicSiteSpread': {'url': '/SpreadSetting/GetLicSiteSpread' , 'session_type': 'post', 'data': '',
            'headers': ''  
        },
        'GetPeakHourSpread': {'url': '/SpreadSetting/GetPeakHourSpread' , 'session_type': 'post', 'data': '',
            'headers': '' 
        },
        'ExtendToken': {'url': '/Login/ExtendToken' , 'session_type': 'post', 'data': '',
            'headers': '' 
        },
        'ShowAllOdds': { 'url': '/Login/ExtendToken' , 'session_type': 'post', 'data': '',
            'headers': ''
        },
        'GetTickets': {'url': '/BetV2/GetTickets' , 'session_type': 'post', 'data': '',
            'headers': ''
        },

        'Result': {'url': '/Result/GetResultDropDownList' , 'session_type': 'post', 
        'data':'' , 'headers': ''
            },
        'JSResourceApi': {'url': '/JSResourceApi/GetJSResource' , 'session_type': 'get', 
        'data':'' , 'headers': ''
            },
        'Running_GetEarly':  {'url': '/Running/GetEarly_ch?datatype=0&_=' , 'session_type': 'get', 
        'data':'' , 'headers': ''
            },
        'GetReferenceData':{'url': '/GetReferenceData/GetBettypeName?lang=en-US' , 'session_type': 'get', 
        'data':'' , 'headers': ''
            },
        'GetTopMessage':{'url': '/TopMessage/GetTopMessage' , 'session_type': 'post', 
        'data':'' , 'headers': ''
            },
        'Balance':{'url': '/balance/GetAccountInfo' , 'session_type': 'post', 
        'data':'localtime=8' , 'headers': ''
            },
        'Favorites':{'url': '/Favorites' , 'session_type': 'post', 
        'data':'' , 'headers': ''
            },
        'GetBannerInfo':  {'url': '/Default/GetBannerInfo' , 'session_type': 'post', 
        'data':'isBeforeBanner=false' , 'headers': ''
            },
        'Running_GetRunning':  {'url': '/Running/GetRunningOVR?RunningType=E&_=' , 'session_type': 'get', 
        'data':'' , 'headers': ''
            },
        'Statement/GetStatement':  {'url': '/Statement/GetStatementOVR?bfday=1&_=' , 'session_type': 'get', 
        'data':'' , 'headers': ''
            },
        'Statement/GetAllStatement':  {'url': '/Statement/GetAllStatement_ch?datatype=0&bfday=1&_=' ,
             'session_type': 'get', 
        'data':'' , 'headers': ''
            },
        'GetMySettingsJson': {'url': '/Setting/GetMySettingsJson' ,
             'session_type': 'post', 
        'data':'' , 'headers': ''
            },
        'CheckHasMessage': {'url': '/TopMessage/CheckHasMessage' ,
             'session_type': 'post', 
        'data':'' , 'headers': ''
            },
        'GetSpreadBetTypeGroup':  {'url': '/SpreadSetting/GetSpreadBetTypeGroup' ,
             'session_type': 'post', 
        'data':'' , 'headers': ''
            },
        'GetUMInfo': {'url': '/UMInfo/GetUMInfo' ,
             'session_type': 'get', 
        'data':'' , 'headers': ''
            },
        'GetSportSortString': {'url': '/setting/GetSportSortString' ,
             'session_type': 'post', 
        'data':'defaulteuro=false' , 'headers': ''
            }, 
        'Theme': {'url': '/Theme/Index?operatorId=&templateId=2' ,
             'session_type': 'get', 
        'data':'' , 'headers': ''
            }, 
 

        }


    def site_csv(self):# 從excel 讀取 各site 的 url
        site_url = {}# key 為 site name , value 為url
        with open('allsite_stress.csv', newline='') as csvfile:
            rows = csv.reader(csvfile)
            #print(rows)
            for row in rows:# 取出的 row 為list , 0: site name , 1 : url
                #print(row)
                site_url[row[0]] = row[1]
            csvfile.close()
        return site_url

        #print(site_url)

    def assing_user(self, user_num):
        user_list = ['preview%s_test'%i for i in range(1, 31)]
        
        if user_num == '':# 預設全部
            return user_list

        elif type(user_num) is list: # 如果帶列表 , 就是指定要跑哪幾間 site
            return user_num


        else:
            if type(user_num) is str:# 如果帶的是指定用戶 , 就放進一個 list
                new_user = []
                new_user.append(user_num)
                return new_user
        return user_list[:  user_num ]# 拿多少個 用戶 列表  帶的是int  多少個用戶數

    def assign_site(self, site_name):
        site_list = list(self.site_url.keys()) # 取得 所有 site 名稱,  list
        #self.log.info('site_list : %s'%site_list)
        if site_name == "": #拿全部
            return site_list
        
        elif type(site_name) is int:# 如果是帶指定 要多少間 site 數量
           return site_list[: site_name] 
        
        elif type(site_name) is list: # 如果帶列表 , 就是指定要跑哪幾間 site
            return site_name

        else:
            return 'site name 帶的值有誤'

    def login_site_thread(self):# login site 使用 thread
        login_count = 0
        
        start = time.perf_counter()# 開始api 計時 

        error_count = 0
        site_user_session = {}# site 當 key , value 是user_login_dict  { 'user': 'session' } 為 登入過哪間site 的 session    
        first_init = ''
        #site_dict = self.site_url
        for user in self.user_list:
     
        #for site in self.site_list:
            threads = []
            self.api =  Mobile_Api(device='app',  password= '1q2w3e4r', url= ''  ,client = '',
            sec_times='', stop_times='',site='' )


            for site in self.site_list:
                self.log.info('site: %s , user: %s'%(site, user))
                #self.log.info('login_url : %s'%self.site_url[site])
                '''
                呼叫 登入 流程
                
                '''
                site_name = 'stress_site_%s'%site# 讓login object知道 這個是 壓測 
                t = threading.Thread(target=  self.api.mobile_login
                    ,args = ( user ,'web.desktop' ,'1q2w3e4r',    site_name,  self.site_url[site] )   )
                
                threads.append(t)
                login_count = login_count + 1


            for i in threads:
                i.start()
                time.sleep(0.05)
            for i in threads:
                i.join()

            error_count = error_count + len(self.api.stress_login_dict['error'] )
 
            #self.log.info('self.stress_login_dict: %s '%self.api.stress_login_dict)

            dict_list = []
            #site_dict = {}

            for index, site in enumerate(self.api.stress_login_dict['site_name']):
                user_dict = {}

                user_session = self.api.stress_login_dict['session'][index]
                user_url = self.api.stress_login_dict['url'][index]
                
                user_dict['session'] = user_session
                user_dict['url'] = user_url
                
                dict_list.append(user_dict)
            
            for index, site in enumerate(self.api.stress_login_dict['site_name']):
                site_dict = {}
                user_dict = dict_list[index]
                site_dict[user] = user_dict
                
                if first_init == '':# 初始 site_user_session 為空,先放進來字典
                    site_user_session[site] = site_dict
                else:#

                    old_dict = site_user_session[site]
                    old_dict.update(site_dict)
                
                    site_user_session[site] = old_dict

            first_init = 'true'

        self.login_headers = self.api.headers#取得 登入 後的 header


        login_time =  '{0:.4f}'.format(time.perf_counter() - start) 

        self.log.info('總登入數量: %s , 耗時: %s'%(login_count, login_time) )
        self.log.info('登入的site  %s 間 , : %s'%(len(self.site_list),self.site_list) )
        self.log.info('登入失敗 數量: %s'%error_count)

        return site_user_session
    
    def login_user_thread(self):# login user 使用 thread
        login_count = 0
        
        start = time.perf_counter()# 開始api 計時 
        
        site_user_session = {}# site 當 key , value 是user_login_dict  { 'user': 'session' } 為 登入過哪間site 的 session    
        

            
        for site in self.site_list:
            threads = []
            self.api =  Mobile_Api(device='app',  password= '1q2w3e4r', url= self.site_url[site]  ,client = '',
            sec_times='', stop_times='',site='', queue= '' )


            for user in self.user_list:
                self.log.info('site: %s , user: %s'%(site, user))
                user_login_info = {}# 存放 各個需要的key , session url , user , session 等
                '''
                呼叫 登入 流程
                
                '''
                site_name = 'stress_user'# 讓login object知道 這個是 壓測 
                t = threading.Thread(target=  self.api.mobile_login
                    ,args = ( user ,'web.desktop' ,'1q2w3e4r',    site_name  )   )
                
                threads.append(t)
                login_count = login_count + 1

            for i in threads:
                i.start()
            for i in threads:
                i.join()
        

            site_user_session[site] =  self.api.site_stress
            self.login_headers = self.api.headers#取得 登入 後的 header
        

        login_time =  '{0:.4f}'.format(time.perf_counter() - start) 

        self.log.info('總登入數量: %s , 耗時: %s'%(login_count, login_time) )
        self.log.info('登入的site  %s 間 , : %s'%(len(self.site_list),self.site_list) )
        #self.log.info('登入失敗 site: %s'%self.login_error)
        #self.log.info('site_user_session :%s '%self.site_user_session)
        return site_user_session


    def login(self ):# 登入 function
        '''
        流程:  每間site 會 先把所有 需要的用戶 做登入  , 並記錄 session , 在 繼續跑 後面的 site
        '''

        login_count = 0
        start = time.perf_counter()# 開始api 計時 
        
        site_user_session = {}# site 當 key , value  { 'user': 'session' } 為 登入過哪間site 的 session 
        for site in self.site_list:
            
            user_login_dict = {}# key 當user , value 為 user_login_info (dict)
            for user in self.user_list:
                self.log.info('site: %s , user: %s'%(site, user))
                user_login_info = {}# 存放 各個需要的key , session url , user , session 等
                '''
                呼叫 登入 流程

                
                '''
                
                self.api = Api_Object.Login(sec_times = 1 ,stop_times = 1 ).login_api(device='mobile', 
                user= user,  url = self.site_url[site]   ,
                central_account='web.desktop',central_password='1q2w3e4r' )

                if self.api.error_msg != '':# 不等於 空字串 , 就是登入有問題
                    self.log.error('site: %s , user: %s , login fail: %s'%(site, user, self.api.error_msg ))
                    self.login_error[site] = self.site_url[site]
                    continue
                
                login_count = login_count + 1
                user_login_info['session'] = self.api.client_session
                user_login_info['url'] = self.api.url # 每個 user 登入 後 ,url 後面都會產出新的 session
                
                user_login_dict[user] = user_login_info

            site_user_session[site] = user_login_dict
            self.login_headers = self.api.headers#取得 登入 後的 header
        

        login_time =  '{0:.4f}'.format(time.perf_counter() - start) 

        self.log.info('總登入數量: %s , 耗時: %s'%(login_count, login_time) )
        self.log.info('登入的site  %s 間 , : %s'%(len(self.site_list),self.site_list) )
        self.log.info('登入失敗 site: %s'%self.login_error)
        #self.log.info('site_user_session :%s '%self.site_user_session)
        return site_user_session
    
    '''
    post api 統一走這支
    user_session 會 從外面 呼叫此 function 時 帶進來
    header 和 data 就看 各api執行 時 有無需要增加 在帶 , header 如果要增加, 需為 字典
    session_url 也是從外面傳進來 , 登入後的 url

    api_list 存放 各api 每次的 回應時間
    data_query 給 data post 傳的參數
    '''
    # user_session 會 從外面 呼叫此 function 時 傳入 ,外面傳進來
    def session_post_get(self ,site,  user_session, session_url ,func_name, data_query= '' 
         ):
        

        
        api_headers = self.api_dict[func_name]['headers']# 會取出 各api 的 headers 和 data
        
        if api_headers == "":
            pass
        else:# 為字典形式
            for key in api_headers.keys():
                self.login_headers[key] = api_headers[key]#增加 key value到  login_headers
        
        session_type = self.api_dict[func_name]['session_type']
        api_url =  session_url + self.api_dict[func_name]['url']
        
        if func_name == 'GetTickets': # get_ticket 的 data , 需 從 self.api.Match_dict  組出來傳進去
            '''
            self.log.info('先打 updatebalance')
            r = user_session.post(url = session_url + '/balance/UpdateBalance'
            , data = '' ,headers = self.login_headers )# 先試試是不是要先 update balance
            '''
            data = self.get_ticket_data()
        
        elif func_name == 'GetContributor':
            if data_query == '':
                data = 'isParlay=false&both=false&defaulteuro=false'
            else:
                data = 'isParlay=true&both=false&defaulteuro=false'

        elif func_name in ['Running_GetEarly', 'Running_GetRunning' , 'Statement/GetStatement', 'Statement/GetAllStatement']:
            now = int(time.time()*1000)
            api_url = session_url + self.api_dict[func_name]['url']+str(now)
            
            data = ''

        else:
            data = self.api_dict[func_name]['data']
        
        self.count = self.count + 1
        

        '''
        self.log.info('start %s site: %s, api: %s , session_type : %s , api_url : %s'%(self.count,site,
        func_name,session_type, api_url) )
        有必要再 印
        '''

        start = time.perf_counter()# 開始api 計時 

        if session_type == 'post':
            r = user_session.post(url = api_url
            , data = data ,headers = self.login_headers )
        else:# get
            r = user_session.get(url = api_url
            , data = data ,headers = self.login_headers ) 
        self.request_time =  '{0:.4f}'.format(time.perf_counter() - start)  # 該次 請求的url 時間
        
        
        
        #self.api_dict[func_name]['response_time'].append(self.request_time)# 這個是存放 該api 所有site的執行時間


        # 去 對 response 確認是否有回復 預期情況
        self.retrun_response(response = r, func_name = func_name, 
             site = site )


    '''
    # 從 api object分別打 showallodds / getmarket 後 取得所有資訊 
    然後組出 一個 data 資訊 給 get_ticket data 使用
    self.Match_dict 是個 index 包字典 odddsid : {  相關 betting 資訊 } 
    '''
    def get_ticket_data(self):

        index_key = 0
        Match = self.api.Match_dict[ index_key ]# 取出 index 0  key 為 Oddsid ,value為 字典,涵蓋 各種 資訊
        oddsid_list = list(Match.keys())# list裡面放 所有 odds id
        ran_index = random.randint(0, len(oddsid_list) -1  )
        
        Oddsid =  oddsid_list[ran_index]# 隨機取出 odds id , 拿到後就可以取出 接下來後面的 各參數值
        Oddsid_dict = Match[Oddsid]

        bet_team_index = 0 #正常會有 home/ away , 統一先用 index 0值
        odds = Oddsid_dict['odds_%s'%bet_team_index]
        bet_team =  Oddsid_dict['bet_team_%s'%bet_team_index]
        
        
        data_format = "ItemList[{index_key}][type]={bet_type}&ItemList[{index_key}][bettype]={BetTypeId}&ItemList[{index_key}][oddsid]={oddsid}&ItemList[{index_key}][odds]={odds}&\
        ItemList[{index_key}][Hscore]=0&ItemList[{index_key}][Matchid]={Matchid}&ItemList[{index_key}][betteam]={betteam}&\
        ItemList[{index_key}][QuickBet]=1:100:10:1&ItemList[{index_key}][ChoiceValue]=&ItemList[{index_key}][home]={Team1}&\
        ItemList[{index_key}][away]={Team2}&ItemList[{index_key}][gameid]={gameid}&ItemList[{index_key}][isMMR]=0&ItemList[{index_key}][MRPercentage]=&ItemList[{index_key}][GameName]=&\
        ItemList[{index_key}][SportName]=C&ItemList[{index_key}][IsInPlay]=false&ItemList[{index_key}][SrcOddsInfo]=&ItemList[{index_key}][pty]=1&ItemList[{index_key}][BonusID]=0&ItemList[{index_key}][BonusType]=0&ItemList[{index_key}][sinfo]=53FCX0000&ItemList[{index_key}][hasCashOut]=false\
        ".format(index_key= index_key, BetTypeId =  Oddsid_dict['BetTypeId'], oddsid = Oddsid 
        ,Matchid = Oddsid_dict['MatchId'] , Team1 = Oddsid_dict['Team1'], Team2= Oddsid_dict['Team2'] ,
        odds =  odds ,gameid =self.api.gameid    ,betteam = bet_team,  bet_type = "OU")

        return data_format

            
    def retrun_response(self, response ,func_name  , site):# 對 response做處理
        try:
            if func_name == '/':# 沒有 response json ,渲染html
                response
            
            
            # 其他有 json 格式]
            repspone_json = response.json()
            if func_name == 'UpdateBalance':
                
                Data = repspone_json['Data']
                msg =  "Bal: %s , BCredit: %s"%(Data['Bal'], Data['BCredit'] )

                #self.log.info('%s response: %s'%( func_name,msg  ))
            elif func_name == 'GetBannerInfo':
                status = repspone_json['status']

            elif func_name == 'GetTickets':
                Data = repspone_json['Data'][0]# list 包字典

                msg =  "GetTickets:  Minbet : %s , Maxbet: %s , DisplayOdds: %s"%(Data['Minbet'],   
                     Data['Maxbet'] , Data['DisplayOdds'])

                #self.log.info(msg)
            elif func_name == 'Result':
                Data = list(repspone_json.keys())
                # self.log.info('Data: %s'%(Data ))

            elif func_name == 'Theme':
                pages = repspone_json['pages']

            elif func_name == 'Running_GetEarly':
                stake_count = repspone_json['StakeCount']
                ticket_count = repspone_json['TicketCount'] 
            
            elif func_name in ['Running_GetRunning','Statement/GetStatement']:
                ticketcount = repspone_json['ticketcount']

            elif func_name == 'GetReferenceData':# a
                len_response = len(repspone_json)
                msg = 'response len : %s'%len_response

            elif func_name == 'Statement/GetAllStatement':
                OpeningBalance=repspone_json['OpeningBalance'] 

            
            else:
                errorcode = repspone_json['ErrorCode']
                if func_name == 'GetUMInfo':
                    if errorcode != 1:# 1 為 沒um
                        assert False
                else:
                    if errorcode != 0:
                        assert False
                
                #self.log.info('%s response Errorcode: %s,  Data: %s'%( func_name,errorcode,msg  ))




            self.Stress_reponse[func_name].append(self.request_time)
            #self.api_object[func_name].append(self.request_time)
            


            
        except Exception as e:
            self.error_count = self.error_count + 1
            self.log.error('api : %s , error : %s , msg: %s'%(func_name, e,response.text ) )
            
     

    '''
    要整理資料結構 , 最後的樣式 是 
    {'Api': [[site , 1s ], [site, 2s]  ]  }# key為API, value 為一個 二為陣列 , 裡面放這api 各site 的回應分布
    最後用 lambda sort 函士  把 該api 最快 的 site 和 最慢的site 列出

    目前沒用
    '''
    def cal_response_time(self):# 統整 各 site 打api 的回應時間 平均
        self.cal_dict = {}# 統計 各site 回應時間
        # key 為 api , value 為list (存放 [site, 時間]   ) 二為陣列
        self.api_two_dict = {'UpdateBalance': [] , 'GetContributor': [], 'TwoCounter': [] ,'GetStatusCount': [],
            'GetLicSiteSpread': [], 'GetPeakHourSpread': [], 'ExtendToken': [], 'GetTickets': []
        
          }

        #update_balance_list = []# 當作二為陣列
        self.log.info('self.site_respone_dict: %s'%self.site_respone_dict)
        for site in self.site_respone_dict.keys():
            for api in self.site_respone_dict [site]:
                result_list = self.site_respone_dict [site][api]# 為reponse時間 列表

                for api_time in result_list:#把該 api 的回應時間 取出
                    new_list = []
                    new_list.append(site)
                    new_list.append(api_time)
                    self.api_two_dict[api].append(new_list)
                
                self.cal_dict[api] = self.api_two_dict[api]

                
                '''
                if api == 'UpdateBalance':
                    
                    for api_time in result_list:#把該 api 的回應時間 取出
                        new_list = []
                        new_list.append(site)
                        new_list.append(api_time)
                        #[site, 回應時間 ]
                        update_balance_list.append(new_list)

                    self.cal_dict['UpdateBalance'] = update_balance_list
                '''

                               
        self.log.info('cal dict : %s'%self.cal_dict) 
        #self.log.info('api_two_dict: %s'%self.api_two_dict)      
        for api in self.cal_dict.keys():

            scores  = sorted(self.cal_dict[api], key = lambda s: s[1])
            self.log.info('%s: %s 執行最快 回應時間: %s , %s 執行最慢 : %s'%(api, scores[0][0],  
            scores[0][1],  scores[-1][0],  scores[-1][1]   ) )


    def site_sum(self):# 這個是回應 該api 回應平均值

        for api in self.Stress_reponse.keys():

            api_time_list = self.Stress_reponse[api]
            len_api_list = len(api_time_list)
            if len_api_list == 0: # 代表沒執行過 的api 空陣列, 不必理會
                continue

            #total = round(sum(map(lambda x: float(x[1]), api_time_list))  ,4)# 該api 執行的總和時間
            total = round(reduce(lambda x , y: float(x) + float(y), api_time_list)  ,4)# 該api 執行的總和時間
            map_a = list(map(float,api_time_list))


            sort_ = sorted(map_a)
            api_aver = round(total / len_api_list, 4)
            self.log.info(' %s 請求數量: %s ,平均回應: %s'%(api, len_api_list,
                 api_aver))

            self.log.info( '最快 : %s , 最慢: %s '%(sort_[0], sort_[-1]))
        
        self.log.info('執行: %s Site , 每間 %s User'%( len(self.site_list),
            len(self.user_list)    ))





    '''
    api_list 帶入 要做 壓測 的api 

    loop 順序 . site > user > api 

    stop_times 值續打幾秒 預設先3秒

    '''
    def thread_func(self,api_list, site_user_session , stop_times = 3, data_query=''):# 做 併發的 地方
    
        self.count = 0
        self.error_count = 0

        # 不用self 是因為 , 如果只做登入一次 ,後續逛想session ,這邊會一值長 
 
        
        
        if 'GetTickets' in api_list: # 如果 壓測的接口 有 getticket, 需先拿 showallodd/ 和 getmarket的相關 參數值
            self.log.info('有getticket的測試, 先去showallodda/ getmarket拿相關資訊')
            self.api.ShowAllOdds(stress_type = 'stress')# 先不帶任何參數, 預設  soccer/ early
            self.api.GetMarket()
            self.log.info('showallodds, getmarket 打完 總長度: %s'%len( self.api.Match_dict))# 這個就是 組出 oddsid mathcid 相關值 給 get ticket使用
            
        #self.log.info('site_user_session: %s'%site_user_session)
        
        
        self.Stress_reponse = defaultdict(list) #這個是 把每次 while 的site/user/api 繼續擴展



        all_thread_list = []
        #   請求數量 達到 指定 數量 時, 就break ,所以小於會一值執行
        

        init_start = time.perf_counter()
        self.log.info('開始送出請求')
        api_url = self.api_dict[api_list[0]]['url']
        self.log.info('url: %s'%api_url)

        self.time_start = time.time() #開始計時
        self.time_end = time.time()

        #print('start: %s'%str_time)
        #self.time_end   會 再while 迴圈一值變動
        while self.time_end - self.time_start <= stop_times:# 當程式執行超過指定時間 ,就break
        
            #while self.count <= assing_req_num:
            second_count = 0# 記錄每秒 多少個請求
            for site in site_user_session.keys():# 取出此次 的 site
                
                thread_list = []

            
                for uesr in  site_user_session[site].keys():# 取出 該site 的所有 user
                    user_info = site_user_session[site][uesr]
                    '''
                    取出各 api 相對應 的 post/get , header ,data , url 
                    '''
                    
                    user_session = user_info['session']
                    session_url = user_info['url']                
                    #self.session_post_get(user_session = user_session, session_url = session_url 
                    # ,func_name = api_name )  

                    for api_name in api_list:
                        
                        t = threading.Thread(target= self.session_post_get, args=(site ,user_session,  session_url,
                            api_name ,data_query  ) )
                        second_count = second_count + 1
                        thread_list.append(t)#存放 每次 site/user/api , 下個秒數執行會被清空
                        all_thread_list.append(t)# 用來最後 請求送完後 ,確認 response 回來

                try:
                    for i in thread_list:
                        i.start()
                        time.sleep(0.01)# 0.01
                        
                except Exception as e:
                    self.log.error('thread error : %s'%e)

 
            #time.sleep(0.05)# 這邊 的是控制每秒送出間格
            self.time_end = time.time() #開始計時
            end_req_time =  '第 {0:.4f} s'.format(time.perf_counter() - init_start) 
            #self.log.info('%s 送出 %s 請求'%(end_req_time,   second_count ))



        self.log.info('持續打了 : %s s , 總共 %s 請求'%( stop_times, self.count ,)  )
        for i in all_thread_list:
            i.join()

            '''
            走到這, 代表 該site 的 所有 user/api打完, 需把 self.site_respone_dict 繼續延展起來
            '''    
            
            #self.Stress_reponse[site_count] = self.site_respone_dict 

        #self.log.info('Stress_reponse: %s'%self.Stress_reponse )
        self.log.info('reponse 有誤 數量: %s'%self.error_count)




#In[]
#登入


'''
user_num 和 site_name 皆可以帶  多少數量 (int) 或者 指定的 用戶/site (list)
兩者預設 空字串 為全部
site_list = ['JIB88' ]
user_num =  ['preview30_test']
login_user_thread , login , login_site_thread

'''
allsite = AllSite_Stress( user_num = 1 ,
site_name = 1)

site_user_session = allsite.login_site_thread()#然後登入 ,會產出 各 site 各用戶 登入 的session

#In[]





'''
api_list = [ 'UpdateBalance' , 'GetContributor' , 'TwoCounter' , 'GetStatusCount' ,
 'GetLicSiteSpread', 'GetPeakHourSpread', 'GetTickets', 'ExtendToken' ]
 
Result , JSResourceApi , Running_GetEarly , GetReferenceData , GetTopMessage
Balance , Favorites , GetBannerInfo , RecommendTickets , Running_GetRunning ,Statement/GetStatement 
Statement/GetAllStatement , GetMySettingsJson , CheckHasMessage , GetSpreadBetTypeGroup
GetUMInfo , GetSportSortString , Theme

stop_times 值續打幾秒

每秒 會執行多少個請求 , 目前是依據 多少個 user / site / api
ex:
登入 1個 user / 1 間 site / 打 8 支api , 就是每秒 送出 8個 req
登入 10 個 user / 10 間 site / 打 1 支api , 就是 每秒會送出 100 個req
data_query 只對 data post 需帶參數 才有影響
'''


allsite.thread_func( api_list = [ 'TwoCounter' ] , data_query = '' ,
    site_user_session = site_user_session, stop_times =  1)


allsite.site_sum()#統整 該api 的回應時間 平均(所有site)





# %%
