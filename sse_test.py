#In[]
import sys
import time
import requests,json,pprint
from sseclient import SSEClient
from datetime import datetime
from  Logger import create_logger
from collections import defaultdict

test_dict = {}

log = create_logger(r"\AutoTest", 'test') 
done_index = 0

def test_sse(url, index  ):
    global done_index
    msg_dict  = defaultdict(list)
    def with_urllib3(url, headers):
        """Get a streaming response for the given event feed using urllib3."""
        import urllib3
        http = urllib3.PoolManager()
        return http.request('GET', url, preload_content=False, headers=headers)

    def with_requests(url, headers):
        """Get a streaming response for the given event feed using requests."""
        return requests.get(url, stream=True, headers=headers)

    def with_session(url, headers):
        """Get a streaming response for the given event feed using requests."""
        session = requests.Session()
        return session.get(url,headers=headers)
    
    #now = datetime.now().strftime('%Y-%m-%d/%H:%M:%S')
    headers = {'Accept': 'text/event-stream','sysid': str(index) }
    #response = with_requests(url, headers)  # or with_requests(url, headers)
    client = SSEClient(url, headers=headers)
    #client = SSEClient(response)
    try:
        #client = SSEClient(response.json())
        for event in client:
            if not event.data:
                continue

            outputMsg = json.loads(event.data)
            #print(outputMsg)
            res_index = outputMsg['Index']
            res_mess = outputMsg['Message']
            ress_code = outputMsg['ResultCode']

            #log.info(outputMsg)
            test_dict[index] = msg_dict
            if res_index >= 100:# 各message推波到 index 10 就停
                done_index = done_index + 1
                #log.info('res_mess: %s done  '%res_mess)
                return 'done'
            if ress_code != 0:
                log.error('res_mess: %s  ResultCode 不為0'%res_mess)
                return 'Fail'
            #print (response_index)
    except Exception as e:
        log.error(e)
        


#test_sse(url = 'http://qasb4.athena000.com:50052/api/LiveTips/GetMessage',index= 1)



#return_res_num()
#In[]

import threading
def sse_thread(url ,stop_times, num_times):
    #global msg_list
    num = 0
    response_list = []# 用來 最後 Join　response
    time_start = time.time() #開始計時
    time_end = time.time()
    str_time= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time_start))
    print('start: %s'%str_time)
    #self.time_end   會 再while 迴圈一值變動
    while time_end - time_start <= stop_times:# 當程式執行超過指定時間 ,就break
        threads = []
        for i in range(num_times):
            num = num + 1
            t  = threading.Thread(target= test_sse , args=(url ,num  ))
            #print (self.headers)
            threads.append(t)
            response_list.append(t)
        for i in threads:
            i.start()
        if num >= 500:
            break
        time_end  = time.time() #開始計時
    print('time cost', time_end -time_start,'s')
    log.info('達到 sse 數量 :%s'%num)


    for i in response_list:
        i.join()
    log.info('done_index: %s done  '%done_index)
    
    #print(test_dict)
    #log.info('總index數量 : %s'%len(msg_list))

sse_thread(url = 'http://qasb4.athena000.com:50052/api/LiveTips/GetMessage' ,stop_times = 1, num_times = 1 )
