#In[]

from logging import log
import threading
import execjs
import hashlib
from PIL import Image
from numpy import False_
import pytesseract,os,time
from  Logger import create_logger 
import pathlib
from Common import Common

from urllib.parse import urlparse


#In[]
class Login(Common):#取得驗證碼邏輯 
    def __init__(self,device="",sec_times='',stop_times='',url=''):
        super().__init__(sec_times,stop_times)
        self.logger = create_logger(r"\AutoTest", 'test')
        if device == 'Pc':
            self.dr = self.get_driver()
        self.img_pic = pathlib.Path(__file__).parent.absolute().__str__() + "login_code.jpg"
        self.download_waiting_time = 3
        self.url = url
        self.cookies = ""# 預設空, 會從驗證碼時,拿取 ASP.NET_SessionId


    def validation(self):
    # 取得圖片
        #self.logger.info(self.img_pic)
        login_code = Image.open(self.img_pic)
        self.logger.info(login_code)
        # result.show()
        # 驗證碼圖片修正 轉為白底黑字
        identify_result = self.convert_img(login_code, 225)
        # result.show()
        pytesseract.pytesseract.tesseract_cmd = 'Tesseract-OCR\\tesseract.exe'
        identify_result = pytesseract.image_to_string(identify_result).strip()
        # 刪除圖片
        os.remove(self.img_pic)
        self.logger.info('圖片刪除成功')
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
            if 'qasb' in self.url:# qasb 測試環境 url輸入後 取得當前 xideqseTWIN 的url
                self.dr.get(self.url)
                current_url = self.dr.current_url# 取得轉換後的測試url ex: http://qasb.athena000.com:42104/(S(xideqseTWIN-Avzh25wrew0zndzoe3tmqiamhf2X-MXwjdkH3qs47fawD1gZZ))/
                self.url = current_url.split('?')[0]#?scmt=tab01&ssmt=tab01 移除
                self.logger.info('轉換url : %s'%self.url )
                login_code_url = '%s/login_code.aspx?%s'%(self.url,now)
                self.dr.get(login_code_url)
            else:#Production
                login_code_url = '%s/login_code.aspx?%s'%(self.url,now)
                self.logger.info('login_code_url: %s'%login_code_url)
                self.dr.get(login_code_url)
            
            self.dr.get_screenshot_as_file(self.img_pic)
            for i in range(self.download_waiting_time):
                if os.path.isfile(self.img_pic):
                    self.logger.info('圖片有找到')
                    break
                else:
                    self.logger.info('圖片未找到')
                    time.sleep(1)
                    if i == self.download_waiting_time - 1:
                        raise IOError

            validate_result = self.validation()
            
            if validate_result.isdigit() is False:# 檢查取得的驗證碼是否都是數值,如果有字母 馬上retry
                self.logger.info('有英文字 %s,直接retry'%validate_result)
            elif len(validate_result) < 4:#長度小於4也要retry
                self.logger.info('長度小於4 %s,直接retry'%validate_result)
            else:
                self.logger.info('validate_result: %s'%validate_result)
                if 'qasb' in self.url:
                    break
                self.cookies = self.dr.get_cookies()
                self.logger.info('cookies: %s'%self.cookies )
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
            self.logger.info('PKey: %s'%PWKEY) 
            return PWKEY 
        except:
            self.logger.error('PKey: 取得失敗') 
            return False
    

