
import time
import Api_Object
from  Logger import create_logger 
import sys

class mobile_api_betting:
    def __init__(self,url,id,pw,central_account,central_password,market,sport,all_bet_type=True,match_id='',all_odds_type=[]):
        self.url = url #測試用
        self.id = id
        self.pw = pw
        self.central_account = central_account
        self.central_password = central_password
        self.sport = sport
        self.market = market
        self.match_id = match_id #用於 Filter 要測試哪一個 Match ID
        self.all_bet_type = all_bet_type #True 下 all Bet Type，False 下 all Bet Choise
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

            mobile_api = Api_Object.Login().login_api(device='app', user=self.id, url=self.url,central_account=self.central_account,central_password=self.central_password)
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
                    else:
                        self.log.info("無 More Odds 可下注")
                    return False

                mobile_api.GetMarket()
                already_list = mobile_api.DoallbettypeBet(all_bet_type=self.all_bet_type,already_list=already_list)

        pass_txt = open('Config/pass.txt', 'r')  #把結果印在 Log 裡面方便確認
        fail_txt = open('Config/fail.txt', 'r')
        print("PASS Test Case : ")
        print(pass_txt.read())
        print("FAIL Test Case : ")
        print(fail_txt.read())
        


url = sys.argv[1]
id=sys.argv[2]
pw=sys.argv[3]
central_account = sys.argv[4]
central_password = sys.argv[5]
sport=sys.argv[6]
market=sys.argv[7]
match_id=sys.argv[8]
all_bet_type=sys.argv[9]
all_odds_type=sys.argv[10]
all_odds_type = all_odds_type.split(',')

#mobile_api_betting_test = mobile_api_betting(url= 'http://smart.athena000.com/',id='twqa10',pw='1q2w3e4r',central_account='web.desktop',central_password='1q2w3e4r',market='Early',sport="Soccer",all_bet_type=False,match_id='48948456',all_odds_type="MY")
mobile_api_betting_test = mobile_api_betting(url= url,id=id,pw=pw,central_account=central_account,central_password=central_password,market=market,sport=sport,all_bet_type=all_bet_type,match_id=match_id,all_odds_type=all_odds_type)
mobile_api_betting_test.api_betting()
