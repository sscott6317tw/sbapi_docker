
import time
import Api_Object
from  Logger import create_logger 
import sys

class mobile_api_betting:
    def __init__(self,url,id,pw,central_account,central_password,market,sport,all_bet_choice=True,match_id='',all_odds_type=[]):
        self.url = url #測試用
        self.id = id
        self.pw = pw
        self.central_account = central_account
        self.central_password = central_password
        self.sport = sport
        self.market = market
        self.match_id = match_id #用於 Filter 要測試哪一個 Match ID
        self.all_bet_choice = all_bet_choice #'true' 下 all Bet choice，'false' 下 all Bet Type
        self.all_odds_type = all_odds_type
        self.log = create_logger(r"\AutoTest", 'mobile_api_betting')
        #用來存放 Pass Fail 注單資訊
        pass_txt = open('Config/pass.txt', 'w+') 
        fail_txt = open('Config/fail.txt', 'w+')
        pass_txt.write('')
        fail_txt.write('')
        pass_txt.close()
        fail_txt.close()

    def api_betting(self):
        odds_type_list = self.all_odds_type
        for odds_type in odds_type_list:
            pass_txt = open('Config/pass.txt', 'a+') 
            fail_txt = open('Config/fail.txt', 'a+')
            pass_txt.write('Test Odds Type : %s'%odds_type+'\n')
            fail_txt.write('Test Odds Type : %s'%odds_type+'\n')
            pass_txt.close()
            fail_txt.close()

            mobile_api = Api_Object.Login().login_api(device='app', user=self.id,password=self.pw, url=self.url,central_account=self.central_account,central_password=self.central_password)
            mobile_api.set_odds_type(odds_type=str(odds_type))
        
            already_list = []
            bet_type_list = ['OU','more']
            #bet_type_list = ['more']
            for bet_type in bet_type_list:
                print(self.match_id)
                showallodds_result = mobile_api.ShowAllOdds(type='test',market=str(self.market[0]).lower(),filter=self.match_id,sport=self.sport,bet_type=bet_type)
                if showallodds_result == True or showallodds_result == 'False':
                    pass
                else:
                    if bet_type == 'OU' :
                        if showallodds_result == "No Market":
                            self.log.info("無 %s Market，請確認後再重新輸入"%self.market)
                        elif showallodds_result == "No MatchID":
                            self.log.info("無 %s MatchID(League)，請確認後再重新輸入"%self.match_id)
                        else:
                            self.log.info("打 Show All Odds API 發生錯誤")
                        return False
                    else:
                        self.log.info("無 More Odds 可下注")
                    

                mobile_api.GetMarket()
                already_list = mobile_api.DoallbettypeBet(all_bet_choice=self.all_bet_choice,already_list=already_list)

        pass_txt = open('Config/pass.txt', 'r')  #把結果印在 Log 裡面方便確認
        fail_txt = open('Config/fail.txt', 'r')
        print(pass_txt.read())
        print(fail_txt.read())
        pass_txt.close()
        fail_txt.close()
        pass_count = len(open('Config/pass.txt', 'r').readlines())-len(odds_type_list)
        print("PASS Test Case : %s "%pass_count)
        fail_count = len(open('Config/fail.txt', 'r').readlines())-len(odds_type_list)
        print("FAIL Test Case : %s "%fail_count)
        


url = sys.argv[1]
id=sys.argv[2]
pw=sys.argv[3]
central_account = sys.argv[4]
central_password = sys.argv[5]
sport=sys.argv[6]
market=sys.argv[7]
match_id=sys.argv[8]
all_bet_choice=sys.argv[9]
all_odds_type=sys.argv[10]
all_odds_type = all_odds_type.split(',')

#mobile_api_betting_test = mobile_api_betting(url= 'http://smart.athena000.com/',id='autoqa01',pw='1q2w3e4r',central_account='web.desktop',central_password='1q2w3e4r',market='Early',sport="Soccer",all_bet_choice='true',match_id='49216814',all_odds_type=["Dec"])
#mobile_api_betting_test = mobile_api_betting(url= 'https://m.nova88.com/',id='wendy01',pw='111111',central_account='web.desktop',central_password='1q2w3e4r',market='Early',sport="Soccer",all_bet_choice='true',match_id='48940392',all_odds_type=["Dec"])
mobile_api_betting_test = mobile_api_betting(url= url,id=id,pw=pw,central_account=central_account,central_password=central_password,market=market,sport=sport,all_bet_choice=all_bet_choice,match_id=match_id,all_odds_type=all_odds_type)
mobile_api_betting_test.api_betting()