class Mobile_Api(Login):# Mobile 街口  ,繼承 Login
    def __init__(self,device="",url='',password=''):
        super().__init__(device) 
        self.login_session = {}# key 為 user ,value 放 NET_SessionId
        self.url = url
        self.password = password
        self.Order_dict = {}#  key 訂單,value 為 BetTypeId_list
        self.fail_bettype = []# 存放失敗 的bettype 
        self.MatchId = {}# 存放 matchid value 放team
        self.MarketId = {}
        '''
        if self.login is None:
            self.mobile_login()
        '''

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


    def mobile_login(self,user):# Mobile Login街口邏輯
        common_js = execjs.compile(self.js_from_file('./login_js/mobile.js'))# 讀取 login js檔

        PKey = self.get_Pwekey()
        cfs_psswd = common_js.call("r", self.password ,PKey)#App 密碼加密,適用 密碼和 PKey 去做前端js處理
        self.logger.info('app cfs_psswd: %s'%cfs_psswd)

        login_data = 'Username={user}&Password={cfs_psswd}&Language=zh-CN&isGesture=false\
        &skinMode=3%3D%3D&__tk=&detecas_analysis=%7B%22startTime%22%3A1630246986799%2C%22version\
        %22%3A%222.0.6%22%2C%22exceptions%22%3A%5B%5D%2C%22executions%22%3A%5B%5D%2C%22storages%22%3A%5B%5D%2C%22devices%22%3A%5B%5D%2C%22\
        enable%22%3Atrue%7D'.format(user=user, cfs_psswd=cfs_psswd)

        self.headers['X-Requested-With'] =  'XMLHttpRequest'
        self.headers['Content-Type'] =  'application/x-www-form-urlencoded; charset=UTF-8'
        #self.logger.info('headers: %s'%self.headers)
        
        r = self.session.post(self.url  + '/Login/index',data=login_data,headers=self.headers)
        try:
            repspone_json = r.json()
            #self.logger.info('response: %s'%repspone_json)
            ErrorMsg = repspone_json['ErrorMsg']
            self.logger.info('ErrorMsg: %s'%ErrorMsg)
            if ErrorMsg != 'login_success':
                return ErrorMsg
            Data_url = repspone_json['Data']# 登入成功後, 需在get 一次 response 回傳的 url
            r = self.session.get(self.url  + Data_url, headers=self.headers)
            #self.login = 'login ready'

            cookie_session = self.session.cookies.get_dict()
            NET_SessionId = cookie_session['ASP.NET_SessionId']
            self.logger.info('NET_SessionId: %s'%NET_SessionId )
            self.login_session[user] = NET_SessionId
            #self.logger.info('self.login_session: %s'%self.login_session)
            return True
        except:
            self.logger.info('Login Api Fali')
            return False

    def balance(self):# /balance/GetAccountInfo
        
        balance_info_data = 'localtime=8'
        self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
        r = self.session.post(self.url  + '/balance/GetAccountInfo',data=balance_info_data,headers=self.headers)
        try:
            repspone_json = r.json()
            self.logger.info('response: %s'%repspone_json)
            return True
        except:
            self.logger.info('mobile balance Api Fali')
            return False

    '''
    type 帶 test 就 可以 忽略 testing 比賽 
    '''
    def ShowAllOdds(self,type='',market='l',filter='',sport=''):# 取得 MatchId 傳給 GetMarket , 還有取得 TeamN 回傳給 DoplaceBet  的 home/away
        
        # e為 早盤, t為 today
        #market = 't'# 預設 today
        self.sport = sport
        self.gameid = self.game_mapping(self.sport)# 後面 get market 和 betting 就不用在多傳 gameid 參數了, 統一在這宣告
        for market in market:
            data = 'GameId=%s&DateType=%s&BetTypeClass=parlay&Gametype=1'%(self.gameid  ,market)# 先寫死cricket, 之後優化
            self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
            
            try:
                r = self.session.post(self.url  + '/Odds/ShowAllOdds',data=data,headers=self.headers)
                repspone_json = r.json()
                #self.logger.info('repspone_json: %s'%repspone_json)   
            except:
                self.logger.info('mobile ShowAllOdds Api Fali')
                return False
            
            try:
                Data = repspone_json['Data']# 字典 裡面包兩個key, NewMatch 和 TeamN
                NewMatch = Data['NewMatch']# list
                TeamN = Data['TeamN']# dict
                LeagueN = Data['LeagueN']
                #self.logger.info('TeamN: %s'%TeamN)
                for index,dict_ in enumerate(NewMatch):
                    #self.logger.info('index: %s'%index)
                    team_name = {}
        
                    TeamId1 = dict_['TeamId1']
                    TeamId2 = dict_['TeamId2']
                    LeagueId = dict_['LeagueId']
                    League_name = LeagueN[str(LeagueId)]

                    if type == '':# 不能有test 的賽事 
                        if any(test_parlay in League_name for test_parlay in  ['TESTING','test','Test'] ):# 如果 不是要 針對test 然後 testing 又再 league ,不能串
                            continue
                    # type 帶 test 就 可以 忽略 testing 比賽 
                    team_name['Team1'] = TeamN[ str(TeamId1) ]
                    team_name['Team2'] = TeamN[str(TeamId2) ]
                    team_name['League'] = League_name
                    team_name['Market'] = market
                    
                    #self.logger.info('team_name: %s'%team_name)
                    MatchId = dict_['MatchId']# 取出Matchid ,並當作 Key
                    self.MatchId[MatchId] = team_name# MatchId 當key ,value為 teamname
            except Exception as e:
                self.logger.error('ShowAllOdds: %s'%e)
                return False
        if  filter != '' and len(filter) != 0 :# 只拿指定 的match id , 防呆 fiter如果帶空list
            for key in list(self.MatchId):
                if key not in filter:
                    del self.MatchId[key]
        len_matchid = len(self.MatchId)
        self.logger.info('self.MatchId: %s'%self.MatchId)
        self.logger.info('len MatchId: %s'%len_matchid )
        
        if len_matchid < 3:
            self.logger.info('長度小於3 無法串票')
            return 'False'


    '''
    parlay_len 預設 給3 是 找三個match 來串即可, 如果不是 3 就是 給其他長度
    BetType 預設為 parlay . parlaymore 為更多 bet

    取得   MarketId(oddsid), Price(odds) , BetTypeId
    '''
    def GetMarket(self,parlay_len='3',BetType='parlay'):
        self.Match_dict = {}# key 當作 index, value 存放 該match id 裡所有 的bettype(self.MarketId)
        
        for index,match_id in enumerate(self.MatchId.keys()):
            self.MarketId = {}
            market = self.MatchId[match_id]['Market']
            data = {"GameId": self.gameid ,"DateType":market,"BetTypeClass":BetType,"Matchid":match_id,"Gametype":1}
            try:
                r = self.session.post(self.url  + '/Odds/GetMarket',data=data,headers=self.headers)
                repspone_json = r.json()
                #self.logger.info('repspone_json: %s'%repspone_json) 
            except:
                self.logger.info('mobile GetMarket Api Fali')
                continue
            try:
                # 回傳的 資料結構不同
                if BetType == 'parlaymore':
                    NewOdds = repspone_json['Data']['Markets']['NewOdds']# 一個list 裡面包一個長度的dict
                else:
                    NewOdds = repspone_json['Data']['NewOdds']
                
                MatchId_value = self.MatchId[match_id]
                
                for dict_ in NewOdds:#list包字典# ,裡面 一個dict 會有 很多 marketid (Oddsid)要取得
                    #self.logger.info('dict: %s'%dict_)
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
                    self.logger.info('串%s場即可'%parlay_len)
                    break


            except Exception as e:
                self.logger.error('GetMarket: %s'%e)
                return False
        self.logger.info('self.Match_dict 0 : %s'%len(self.Match_dict[0] ))
        self.logger.info('self.Match_dict 1 : %s'%len(self.Match_dict[1]))
        self.logger.info('self.Match_dict 2: %s'%len(self.Match_dict[2]))

        
    '''
    already_list 是有做過的bettype , 拿來 驗證 做過的bettype, 做 random bettype 5次 
    parlay_type 1 為 mix parlay , 2 為 Trixie (4 Bets)
    bet_team_index 是拿來 要做 betttype 的 哪個bet choice , 一個bettype 下 正常會有 bet_team_1 , bet_team_2 ...甚至更多
    assign_list 是用來指定 bettype下注, 空字串就是不用,走random ,有值的話 , key 為 market value為
    '''
    def DoplaceBet(self,user,already_list=[],bet_team_index='0',parlay_type='1',assign_list=''):
        import random
        '''
        SportName 和 gameid 之後 做動態傳入,目前寫死 
        '''
        BetTypeId_list = []
        Odds_dict = {}# key 為 match id ,value 為 odds
        Parlay_dict = {'1' : '1', '2': '4' }# value 是拿來 給 parlay data 的  BetCount 和 TotalStake

        len_Match_dic= len(self.Match_dict )
        self.logger.info('len_Match_dict : %s'%len_Match_dic)
        if assign_list == '':# 預設為字串 ,使用隨機
            try:
                data_str = ""# 需loop 慢慢加起來
                for index_key in self.Match_dict.keys():#index_key 為 數值 ,一個 match 比賽 , 就是一個key
                    #self.logger.info('index_key : %s'%index_key)
                    Match = self.Match_dict[index_key]# key 為 Oddsid ,value為 字典,涵蓋 各種 資訊
                    #self.logger.info('len : %s'%len(Match))

                    Match_key_list = list(Match.keys())# list裡面放 bettype

                    retry_count = 0
                    while True:
                        ran_index = random.randint(0, len(Match_key_list) -1  )
                        Ran_Match_id =   Match_key_list[ran_index]# 隨機取出 odds id
                        self.logger.info('Ran_Match_id: %s'%Ran_Match_id)
                    
                        BetTypeId = Match[Ran_Match_id]['BetTypeId']
                        if BetTypeId not in already_list:
                            self.logger.info('BetTypeId: %s 沒有投注過 ,成立'%BetTypeId)
                            break
                        self.logger.info('BetTypeId: %s 已經存在過注單裡 ,retry : %s'%(BetTypeId, retry_count ))
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
                    其他sport 拿到的 odds 需轉成 Dec Odds , Cricket 原本就是 dec odds所以不做轉換 
                    5: Ft 1x2 , 15: 1H 1x2(原本就是 dec odds, 不用轉) 
                    '''
                    if  self.gameid != 50:# cricket 的不用轉 
                        if BetTypeId not in [5, 15]:#  5: Ft 1x2 , 15: 1H 1x2 他們是 屬於Dec Odds
                            odds = self.Odds_Tran(odds)
                            self.logger.info('%s bettype: %s , 需轉乘 Dec odds: %s'%( self.sport,BetTypeId, odds) )

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
                        self.logger.error('data_format: %s'%e)

                    data_str = data_str + data_format + '&'
                    if index_key == len_Match_dic -1 :

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
                    
                    Odds_dict[Matchid] = odds 
                    BetTypeId_list.append(BetTypeId)
                
                self.logger.info('BetTypeId_list: %s'%BetTypeId_list)
                self.logger.info('OddsId :%s'%Odds_dict)
            except Exception as e:
                self.logger.error('DoplaceBet: %s'%e)
        
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
                    self.logger.error('data_format: %s'%e)

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
                BetTypeId_list.append(oddsid)
            self.logger.info('BetTypeId_list :%s'%BetTypeId_list)
        
        retry_count = 0
        while True:
            try:
                import re
                data_str = re.sub(r"\s+", "", data_str)# 移除空白,對 打接口沒影響 ,只是 data好看 

                self.headers['Cookie'] = 'ASP.NET_SessionId='+ self.login_session[user]

                post_data =  data_str
                r = self.session.post(self.url  + '/BetParlay/DoplaceBet',data = post_data.encode(),
                headers=self.headers)# data_str.encode() 遇到中文編碼問題 姊法
                repspone_json = r.json()
                Data = repspone_json['Data']
                response_code = str(Data['Code'])
                Message = Data['Message']
                if response_code == '45':# HDP/OU has been changed
                    self.logger.error('ErrorMsg: %s'%repspone_json['ErrorMsg'] ) 
                    self.logger.info('Message: %s'%Message)

                    #self.fail_bettype.append(BetTypeId_list[0])
                    return False
                
                elif response_code == '-91':# update odds
                    self.logger.info('Message: %s'%Message)
                    self.logger.info('休息 兩秒鐘 再做')
                    time.sleep(2)
                    return '重新'

                elif response_code == '15':# odds has changed
                    self.logger.info('Message: %s'%Message)
                    ItemList = Data['ItemList']
                    self.logger.info('ItemList: %s'%ItemList)# 一個list 裡面包 多個dict ,確認 每個 單 是否都有 odds changed
                    
                    
                    odds_change_dict = {}# 變更後的odds , key 為 matchid , value 為 odds
                    for dict_ in ItemList:
                        if str(dict_['Code']) == '15':# odds changed
                            Matchid = dict_['Key']
                            odds_change = dict_['Message'].split('to')[-1].strip('.').replace(' ','')# 切割完, 在移除最後一個 . 移除空白
                            self.logger.info('odds_change: %s'%odds_change)
                            odds_change_dict[Matchid] = odds_change    
                    self.logger.info('odds_change_dict: %s'%odds_change_dict)

                    for matchid in odds_change_dict.keys():# 把 變更後的odds 取出
                        og_odds = str(Odds_dict[matchid])# 把原本的 odds取出
                        odds_change = odds_change_dict[matchid]# 如果遇到 多個 相同的odds, 目前寫法可能有問題
                        data_str = data_str.replace( og_odds, odds_change)
                        Odds_dict[matchid] = odds_change # 從新變更dict
                    if retry_count == 1: 
                        return 'retry 完'
                    retry_count = retry_count + 1
                    time.sleep(5)# 系統 有防止 快速 打 接口 ,回復 We are updating odds, please try again later
                    
                elif response_code in ['0','1']:# 投注成功
                    self.Order_dict['Message'] = Message

                    TransId_Combo = Data['TransId_Combo']
                    TransId_System = Data['TransId_System']

                    TotalPerBet =  Data['TotalPerBet']
                    self.Order_dict['TotalPerBet'] = TotalPerBet
                    FinalBalance = Data['FinalBalance']
                    self.Order_dict['FinalBalance'] = FinalBalance
                    self.Order_dict['BetTypeId_list'] = BetTypeId_list
                    
                    Odds_list = list(Odds_dict.values() )
                    Match_list = list(Odds_dict.keys() )
                    if TransId_Combo in ['0','']:
                        self.Order_dict['注單ID'] = TransId_System

                    else:
                        self.Order_dict['注單ID'] = TransId_Combo

                    self.Order_dict['Match_list'] = Match_list
                    self.Order_dict['Odds_list'] = Odds_list
                    self.logger.info('Order_dict: %s'%self.Order_dict)
                    return True
                
                else:#例外 沒抓到的 code
                    self.logger.info('response_code : %s'%response_code)
                    self.logger.info('Message: %s'%Message)
                    return 'Bet Fail !'

                #self.logger.info('repspone_json: %s'%repspone_json)   

            except Exception as e:
                self.logger.info('mobile DoplaceBet Api Fali: %s'%e)
                return False




class Desktop_Api(Login):    
    def __init__(self,device="",user='',url= ''):
        super().__init__(device)
        self.login = None
        self.user = user
        self.url = url
        if self.login is None:
            self.desktop_login()
    
    def desktop_login(self):# PC端 login街口 邏輯
        '''加密邏輯 呼叫'''
        common_js = execjs.compile(self.js_from_file('./login_js/dsektop.js'))# 讀取 login js檔
        cfs_psswd = common_js.call("CFS", '1q2w3e4r')# password先做 前端 CFS 加密
        val = self.assert_validation()
        md5_psswd = self.md(password = cfs_psswd,val = val)# md5 將 Cfs加密 的密碼   跟 驗證碼 做md5
        login_data = "txtUserName={0}&txtPasswd={1}&txtValidCode={2}".format( self.user ,md5_psswd,val)
        
        if len(self.cookies) != 0:# aspx 的會為空 list
            asp_cookie = ''# 先初始 空字串, 後面 加起來
            for index,con_dict in enumerate(self.cookies): #self.cookies為 list 包 dict
                cookie_name = con_dict['name']
                cookie_value = con_dict['value']
                asp_cookie = asp_cookie + '%s=%s'%(cookie_name,cookie_value)
                #self.logger.info('asp_cookie: %s'%asp_cookie)
                if index == 0: 
                    asp_cookie = asp_cookie + ';'# 因為會要串兩個 cookie 字串,需要用 ; 來傳進去
            self.logger.info('asp_cookie: %s'%asp_cookie)
            self.headers['Cookie'] = asp_cookie
        
        
        self.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        self.headers['X-Requested-With'] =  'XMLHttpRequest'



        r = self.session.post(self.url  + '/DepositProcessLogin',data=login_data,headers=self.headers)
        try:
            repspone_json = r.json()
            self.logger.info('response: %s'%repspone_json)
            if repspone_json['ShowErrorMsg'] == 'The validation code has expired.':
                self.logger.info('登入 Fali')
                return False

            reponse_url = r.json()['url']# 取得登入後 轉導url
            self.logger.info('reponse_url: %s'%reponse_url)
        
            if 'qasb' in self.url:
                Val_url = '%s%s'%(self.url, reponse_url)
                self.logger.info('Val_url: %s'%Val_url)#/ValidateTicket?Guid=fa426c9c-739d-4b37-9589-db13ab0b1cdd
                r = self.session.get(Val_url,headers=self.headers )
                self.logger.info('r.url: %s'%r.url)
                u = urlparse(r.url)
                self.member_url = 'http://%s%s'%(u.netloc,u.path)
                self.member_url = self.member_url.split('/ValidateTicket')[0]
                self.logger.info('self.member_url: %s'%self.member_url)

                r = self.session.get(self.member_url +  '/NewIndex?lang=en&rt=0&webskintype=2',headers=self.headers )
                
            else:
                u = urlparse(reponse_url)# 擷取 動態 member_url 
                self.member_url = 'http://%s'%u.netloc
                self.logger.info('member_url: %s'% self.member_url)

                r = self.session.get(reponse_url,headers=self.headers )
            self.login = 'login ready'
            return True
        except:
            self.logger.info('登入 Fali')
            return False
    
    def balance(self):# /NewIndex/GetWalletBalance
        balance_info_data = 'TZone=8'
        self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
        post_url = self.member_url  + '/NewIndex/GetWalletBalance'
        self.logger.info('post_url: %s'%post_url)

        self.logger.info('header: %s'%self.headers)
        r = self.session.post( post_url,data=balance_info_data,headers=self.headers)
        try:
            repspone_json = r.json()
            self.logger.info('response: %s'%repspone_json)
            return True
        except:
            self.logger.info('desktop balance Api Fali')
            return False

'''
統一用 來呼叫 Pc或者 Mobile Login街口
'''
def login_api(device,user,url):
    '''devive 為Pc 才會去叫 webdriver ,要取驗證碼'''
    if device in ['mobile','app']:
        mobile_api = Mobile_Api(device='',user=user,url=url)# 初始 login為 None 一定先登入
        return  mobile_api
    else: #都是桌機
        desktop_api = Desktop_Api(device='Pc',user=user,url=url)
        return  desktop_api
