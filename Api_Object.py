#In[]

from collections import defaultdict
from logging import log
import execjs
import hashlib
from PIL import Image
from numpy import False_
import pytesseract,os,time
from  Logger import create_logger 
import pathlib,re
from Common import Common

from urllib.parse import urlparse
logger = create_logger(r"\AutoTest", 'test')

#In[]
class Login(Common):#取得驗證碼邏輯 
    def __init__(self,device="",sec_times='',stop_times='',url=''):
        super().__init__(sec_times,stop_times)
        #logger = create_logger(r"\AutoTest", 'test')
        if device == 'Pc driver':
            self.dr = self.get_driver()
        self.img_pic = pathlib.Path(__file__).parent.absolute().__str__() + "login_code.jpg"
        self.download_waiting_time = 3
        self.url = url
        self.cookies = ""# 預設空, 會從驗證碼時,拿取 ASP.NET_SessionId
    
    
    def login_api(self, device,user,url,client='',central_account='',central_password=''):
        '''devive 為Pc 才會去叫 webdriver ,要取驗證碼'''
        if device in ['mobile','app']:
            mobile_api = Mobile_Api(device='app',  password =  '1q2w3e4r', url=url ,client = client,
            sec_times=self.sec_times, stop_times=self.stop_times )

            mobile_api.mobile_login(user=user,central_account=central_account,
            central_password=central_password)# 初始 login為 None 一定先登入
            return  mobile_api
        else: #都是桌機
            desktop_api = Desktop_Api(device=device,user=user,url=url)
            desktop_api.desktop_login(central_account=central_account,
            central_password=central_password)
            return  desktop_api

    def validation(self):
    # 取得圖片
        #logger.info(self.img_pic)
        login_code = Image.open(self.img_pic)
        logger.info(login_code)
        # result.show()
        # 驗證碼圖片修正 轉為白底黑字
        identify_result = self.convert_img(login_code, 225)
        # result.show()
        pytesseract.pytesseract.tesseract_cmd = 'Tesseract-OCR\\tesseract.exe'
        identify_result = pytesseract.image_to_string(identify_result).strip()
        # 刪除圖片
        os.remove(self.img_pic)
        logger.info('圖片刪除成功')
        return identify_result
    
    def convert_img(self,img, threshold):
        img = img.convert("L")
        # 處理灰度
        pixels = img.load()
        for x in range(img.width):
            for y in range(img.height):
                if pixels[x, y] < threshold:
                    pixels[x, y] = 255
                else:
                    pixels[x, y] = 0
        return img
    def assert_validation(self):# 驗證碼的流程, 寫成function, 如果有解析失敗,好retry
        
        while True:
            now = int(time.time()*1000)
            if 'xideqs' in self.url:# qasb 測試環境 url輸入後 取得當前 xideqseTWIN 的url
                
                self.dr.get(self.url)
                current_url = self.dr.current_url# 取得轉換後的測試url ex: http://qasb.athena000.com:42104/(S(xideqseTWIN-Avzh25wrew0zndzoe3tmqiamhf2X-MXwjdkH3qs47fawD1gZZ))/
                self.url = current_url.split('?')[0]#?scmt=tab01&ssmt=tab01 移除
                logger.info('轉換url : %s'%self.url )
                login_code_url = '%s/login_code.aspx?%s'%(self.url,now)
                self.dr.get(login_code_url)
            else:#Production athena000
                login_code_url = '%s/login_code.aspx?%s'%(self.url,now)
                logger.info('login_code_url: %s'%login_code_url)
                self.dr.get(login_code_url)
            
            self.dr.get_screenshot_as_file(self.img_pic)
            for i in range(self.download_waiting_time):
                if os.path.isfile(self.img_pic):
                    logger.info('圖片有找到')
                    break
                else:
                    logger.info('圖片未找到')
                    time.sleep(1)
                    if i == self.download_waiting_time - 1:
                        raise IOError

            validate_result = self.validation()
            
            if validate_result.isdigit() is False:# 檢查取得的驗證碼是否都是數值,如果有字母 馬上retry
                logger.info('有英文字 %s,直接retry'%validate_result)
            elif len(validate_result) < 4:#長度小於4也要retry
                logger.info('長度小於4 %s,直接retry'%validate_result)
            else:
                logger.info('validate_result: %s'%validate_result)
                if 'qasb' in self.url:
                    break
                self.cookies = self.dr.get_cookies()
                logger.info('cookies: %s'%self.cookies )
                self.dr.close()
                break
        return validate_result

    def js_from_file(self,file_name):# 讀取js 加密邏輯  CFS
        """
        讀取js檔案
        :return:
        """
        with open(file_name, 'r', encoding='UTF-8') as file:
            result = file.read()

        return result



    def md(self,password,val):# md5 加密邏輯 ./DepositProcessLogin 登入加密 邏輯 使用 MD5(CFS(loginData.password) + loginData.validation)
        m = hashlib.md5()
        md5_str = str.encode(password) + str.encode(val)
        m.update(md5_str)
        sr = m.hexdigest()
        return sr

    def get_Pwekey(self):# 取得 pwekey 街口 ,mobile使用
        r = self.session.post(self.url  + '/Default/RefreshPKey',headers=self.headers)
        try:
            PWKEY = r.json()['Data']['PWKEY']
            logger.info('PKey: %s'%PWKEY) 
            return PWKEY 
        except:
            logger.error('PKey: 取得失敗') 
            return False
    

