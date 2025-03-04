from dataclasses import dataclass
import os
import requests
import json
import lxml.html
import re
import datetime

state = os.environ["STATE"]

qmsg = ''

qmsg_key = os.environ["QMSG_KEY"]

# schedule_tm = {'hour': os.environ["H"], 'min': os.environ["M"]}

signIn = {'username': os.environ["USERNAME"], 'password': os.environ["PASSWORD"]}

headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Mobile Safari/537.36',
    }

def run_script():
    conn = requests.Session()
    signInResponse= conn.post(
        url="https://app.upc.edu.cn/uc/wap/login/check",
        headers=headers,
        data= signIn, 
        timeout=10
    )

    historyResponse = conn.get(
        url="https://app.upc.edu.cn/ncov/wap/default/index?from=history",
        headers=headers,
        data={'from': 'history'},
        timeout=10
    )
    historyResponse.encoding = "UTF-8"

    html = lxml.html.fromstring(historyResponse.text)
    JS = html.xpath('/html/body/script[@type="text/javascript"]')
    JStr = JS[0].text
    default = re.search('var def = {.*};',JStr).group()
    oldInfo = re.search('oldInfo: {.*},',JStr).group()


    test_info_json_obj = json.loads(oldInfo.replace('oldInfo: ', '')[:-1])
    print('#1:', test_info_json_obj['address'])
    print('#2:', 'position:', test_info_json_obj['geo_api_info'])
    format_qmsg(test_info_json_obj['address'],'address')

    firstParam = re.search('sfzgsxsx: .,',JStr).group()
    firstParam = '"' + firstParam.replace(':','":')
    secondParam = re.search('sfzhbsxsx: .,',JStr).group()
    secondParam = '"' +  secondParam.replace(':','":')
    lastParam = re.search('szgjcs: \'(.*)\'',JStr).group()
    lastParam = lastParam.replace('szgjcs: \'','').rstrip('\'')

    newInfo = oldInfo
    newInfo = newInfo.replace('oldInfo: {','{' + firstParam + secondParam).rstrip(',')

    defaultStrip = default.replace('var def = ','').rstrip(';')
    defdic = json.loads(defaultStrip)

    dic = json.loads(newInfo)
    dic['ismoved'] = '0'
    for j in ["date","created","id","gwszdd","sfyqjzgc","jrsfqzys","jrsfqzfy"]:
        dic[j] = defdic[j]
    dic['szgjcs'] = lastParam

    newInfo = oldInfo
    newInfo = newInfo.replace('oldInfo: {','{' + firstParam + secondParam).rstrip(',')

    defaultStrip = default.replace('var def = ','').rstrip(';')
    defdic = json.loads(defaultStrip)

    dic = json.loads(newInfo)
    dic['ismoved'] = '0'
    for j in ["date","created","id","gwszdd","sfyqjzgc","jrsfqzys","jrsfqzfy"]:
        dic[j] = defdic[j]
    dic['szgjcs'] = lastParam

    # Send
    saveResponse = conn.post(
        url="https://app.upc.edu.cn/ncov/wap/default/save",
        headers=headers,
        data = dic,
        timeout=10
    )

    saveJson = json.loads(saveResponse.text)
    print(saveJson['m'])
    format_qmsg(saveJson['m'], 'RES')

list_blocked_word = ["中国", "公寓"]

def format_qmsg(new_msg, pre=None):
    global qmsg
    for w in list_blocked_word:
        new_msg = new_msg.replace(w, '*')
    if pre:
        new_msg = '*'*12 + '\n' + pre + '\n    ' + new_msg
    qmsg+=new_msg

def handle_schedule():
    dt0 = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    dt8 = dt0.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
    if(dt8.hour == schedule_tm.hour and dt8.minute == schedule_tm.min):
        return True
    return False

if state == "EN":
    print('Script start')
    run_script()
elif state == "DEN":
    print('Script disabled')
    format_qmsg('Script disabled', 'RES')
else:
    print('STATE ERRO')
    format_qmsg('STATE ERRO[' + state + ']', 'ERRO')

print(qmsg)

if qmsg_key:
    requests.get('https://qmsg.zendee.cn/send/' + qmsg_key, {'msg': qmsg})
