#!/usr/bin/python3

import time
import logging
import random
import asyncio
from typing import Counter
from asyncio.tasks import as_completed

import aiohttp
from aiohttp.client import ClientSession
import tqdm
import tqdm.asyncio
import sys
import requests,json,pprint
from sseclient import SSEClient

DELAY =  1   # delay request send out time (millisecond)
TIMEOUT = 5             # timeout for every request (seconds)
URLS = [
    # Mobile
    #'http://ismart.11bet.com/whoami.aspx',
    #'https://l9j7mb.wsd666.com/whoami.aspx',
    #'https://sports.kotakaya.com/whoami.aspx',

    #'https://mkt.a0285.kzonlinegame.com/whoami.aspx?key=9527'

    # Desktop
    # 112 Group (API site)
    # 'https://hm.l0073.oriental-game.com/whoami.aspx?key=9527',
    # 'http://hm.l0093.owsb88.com/whoami.aspx?key=9527',
    # 'http://mkt.oriental-game.com/whoami.aspx?key=9527', # Before Asia
    # 'http://fbw.oriental-game.com/whoami.aspx?key=9527', # Before 2.0
    # 'http://sb.oriental-game.com/whoami.aspx?key=9527',  # After Asia
    'http://hm.oriental-game.com/whoami.aspx?key=9527',  # After 2.0

    # # 180 Gruop (Boping API site)
    # 'https://mkt.a0284.wabovip.com/whoami.aspx',
    # 'https://mkt.a0285.kzonlinegame.com/whoami.aspx?key=9527', # Kzing2 Asia
    # 'http://fbw.a0285.kzonlinegame.com/whoami.aspx?key=9527', # Kzing2 2.0
    # 'https://mkt.a0067.lnnzyy.com/whoami.aspx?key=9527', # Before Asia
    #'https://ismart.a0228.gamehby.com/whoami.aspx', # Before 2.0
     #'https://sb.a0067.lnnzyy.com/whoami.aspx?key=9527',  # After Asia
    #'http://www.fh968.com/login/index',  # After 2.0
    
    
    
    
   # 'https://www.dcard.tw/f', # ALog,

    # Athena
    #'https://hm.m4080.com/whoami.aspx?key=9527',
    #'https://b4i2to.fx9888.com/whoami.aspx?key=9527'
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/605.1.15 (KHTML, like Gecko)',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
]

# Create logger
logging.basicConfig(format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def timeit(func):
    async def wrapper(*args, **kwargs):
        t1 = time.time()
        ret = await func(*args, **kwargs)
        t2 = time.time()
        logger.info(f'function {func.__name__} execution time: {(t2-t1):.4f} s ')
        return ret
    return wrapper

async def get_client_ip():
    url = 'http://ipinfo.io/ip'
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=TIMEOUT) as resp:
            try:
                text = await resp.text()
                return text
            except:
                pass

async def get_server_ip(url):
    server_ip = None
    user_ran = random.randint(0,len(USER_AGENTS)-1)
    headers = {
        'User-Agent': USER_AGENTS[user_ran]
    }

    #await asyncio.sleep(random.randint(0, DELAY) / 1000)
    try:
        async with aiohttp.ClientSession() as session:
            t1 = time.time()
            async with session.get(url, timeout=TIMEOUT, headers=headers,ssl=False) as resp:
                text = await resp.text()
                t2 = time.time()
                logger.info(f'response time: {(t2-t1):.4f}s')
                #print(resp.text)
                try:
                    if text.startswith('SiteName'):
                        # Asia mkt, sb
                        server_ip = text.split('Server IP : ')[1].split('<br>')[0]
                    elif text.startswith('\r\n\r\n'):
                        # 2.0 hm, fbw
                        server_ip = text.split('Server IP:')[1].split(':')[0]
                    elif text.startswith('<!DOCTYPE'):
                        # Mobile
                        server_ip = text.split('ServerIP')[1].split('<td>')[1].split('</td>')[0]
                except (KeyError, IndexError):
                    logger.info(f'Parse Error on : {url}')
                    logger.debug(text)
                    return 'ParseError'
                return server_ip
    except asyncio.TimeoutError:
        logger.info(f'Request timeout ({TIMEOUT}s): {url}')
        return 'Timeout'
    except aiohttp.client_exceptions.ClientConnectorError as e:
        logger.info(f'Connect failed: {e}')
        return 'ConnectError'
    except aiohttp.client_exceptions.ServerDisconnectedError as e:
        logger.info('ServerDisconnected')
        return 'ServerDisconnectedError'