#login_type 預設空字串, 是使用 athena 登入 
class Mobile_Api(Login):# Mobile 街口  ,繼承 Login
    def __init__(self,client,device="",url='',password='',sec_times='',stop_times=''):
        super().__init__(device,sec_times,stop_times) 
        self.login_session = {}# key 為 user ,value 放 NET_SessionId
        self.url = url
        self.login_type = ''# api site 為 空字串
        if 'athena' in self.url:
            self.login_type = 'athena' # 是 api site 登入 還是  athena site登入 , login方式不一樣
        self.api_site = ''# 預設空
        self.password = password
        self.MatchId = {}# 存放 matchid value 放team
        self.MarketId = {}
        if client == '':
            self.client_session = self.session
        else:
            self.client_session = client
        self.count = 0 #用來跌加  請求個數
        self.stress_dict = defaultdict(list)# 用來 存放壓力測試 街口的 數據
        self.odds_type = 'Dec' #先預設為空，避免沒有執行 Odds type Change 就下注
    '''
    共用 url 請求 的方式, 包含回傳 請求時間, 請求相關資訊放到 stress_dict, 避免每個新增街口, 都要寫一次
    '''
    def stress_request_post(self, request_data ,func_url  ): 
        self.count = self.count + 1
        self.stress_dict['request num'].append(self.count)
        self.stress_dict['request url'].append(request_data)
        start = time.perf_counter()
        print(self.headers)
        r = self.client_session.post(self.url  + func_url , data = request_data,headers=self.headers)
        rquest_url = r.url
        self.stress_dict['request url'].append(rquest_url)

        request_time =  '{0:.4f} s'.format(time.perf_counter() - start) # 該次 請求的url 時間
        logger.info("Request completed in %s s"%request_time )
        self.stress_dict['request completed'].append(request_time)

        return r

        
    def Return_Bet_dict(self,assign_betype):
        return_dict = {}

        for bet_type in assign_betype:
            for index in self.Match_dict.keys():
                if bet_type in self.Match_dict[index].keys():
                    value_dict = {}
                    value_dict[bet_type] = self.Match_dict[index][bet_type]
                    return_dict[index] = value_dict
        index_list = list(self.Match_dict.keys())
        for index in index_list: #取出確認  return_dict 缺少哪個index ,隨機給
            if index in return_dict.keys():
                pass
            else:
                value_dict = {}
                bet_type = list(self.Match_dict[index].keys())[0]
                value_dict[bet_type] = self.Match_dict[index][bet_type]
                return_dict[index] = value_dict
        
        return return_dict


    '''
    athena 需叫 本地js , api site 直接 在 url 後面增加query 參數
    '''
    def mobile_login(self,user,central_account='',central_password=''):# Mobile Login街口邏輯
        if self.login_type  == 'athena':# athena 登入
            common_js = execjs.compile(self.js_from_file('./login_js/mobile.js'))# 讀取 login js檔
            PKey = self.get_Pwekey()
            cfs_psswd = common_js.call("r", self.password ,PKey)#App 密碼加密,適用 密碼和 PKey 去做前端js處理
            logger.info('app cfs_psswd: %s'%cfs_psswd)

            login_data = 'Username={user}&Password={cfs_psswd}&Language=zh-CN&isGesture=false\
            &skinMode=3%3D%3D&__tk=&detecas_analysis=%7B%22startTime%22%3A1630246986799%2C%22version\
            %22%3A%222.0.6%22%2C%22exceptions%22%3A%5B%5D%2C%22executions%22%3A%5B%5D%2C%22storages%22%3A%5B%5D%2C%22devices%22%3A%5B%5D%2C%22\
            enable%22%3Atrue%7D'.format(user=user, cfs_psswd=cfs_psswd)

            self.headers['X-Requested-With'] =  'XMLHttpRequest'
            self.headers['Content-Type'] =  'application/x-www-form-urlencoded; charset=UTF-8'
            #logger.info('headers: %s'%self.headers)
            
            r = self.client_session.post(self.url  + '/Login/index',data=login_data,headers=self.headers)
            try:
                repspone_json = r.json()
                #logger.info('response: %s'%repspone_json)
                ErrorMsg = repspone_json['ErrorMsg']
                ErrorCode = repspone_json['ErrorCode']
                logger.info('ErrorMsg: %s'%ErrorMsg)
                logger.info('ErrorCode: %s'%ErrorCode)
                #if ErrorMsg != 'login_success':
                    #return ErrorMsg
                if ErrorMsg is None and str(repspone_json['ErrorCode']) == '0' :# 位存款帳號登入 會為 none
                    logger.info('未存款登入成功')
                else:
                    Data_url = repspone_json['Data']# 登入成功後, 需在get 一次 response 回傳的 url
                    r = self.client_session.get(self.url  + Data_url, headers=self.headers)
                
                cookie_session = self.client_session.cookies.get_dict()
                NET_SessionId = cookie_session['ASP.NET_SessionId']
                logger.info('NET_SessionId: %s'%NET_SessionId )
                self.login_session[user] = NET_SessionId
                #logger.info('self.login_session: %s'%self.login_session)
                return True
            except Exception as e:
                logger.info('Login Api Fail: %s'%e)
                return False
        
        else: #api site登入
            
            r = self.client_session.get(self.url)
            session_url = r.url # api site 需先拿到 session url 在做登入
            logger.info('登入前 session url: %s'%session_url)
            
            #LicLogin , DepositLogin
            login_query = 'LicLogin/index?lang=en&txtUserName={user}&Password=1q2w3e4r&token=&skin=&CentralAccount={central_account}&CentralPassword={central_password}&menutype=&sportid=&leaguekey=&matchid=&isAPP=\
            &currencyName=&bdlogin=1&tsid=&SkinColor=&types=1%2C0%2Cl'.format(user=user,
            central_account=central_account,central_password=central_password)
            api_login_url = session_url.split('apilogin')[0] + login_query

            self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
            self.headers['Accept-Language'] = 'zh-TW,zh;q=0.9'
            self.headers['X-Requested-With'] = 'XMLHttpRequest'
            self.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            
            r =  self.client_session.get(api_login_url, headers=self.headers)
            
            self.url = r.url.split('#Sports')[0]# 登入後 就是 拿這個 變數 去做後面 各個街口的使用
            logger.info('登入後 的 session url: %s'%self.url)# 登入後的轉導url
            if 'errorcode' in self.url:
                return 'Login Fail'
            
            '''
            api site 不是每個 登入後的都會帶 session url ,ex: bbin
            這會再 showallodds 有不同的判斷
            '''
            if 's(' not in self.url:# 有session 的url 後面都會有 s(
                self.api_site = 'web'
            else:
               self.api_site = 'odds provider' 
            return 'Login True'

    def get_contirbutetor(self ):# /main/GetContributor
        
        data = 'isParlay=false&both=true&defaulteuro=false'
        r = self.stress_request_post(request_data= data, func_url = '/main/GetContributor' )
        try:
            repspone_json = r.json()
            ErrorCode = repspone_json['ErrorCode']
            self.stress_dict['response'].append('ErrorCode: %s'%ErrorCode)

            logger.info('ErrorCode: %s '%(ErrorCode ) )
            return True
        except:
            logger.error('response :%s'%r.text )
            self.stress_dict['response'].append(r.text) 
            logger.error('get_contirbutetor Api Fail')
            return False

    def set_odds_type(self,odds_type='MY'):# /setting/SaveUserProfile
        self.odds_type = odds_type
        odds_type_dict = {'Dec' : '1','CN' : '2','Indo' : '3','MY' : '4','US' : '5'}
        data = 'DefaultLanguage=en-US&OddsType={odds_type}&BetStake=0&BetterOdds=false&oddssort=2&inpbetStake=0'.format(odds_type=odds_type_dict[odds_type])
        r = self.client_session.post(self.url  + '/setting/SaveUserProfile',data=data,headers=self.headers)
        try:
            repspone_json = r.json()
            ErrorCode = repspone_json['ErrorCode']
            self.stress_dict['response'].append('ErrorCode: %s'%ErrorCode)
            logger.info('ErrorCode: %s '%(ErrorCode ) )
            return True
        except:
            logger.error('response :%s'%r.text )
            self.stress_dict['response'].append(r.text) 
            logger.error('Setting Odds Type Api Fail')
            return False

    def balance(self):# /balance/GetAccountInfo
        
        data = 'localtime=8'
        #self.headers['Referer'] = self.url
    
        r = self.stress_request_post(request_data= data, func_url = '/balance/GetAccountInfo' )

        #r = self.client_session.post(self.url  + '/balance/GetAccountInfo', data=data,headers=self.headers)
       
        try:
            repspone_json = r.json()
            Bal = repspone_json['Data']['Bal']
            BCredit = repspone_json['Data']['BCredit']
            self.stress_dict['response'].append('Bal: %s , BCredit: %s '%(Bal ,BCredit ) )
            
            logger.info('Bal: %s , BCredit: %s '%(Bal ,BCredit ))
            return True
        except:
            logger.error('url :%s'%r.url )
            self.stress_dict['response'].append(r.text)
            logger.error('mobile balance Api Fail')
            return False

    '''
    type 帶 test 就 可以 忽略 testing 比賽  ,bet_type 可帶 其他(ex: parlay)
    '''
    def ShowAllOdds(self,type='',market='e',filter='',sport='Soccer',bet_type='OU'):# 取得 MatchId 傳給 GetMarket , 還有取得 TeamN 回傳給 DoplaceBet  的 home/away
        
        # e為 早盤, t為 today
        #market = 't'# 預設 today
        self.sport = sport
        self.bet_type = bet_type
        self.gameid = self.game_mapping(self.sport)# 後面 get market 和 betting 就不用在多傳 gameid 參數了, 統一在這宣告
        for market in market:
            data = 'GameId=%s&DateType=%s&BetTypeClass=%s&Gametype=1'%(self.gameid  ,market,self.bet_type)# 先寫死cricket, 之後優化
            self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
            
            try:# athen 和部分api的 ,走 一個邏輯
                if self.login_type  == 'athena' or self.api_site =='web':# athena  
                    r = self.client_session.post(self.url  + '/Odds/ShowAllOdds',data=data,headers=self.headers)
                    repspone_json = r.json()
                else:
                    if 'Authorization' not in list(self.headers.keys()):
                        logger.info('使用api site ,需先打 /Login/ExtendToken 拿出 Bearer')
                        r = self.client_session.post(self.url+ '/Login/ExtendToken',headers=self.headers)
                        Bearer_data = r.json()['Data']# 需傳到 showallodds
                        logger.info('Bearer_data: %s'%Bearer_data)
                        
                        self.headers['Authorization'] = 'Bearer  %s'%Bearer_data
                    r = self.client_session.get('http://oplg1.fast4indo.com/' + '/Odds/ShowAllOddsApi?'+data,headers=self.headers)
                    repspone_json = r.json()
                #logger.info('repspone_json: %s'%repspone_json)   
            except:
                logger.info('mobile ShowAllOdds Api Fail')
                return False
            
            try:
                Data = repspone_json['Data']# 字典 裡面包兩個key, NewMatch 和 TeamN
                NewMatch = Data['NewMatch']# list
                TeamN = Data['TeamN']# dict
                LeagueN = Data['LeagueN']
                #logger.info('TeamN: %s'%TeamN)
                for index,dict_ in enumerate(NewMatch):
                    #logger.info('index: %s'%index)
                    team_name = {}
        
                    TeamId1 = dict_['TeamId1']
                    TeamId2 = dict_['TeamId2']
                    LeagueId = dict_['LeagueId']
                    League_name = LeagueN[str(LeagueId)]

                    if type == '':# 不能有test 的賽事 
                        if any(test_parlay in League_name for test_parlay in  ['TESTING','test','Test','测试'] ):# 如果 不是要 針對test 然後 testing 又再 league ,不能串
                            continue
                    # type 帶 test 就 可以 忽略 testing 比賽 
                    team_name['Team1'] = TeamN[ str(TeamId1) ]
                    team_name['Team2'] = TeamN[str(TeamId2) ]
                    team_name['League'] = League_name
                    team_name['Market'] = market
                    
                    #logger.info('team_name: %s'%team_name)
                    MatchId = dict_['MatchId']# 取出Matchid ,並當作 Key
                    self.MatchId[MatchId] = team_name# MatchId 當key ,value為 teamname
            except Exception as e:
                logger.error('ShowAllOdds: %s'%e)
                return False
        if  filter != '' and len(filter) != 0 :# 只拿指定 的match id , 防呆 fiter如果帶空list
            for key in list(self.MatchId):
                if key not in filter:
                    del self.MatchId[key]
        len_matchid = len(self.MatchId)
        logger.info('self.MatchId: %s'%self.MatchId)
        logger.info('len MatchId: %s'%len_matchid )
        
        if len_matchid < 3:
            logger.info('長度小於3 無法串票')
            return 'False'


    '''
    parlay_len 預設 給3 是 找三個match 來串即可, 如果不是 3 就是 給其他長度
    BetType 預設為 parlay . parlaymore 為更多 bet

    取得   MarketId(oddsid), Price(odds) , BetTypeId
    '''
    def GetMarket(self):
        if 'parlay' in  self.bet_type:
            parlay_len = '3'
        else:
            parlay_len = '1'
        self.Match_dict = {}# key 當作 index, value 存放 該match id 裡所有 的bettype(self.MarketId)
        for index,match_id in enumerate(self.MatchId.keys()):
            self.MarketId = {}
            market = self.MatchId[match_id]['Market']
            logger.info('match_id : %s, 資訊: %s'%(match_id, self.MatchId[match_id]   ))
            data = {"GameId": self.gameid ,"DateType":market,"BetTypeClass":self.bet_type,"Matchid":match_id,"Gametype":1}
            try:
                r = self.client_session.post(self.url  + '/Odds/GetMarket',data=data,headers=self.headers)
                repspone_json = r.json()
                #logger.info('repspone_json: %s'%repspone_json) 
            except:
                logger.info('mobile GetMarket Api Fail')
                continue
            try:
                # 回傳的 資料結構不同
                if self.bet_type == 'parlaymore':
                    NewOdds = repspone_json['Data']['Markets']['NewOdds']# 一個list 裡面包一個長度的dict
                else:
                    NewOdds = repspone_json['Data']['NewOdds']
                
                MatchId_value = self.MatchId[match_id]
                
                for dict_ in NewOdds:#list包字典# ,裡面 一個dict 會有 很多 marketid (Oddsid)要取得
                    #logger.info('dict: %s'%dict_)
                    new_dict = {}
                    
                    MarketId = dict_['MarketId']
                    new_dict['MatchId'] = dict_['MatchId']
                    new_dict['BetTypeId'] = dict_['BetTypeId']
                    
                    new_dict['Line'] = dict_['Line']

                    Selecetion_key =  list(dict_['Selections'].keys())# 為一個betype 下面 所有的bet choice

                    for bet_choice_index, bet_choice in enumerate(Selecetion_key): 
                        odds = dict_['Selections'][bet_choice]['Price']
                        new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                        new_dict['odds_%s'%bet_choice_index] = odds
                    
                    new_value = MatchId_value.copy()# 原本
                    new_value.update(new_dict)# 新的放進來
                    self.MarketId[MarketId] = new_value
                
                Market_value = self.MarketId
                self.Match_dict[index] = Market_value
                if index == int(parlay_len) - 1:
                    logger.info('串%s場即可'%parlay_len)
                    logger.info(self.MarketId)
                    break


            except Exception as e:
                logger.error('GetMarket: %s'%e)
                return False
        logger.info('self.Match_dict 0 : %s'%len(self.Match_dict[0] ))
        if int(parlay_len) ==3:
            logger.info('self.Match_dict 1 : %s'%len(self.Match_dict[1]))
            logger.info('self.Match_dict 2: %s'%len(self.Match_dict[2]))

    def Betting_response(self,response,times):# 針對 投注 回復 做解析
        repspone_json = response.json()
        
        if 'parlay'  in self.bet_type:
            Data = repspone_json['Data']
            response_code = str(Data['Code'])
            Message = Data['Message']
            if response_code == '45':# HDP/OU has been changed
                logger.error('ErrorMsg: %s'%repspone_json['ErrorMsg'] ) 
                logger.info('Message: %s'%Message)

                #self.fail_bettype.append(BetTypeId_list[0])
                return False
            
            elif response_code == '-91':# update odds
                logger.info('Message: %s'%Message)
                logger.info('休息 兩秒鐘 再做')
                time.sleep(2)
                return '重新'

            elif response_code == '15':# odds has changed
                logger.info('Message: %s'%Message)
                ItemList = Data['ItemList']
                logger.info('ItemList: %s'%ItemList)# 一個list 裡面包 多個dict ,確認 每個 單 是否都有 odds changed
                
                
                odds_change_dict = {}# 變更後的odds , key 為 matchid , value 為 odds
                for dict_ in ItemList:
                    if str(dict_['Code']) == '15':# odds changed
                        Matchid = dict_['Key']
                        odds_change = dict_['Message'].split('to')[-1].strip('.').replace(' ','')# 切割完, 在移除最後一個 . 移除空白
                        logger.info('odds_change: %s'%odds_change)
                        odds_change_dict[Matchid] = odds_change    
                logger.info('odds_change_dict: %s'%odds_change_dict)

                for matchid in odds_change_dict.keys():# 把 變更後的odds 取出
                    og_odds = str(self.Odds_dict[matchid])# 把原本的 odds取出
                    odds_change = odds_change_dict[matchid]# 如果遇到 多個 相同的odds, 目前寫法可能有問題
                    data_str = data_str.replace( og_odds, odds_change)
                    self.Odds_dict[matchid] = odds_change # 從新變更dict
                if self.retry_count == 1: 
                    return 'retry 完'
                self.retry_count = self.retry_count + 1
                time.sleep(5)# 系統 有防止 快速 打 接口 ,回復 We are updating odds, please try again later
                
            elif response_code in ['0','1']:# 投注成功
                order_value = {}
                order_value['Message'] = Message

                TransId_Combo = Data['TransId_Combo']
                TransId_System = Data['TransId_System']

                TotalPerBet =  Data['TotalPerBet']
                order_value['TotalPerBet'] = TotalPerBet
                FinalBalance = Data['FinalBalance']
                order_value['FinalBalance'] = FinalBalance
                order_value['BetTypeId_list'] = self.BetTypeId_list
                
                Odds_list = list(self.Odds_dict.values() )
                Match_list = list(self.Odds_dict.keys() )
                if TransId_Combo in ['0','']:
                    order_value['注單ID'] = TransId_System

                else:
                    order_value['注單ID'] = TransId_Combo

                order_value['Match_list'] = Match_list
                order_value['Odds_list'] = Odds_list
                self.Order_dict[times] = order_value
                
                logger.info('order_value: %s'%order_value)
                return True
            
            else:#例外 沒抓到的 code
                logger.info('response_code : %s'%response_code)
                logger.info('Message: %s'%Message)
                return 'Bet Fail !'
        else:# single bet
            '''
            #  ItemList 為一個 list ,裡面 放各資訊 字典 
            '''
            order_value = {}
            Itemdict = repspone_json['Data']['ItemList'][0]# Itemdict 為一個字典
            logger.info('betting response Error Code: %s'%repspone_json['Data']['Common']['ErrorCode'])

            order_value['TransId_Cash'] = Itemdict['TransId_Cash']
            order_value['Message'] = Itemdict['Message']
            logger.info('betting response message: %s'%Itemdict['Message'])
            
            try:
                order_value['DisplayOdds'] = Itemdict['DisplayOdds']
                
                BetRecommends = Itemdict['BetRecommends'][0]# 為一個 list ,裡面含 各個 bet type資訊
                order_value['BettypeName'] = BetRecommends['BettypeName']
                order_value['LeagueName'] = BetRecommends['LeagueName']

                logger.info('order_value  : %s'%order_value)
                return True
            except:
                return False
            

        
        
    '''
    already_list 是有做過的bettype , 拿來 驗證 做過的bettype, 做 random bettype 5次 
    parlay_type 1 為 mix parlay , 2 為 Trixie (4 Bets) , 為空 為 Single bet
    bet_team_index 是拿來 要做 betttype 的 哪個bet choice , 一個bettype 下 正常會有 bet_team_1 , bet_team_2 ...甚至更多
    assign_list 是用來指定 bettype下注, 空字串就是不用,走random ,有值的話 , key 為 market value為
    '''
    def DoplaceBet(self,already_list=[],bet_team_index='0',parlay_type='1',assign_list='',times=''):
        import random
        '''
        SportName 和 gameid 之後 做動態傳入,目前寫死 
        '''
        self.BetTypeId_list = []
        self.Odds_dict = {}# key 為 match id ,value 為 odds
        Parlay_dict = {'1' : '1', '2': '4' }# value 是拿來 給 parlay data 的  BetCount 和 TotalStake

        len_Match_dic= len(self.Match_dict )
        logger.info('len_Match_dict : %s'%len_Match_dic)
        if assign_list == '':# 預設為字串 ,使用隨機l
            try:
                data_str = ""# 需loop 慢慢加起來
                for index_key in self.Match_dict.keys():#index_key 為 數值 ,一個 match 比賽 , 就是一個key
                    #logger.info('index_key : %s'%index_key)
                    Match = self.Match_dict[index_key]# key 為 Oddsid ,value為 字典,涵蓋 各種 資訊
                    #logger.info('len : %s'%len(Match))

                    Match_key_list = list(Match.keys())# list裡面放 bettype

                    retry_count = 0
                    while True:
                        ran_index = random.randint(0, len(Match_key_list) -1  )
                        Ran_Match_id =   Match_key_list[ran_index]# 隨機取出 odds id
                        logger.info('Ran_Match_id: %s'%Ran_Match_id)
                    
                        BetTypeId = Match[Ran_Match_id]['BetTypeId']
                        if BetTypeId not in already_list:
                            logger.info('BetTypeId: %s 沒有投注過 ,成立'%BetTypeId)
                            break
                        logger.info('BetTypeId: %s 已經存在過注單裡 ,retry : %s'%(BetTypeId, retry_count ))
                        retry_count = retry_count + 1
                        if retry_count >= 10:   
                            break

                    Matchid = Match[Ran_Match_id]['MatchId']
                    Team1 = Match[Ran_Match_id]['Team1']
                    Team2 = Match[Ran_Match_id]['Team2']
                    try:# 有些 bettype 下 會有超過 2的長度, 如果 傳2 以上會爆錯, 就統一用 0來代替
                        odds = Match[Ran_Match_id]['odds_%s'%bet_team_index]
                    except:
                        odds = Match[Ran_Match_id]['odds_0']
                    
                    try:# 有些 bettype 下 會有超過 2的長度, 如果 傳2 以上會爆錯, 就統一用 0來代替
                        bet_team = Match[Ran_Match_id]['bet_team_%s'%bet_team_index]
                    except:
                        bet_team = Match[Ran_Match_id]['bet_team_0']
                    
                    oddsid = Ran_Match_id
                    BetTypeId = Match[Ran_Match_id]['BetTypeId']
                    
                    Line = Match[Ran_Match_id]['Line']
                    if  Line == 0:
                        Line = ''
                
                    #if index > 2 and set_bet == 1:#串三個即可 . set_bet = 1代表
                        #break

                    '''
                    parlay
                    其他sport 拿到的 odds 需轉成 Dec Odds , Cricket 原本就是 dec odds所以不做轉換 
                    5: Ft 1x2 , 15: 1H 1x2(原本就是 dec odds, 不用轉) 
                    '''
                    if 'parlay' not in self.bet_type : # single odds 先不轉
                        bet_stake = 1
                        pass
                        
                    else:# parlay
                        bet_stake = ''

                        if  self.gameid != 50:# cricket 的不用轉 
                            if BetTypeId not in [5, 15]:#  5: Ft 1x2 , 15: 1H 1x2 他們是 屬於Dec Odds
                                odds = self.Odds_Tran(odds)
                                logger.info('%s bettype: %s , 需轉乘 Dec odds: %s'%( self.sport,BetTypeId, odds) )

                    try:
                        data_format = "ItemList[{index_key}][type]={bet_type}&ItemList[{index_key}][bettype]={BetTypeId}&ItemList[{index_key}][oddsid]={oddsid}&ItemList[{index_key}][odds]={odds}&\
                        ItemList[{index_key}][Line]={Line}&ItemList[{index_key}][Hscore]=0&ItemList[{index_key}][Ascore]=0&ItemList[{index_key}][Matchid]={Matchid}&ItemList[{index_key}][betteam]={betteam}&\
                        ItemList[{index_key}][stake]={bet_stake}&ItemList[{index_key}][QuickBet]=1:100:10:1&ItemList[{index_key}][ChoiceValue]=&ItemList[{index_key}][home]={Team1}&\
                        ItemList[{index_key}][away]={Team2}&ItemList[{index_key}][gameid]={gameid}&ItemList[{index_key}][isMMR]=0&ItemList[{index_key}][MRPercentage]=&ItemList[{index_key}][GameName]=&\
                        ItemList[{index_key}][SportName]=C&ItemList[{index_key}][IsInPlay]=false&ItemList[{index_key}][SrcOddsInfo]=&ItemList[{index_key}][pty]=1&ItemList[{index_key}][hdp1]={Line}&\
                        ItemList[{index_key}][hdp2]=0&ItemList[{index_key}][BonusID]=0&ItemList[{index_key}][BonusType]=0&ItemList[{index_key}][sinfo]=53FCX0000&ItemList[{index_key}][hasCashOut]=false\
                        ".format(index_key= index_key, BetTypeId=BetTypeId, oddsid=oddsid ,Matchid = Matchid ,
                        Team1 =Team1, Team2= Team2 ,odds=odds ,gameid = self.gameid,betteam = bet_team,
                        Line = Line, bet_type = self.bet_type, bet_stake = bet_stake )
                    except Exception as e:
                        logger.error('data_format: %s'%e)

                    data_str = data_str + data_format + '&'
                    '''
                    parlay 串多少match 邏輯
                    當 index 到了 總長度 的最後, 須把 combo_str 家回data裡
                    '''
                    if index_key == len_Match_dic -1 :
                        if 'parlay'  in self.bet_type :# parlay
                            if parlay_type == '2':# system parlay ,的total stake 要根據 長度 來做動態 計算
                                TotalStake = len_Match_dic - 3 +  3# 如果 總長度 為4 . 4- 3  +  4
                            else: # Mix parlay 
                                TotalStake = int(Parlay_dict['1'])
                            if len_Match_dic > 3:
                                if parlay_type == '1':
                                    combo_type = 4
                                else:
                                    combo_type = 1
                            else:
                                combo_type = parlay_type
                            combo_str = "ComboLists[0][Type]={combo_type}&ComboLists[0][BetCount]={parlay_value}&ComboLists[0][Stake]=1&Combi=false&IsAnyOdds=false&\
                            TotalStake={TotalStake}".format(combo_type=combo_type, parlay_value= Parlay_dict[parlay_type],TotalStake = TotalStake )
                            
                            data_str = data_str + combo_str
                        else:# single

                            combo_str = "&ItemList[0][Minbet]=1"

                            data_str = data_str + combo_str
                            
                            r = self.client_session.post(self.url  + '/BetV2/GetTickets',data = data_str.encode(),
                                    headers=self.headers)# data_str.encode() 遇到中文編碼問題 姊法
                            try:
                                logger.info('GetTickets OK')
                            except:
                               logger.error('Single Bet Get Ticket 有誤')
                            if index_key == 0:
                                break 

                    
                    #self.Odds_dict[Matchid] = odds 
                    #self.BetTypeId_list.append(BetTypeId)
                
                #logger.info('BetTypeId_list: %s'%self.BetTypeId_list)
                #logger.info('OddsId :%s'%self.Odds_dict)
            except Exception as e:
                logger.error('DoplaceBet: %s'%e)
        
        else:# 指定 betlist 投注
            Match_dict = self.Return_Bet_dict(assign_list)
            data_str = ""
            for index_key in Match_dict.keys():
                
                oddsid = list(Match_dict[index_key].keys())[0]
                BetTypeId = Match_dict[index_key][oddsid]['BetTypeId']
                Matchid = Match_dict[index_key][oddsid]['MatchId']
                Team1 = Match_dict[index_key][oddsid]['Team1']
                Team2 = Match_dict[index_key][oddsid]['Team2']
                
                Line = Match_dict[index_key][oddsid]['Line']
                if  Line == 0:
                    Line = ''
                
                try:# 有些 bettype 下 會有超過 2的長度, 如果 傳2 以上會爆錯, 就統一用 0來代替
                    odds = Match_dict[index_key][oddsid]['odds_%s'%bet_team_index]
                except:
                    odds = Match_dict[index_key][oddsid]['odds_0']
                
                try:# 有些 bettype 下 會有超過 2的長度, 如果 傳2 以上會爆錯, 就統一用 0來代替
                    bet_team = Match_dict[index_key][oddsid]['bet_team_%s'%bet_team_index]
                except:
                    bet_team = Match_dict[index_key][oddsid]['bet_team_0']

                try:
                    data_format = "ItemList[{index_key}][type]=parlay&ItemList[{index_key}][bettype]={BetTypeId}&ItemList[{index_key}][oddsid]={oddsid}&ItemList[{index_key}][odds]={odds}&\
                    ItemList[{index_key}][Line]={Line}&ItemList[{index_key}][Hscore]=0&ItemList[{index_key}][Ascore]=0&ItemList[{index_key}][Matchid]={Matchid}&ItemList[{index_key}][betteam]={betteam}&\
                    ItemList[{index_key}][stake]=&ItemList[{index_key}][QuickBet]=1:100:10:1&ItemList[{index_key}][ChoiceValue]=&ItemList[{index_key}][home]={Team1}&\
                    ItemList[{index_key}][away]={Team2}&ItemList[{index_key}][gameid]={gameid}&ItemList[{index_key}][isMMR]=0&ItemList[{index_key}][MRPercentage]=&ItemList[{index_key}][GameName]=&\
                    ItemList[{index_key}][SportName]=C&ItemList[{index_key}][IsInPlay]=false&ItemList[{index_key}][SrcOddsInfo]=&ItemList[{index_key}][pty]=1&ItemList[{index_key}][hdp1]={Line}&\
                    ItemList[{index_key}][hdp2]=0&ItemList[{index_key}][BonusID]=0&ItemList[{index_key}][BonusType]=0&ItemList[{index_key}][sinfo]=53FCX0000&ItemList[{index_key}][hasCashOut]=false\
                    ".format(index_key= index_key, BetTypeId=BetTypeId, oddsid=oddsid ,Matchid = Matchid ,
                    Team1 =Team1, Team2= Team2 ,odds=odds ,gameid = self.gameid,betteam = bet_team,Line = Line )
                except Exception as e:
                    logger.error('data_format: %s'%e)

                data_str = data_str + data_format + '&'
                if index_key == len(Match_dict) -1 :
                    if parlay_type == '2':# system parlay ,的total stake 要根據 長度 來做動態 計算
                        TotalStake = len_Match_dic - 3 +  3# 如果 總長度 為4 . 4- 3  +  4
                    else: # Mix parlay 
                        TotalStake = int(Parlay_dict['1'])
                    if len_Match_dic > 3:
                        if parlay_type == '1':
                            combo_type = 4
                        else:
                            combo_type = 1
                    else:
                        combo_type = parlay_type
                    combo_str = "ComboLists[0][Type]={combo_type}&ComboLists[0][BetCount]={parlay_value}&ComboLists[0][Stake]=1&Combi=false&IsAnyOdds=false&\
                    TotalStake={TotalStake}".format(combo_type = combo_type, parlay_value= Parlay_dict[parlay_type] ,TotalStake =TotalStake )
                    
                    data_str = data_str + combo_str
                self.BetTypeId_list.append(oddsid)
            logger.info('BetTypeId_list :%s'%self.BetTypeId_list)
        
        retry_count = 0

        try:
            import re
            data_str = re.sub(r"\s+", "", data_str)# 移除空白,對 打接口沒影響 ,只是 data好看 

            #self.headers['Cookie'] = 'ASP.NET_SessionId='+ self.login_session[user]
            post_data =  data_str
            
            if 'parlay' in  self.bet_type:
                r = self.client_session.post(self.url  + '/BetParlay/DoplaceBet',data = post_data.encode(),
                headers=self.headers)# data_str.encode() 遇到中文編碼問題 姊法
            else:# single bet
                r = self.client_session.post(self.url  + '/BetV2/ProcessBet',data = post_data.encode(),
                headers=self.headers)# data_str.encode() 遇到中文編碼問題 姊法

          
            
            return self.Betting_response(response=r, times=times)

            #logger.info('repspone_json: %s'%repspone_json)   

        except Exception as e:
            logger.info('mobile DoplaceBet Api Fail: %s'%e)
            return False




