#In[]
import Api_Object


url = 'http://smart.athena000.com/'   #'http://mkt.11bet.com/onelogin.aspx'
device = 'app'

#In[]
user = 'twqa10'
mobile_api = Api_Object.Login().login_api(device=device, user=user, url=url,central_account='web.desktop',central_password='1q2w3e4r')
mobile_api.set_odds_type(odds_type='Dec')

#In[]
#mobile_api.ShowAllOdds(type='test',market='e',filter='48418819',sport='Soccer',bet_type='OU')
mobile_api.ShowAllOdds(type='test',market='e',filter='48418819',sport='Soccer',bet_type='more')
mobile_api.GetMarket()


#In[]
mobile_api.DoplaceBet()

# %%