@timeit
async def main(thread_num, stop_times, url):


    client_ip = await get_client_ip()

    time_start = time.time() #開始計時
    time_end = time.time()
    #str_time= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time_start))
    total_req = 0
    result = []# 
    #for url in URLS:
        #print(url)
    while time_end - time_start <= stop_times:# 當程式執行超過指定時間 ,就break
        jobs = [get_server_ip(url) for _ in range(thread_num)]
        for job in tqdm.tqdm(asyncio.as_completed(jobs), total=len(jobs)):
            result.append( await job)

        #results = [ await job for job in tqdm.tqdm(asyncio.as_completed(jobs), total=len(jobs)) ]
        time_end  = time.time() #開始計時
        total_req = total_req + len(jobs)

    a = set(result)#重複濾掉,就不用每個都loop
    #print(ip_count)

    
    # Print results
    print('\n========== Results ==========')
    print(f'URL          : {url}')
    print(f'Client IP    : {client_ip}')
    print(f'Requests Sent: {total_req}')
    server_count = len(a)# 多少種不同ip
    for i in a:
        num = result.count(i)
        print('%s : %s'%(i,num))
    print(f'Total Servers: {server_count}\n')
    '''
    for key in ip_count.keys():
        if key == None:
            key = 'None'
        percentage = ip_count[key] / run_times * 100
        print(f'{key:15}: {ip_count[key]:5} ({percentage:.1f}%)')
    '''

async def sse_func(url,index):
    try:
        async with aiohttp.ClientSession() as session:
            headers = {'Accept': 'text/event-stream','sysid': str(index) }
            async with session.get(url,  headers=headers,ssl=False) as resp:
                return SSEClient(await resp.json())
    except Exception as e:
        print(e) 

    
@timeit
async def test_sse(url,stop_times,thread_num):

    #headers = {'Accept': 'text/event-stream'}
    #response = with_requests(url, headers)  # or with_requests(url, headers)

    time_start = time.time() #開始計時
    time_end = time.time()
    #str_time= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time_start))
    total_req = 0
    result = []# 
    #for url in URLS:
        #print(url)
    while time_end - time_start <= stop_times:# 當程式執行超過指定時間 ,就break
        total_req = total_req + 1
        jobs = [sse_func(url,total_req + _) for _ in range(thread_num)]
        for job in tqdm.tqdm(asyncio.as_completed(jobs), total=len(jobs)):
            result.append( await job)
        time_end  = time.time() #開始計時

    '''
    client = SSEClient(url)
    client_list = []

    for event in client:
        outputMsg = event.data
        if type(outputMsg) is not str:
            outputJS = json.loads(outputMsg)
            FilterName = "data"
            #print( FilterName, outputJS[FilterName] )
            print(outputJS[FilterName])
        
        pprint.pprint(event.json())
        client_list.append(event.json())
        pprint.pprint(event.data)
        pprint.pprint(json.loads(event.data))
    '''

if __name__ == '__main__':

    thread_num = 2
    stop_times = 1
    url = 'http://fbw.oriental-game.com/whoami.aspx?key=9527'

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(thread_num,stop_times, url) ) # loading balance
        
        
        #loop.run_until_complete(test_sse( url = url,thread_num = thread_num,stop_times= stop_times) ) # sse


    except KeyboardInterrupt:
        print('\nreceive SIGINT, program exit...')
        exit(0)