class Desktop_Api(Login):    
    def __init__(self,client="",device="",user='',url= ''):
        super().__init__(device)
        self.login = None
        self.user = user
        self.url = url
        self.login_type = ''# api site
        if client == '':
            self.client_session = self.session
        else:
            self.client_session = client
        if 'athena' in self.url:
            self.login_type = 'athena' # 是 api site 登入 還是  athena site登入 , login方式不一樣
    
    def desktop_login(self,central_account='',central_password=''):# PC端 login街口 邏輯
        '''加密邏輯 呼叫'''
        if self.login_type == 'athena':# athena 的登入 方式 , 會須使用 js 加密
            common_js = execjs.compile(self.js_from_file('./login_js/dsektop.js'))# 讀取 login js檔
            cfs_psswd = common_js.call("CFS", '1q2w3e4r')# password先做 前端 CFS 加密
            val = self.assert_validation()# 取得驗證碼
            md5_psswd = self.md(password = cfs_psswd,val = val)# md5 將 Cfs加密 的密碼   跟 驗證碼 做md5
            login_data = "txtUserName={0}&txtPasswd={1}&txtValidCode={2}".format( self.user ,md5_psswd,val)
            if len(self.cookies) != 0:# aspx 的會為空 list
                asp_cookie = ''# 先初始 空字串, 後面 加起來
                for index,con_dict in enumerate(self.cookies): #self.cookies為 list 包 dict
                    cookie_name = con_dict['name']
                    cookie_value = con_dict['value']
                    asp_cookie = asp_cookie + '%s=%s'%(cookie_name,cookie_value)
                    #logger.info('asp_cookie: %s'%asp_cookie)
                    if index == 0: 
                        asp_cookie = asp_cookie + ';'# 因為會要串兩個 cookie 字串,需要用 ; 來傳進去
                logger.info('asp_cookie: %s'%asp_cookie)
                self.headers['Cookie'] = asp_cookie

        else:# api site
            if 'onelogin' not in self.url:# 多幫忙檢查 ,需要帶 onelogin
                self.url = self.url + '/onelogin.aspx'
            r = self.client_session.get(self.url  ,headers=self.headers)# 需先拿 session url
            
            self.url  = r.url.split('/onelogin.aspx')[0]# 回復的url 需再拿掉 onelogin.aspx . 再去打 despoist login
            logger.info('onelogin 需 先拿session url: %s'%self.url )
            # 然後 在用 這個 session url 去拿 驗證碼 ,但要移除  /onelogin.aspx

            login_data = "lang=en&WebSkinType=&matchid=&leaguekey=&market=T&menutype=0&act=sports&game=&gamename=&gameid=&Otype=&HomeUrl=&deposit=&extendSessionUrl=&Link=&Sport=&Date=&SkinColor=&centralAccount={central_account}&centralPassword={central_password}&txtUserName={user}&txtPasswd=1q2w3e4r&token=&TSID=&txtValidCode=&hidubmit=YES".format(central_account=central_account,central_password=central_password,user=self.user )

        self.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        self.headers['X-Requested-With'] =  'XMLHttpRequest'
        r = self.client_session.post(self.url  + '/DepositProcessLogin',data=login_data,headers=self.headers)
        
        try:
            #if self.login_type == 'athena':# athena 回復格式 有json 
            repspone_json = r.json()
            logger.info('response: %s'%repspone_json)
            if repspone_json['ShowErrorMsg'] == 'The validation code has expired.' or repspone_json['ErrorCode'] !='':
                logger.info('登入 Fail')
                return False

            reponse_url = r.json()['url']# 取得登入後 轉導url
            logger.info('reponse_url: %s'%reponse_url)
        
            if 'qasb' in self.url or 'xide' in self.url:# 有sesion 的判斷
                Val_url = '%s'%( reponse_url)
                logger.info('Val_url: %s'%Val_url)#/ValidateTicket?Guid=fa426c9c-739d-4b37-9589-db13ab0b1cdd
                r = self.client_session.get(Val_url,headers=self.headers )
                logger.info('r.url: %s'%r.url)
                u = urlparse(r.url)
                self.member_url = 'http://%s%s'%(u.netloc,u.path)
                self.member_url = self.member_url.split('/ValidateTicket')[0]
                logger.info('self.member_url: %s'%self.member_url)

                r = self.client_session.get(self.member_url +  '/NewIndex?lang=en&rt=0&webskintype=2',headers=self.headers )
                
            else:
                u = urlparse(reponse_url)# 擷取 動態 member_url 
                self.member_url = 'http://%s'%u.netloc
                logger.info('member_url: %s'% self.member_url)

                r = self.client_session.get(reponse_url,headers=self.headers )
            self.login = 'login ready'
            
            return True

        except:
            logger.info('登入 Fail')
            return False

    def balance(self):# /NewIndex/GetWalletBalance
        balance_info_data = 'TZone=8'
        self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
        post_url = self.member_url  + '/NewIndex/GetWalletBalance'
        logger.info('post_url: %s'%post_url)

        logger.info('header: %s'%self.headers)
        r = self.client_session.post( post_url,data=balance_info_data,headers=self.headers)
        try:
            repspone_json = r.json()
            logger.info('response: %s'%repspone_json)
            return True
        except:
            logger.info('desktop balance Api Fail')
            return False
    
    def hm_sport(self):# /NewIndex/GetWalletBalance
       
        self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
        self.hm_url = self.member_url.replace('member','hm')
        
        logger.info('hm_url: %s'%self.hm_url)

        logger.info('header: %s'%self.headers)
        r = self.client_session.get( self.hm_url + '/NewIndex/GetWalletBalance',headers=self.headers)
        cookie_session = self.client_session.cookies.get_dict()
        logger.info('cookie_session: %s'%cookie_session)
        try:
            repspone_json = r.json()
            logger.info('response: %s'%repspone_json)
            return True
        except:
            logger.info('desktop balance Api Fail')
            return False

    def show_sports(self):# /Sports/

        #用於抓取登入後的 hm session id
        self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
        post_url = self.member_url + '/EntryIndex/OpenSports'
        logger.info('post_url: %s'%post_url)
        open_sports = self.session.get(post_url,headers = self.headers)
        cookie_session = self.session.cookies.get_dict()
        
        if self.login_type == 'athena':
            NET_SessionId = cookie_session['ASP.NET_SessionId']
        
            logger.info('NET_SessionId: %s'%NET_SessionId)
            self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
            self.headers['Cookie'] = "ASP.NET_SessionId=" + NET_SessionId
            self.hm_url = self.member_url.replace('member','hm')

            post_url = self.hm_url  + '/Sports/'
            logger.info('post_url: %s'%post_url)

            logger.info('header: %s'%self.headers)
            r = self.client_session.get( post_url,headers=self.headers)
            try:
                sucess_data = re.findall("<html.+>",r.text)[0]
                return r.text
            except Exception as e:
                logger.info('desktop balance Api Fail : %s'%str(e))
                return False
        else: #由於 api site opensports 打出後，會自動回傳 Sport API，不須像 Athena 再去打，所以直接判斷回傳是否正確
            try:
                sucess_data = re.findall("<html.+>",open_sports.text)[0]
                return sucess_data
            except Exception as e:
                return open_sports.text

    def check_whats_new_picture(self): #確認圖片是否會在網頁圖片 List 裡
        print(self.url)
        self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
        if "www" in self.url:
            self.url = self.url.replace("www","hm")
        else:
            pass
        r = self.client_session.post(self.url + '/Promotion/GetWhatIsNewData',headers=self.headers)
        print(r.text)


'''
#In[]
api = Login(sec_times = 1 ,stop_times = 1 ).login_api(device='mobile', user= 'twqa09',
 url = 'http://qasb2.athena000.com:50006/',
 central_account='',central_password='' )


#In[]
#api.get_contirbutetor()


#In[]


api.threads(func_name_list = [   api.balance ] )



#In[]

print (api.stress_dict)



'''
