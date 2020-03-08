import urllib.request
import json

import datetime
import pytz

def get_weather_data():
    api_date, api_time = get_api_date()
    #http://apis.data.go.kr/1360000/VilageFcstInfoService/getVilageFcst?serviceKey=~~&pageNo=1&numOfRows=10&dataType=XML&base_date=20200210&base_time=0500&nx=62&ny=120
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService/getVilageFcst"
    key = "?serviceKey=kr%2FQXx6vPof0PDy8c%2BYL6vB2U7M7rv%2ByDaBzN%2FJ1orHghEJnhIds2hOmt59WFhziYr0vvgFzsKAg1UlTpPLuQw%3D%3D"
    pageNo = "&pageNo=1"
    numOfRows = "&numOfRows=10"
    dataType = "&dataType=JSON"
    date="&base_date=" + api_date #실제 날짜가 아닌, 크롤링을 위한 날짜
    time="&base_time=" + api_time # 마찬가지.
    nx = "&nx=62"
    ny = "&ny=120"
    
    api_url= url+key+pageNo+numOfRows+dataType+date+time+nx+ny

    data = urllib.request.urlopen(api_url).read().decode('utf8')
    data_json = json.loads(data)
    #print(data_json)

    parsed_json = data_json['response']['body']['items']['item']

    target_date = parsed_json[0]['fcstDate'] #문서상 날짜
    target_time = parsed_json[0]['fcstTime'] #문서상 시각

    date_calibrate = target_date
    if target_time >'1300':
        date_calibrate = str(int(target_date) + 1) #문서상 시각이 13시를 넘을 때, 아침 날씨를 다음날로 받기 위한 코드
    passing_data = {}
    for one_parsed in parsed_json:
        if one_parsed['fcstDate'] == target_date and one_parsed['fcstTime'] == target_time:
            passing_data[one_parsed['category']] = one_parsed['fcstValue']
        if one_parsed['fcstDate'] == date_calibrate and (one_parsed['category'] == 'TMX' or one_parsed['category'] == 'TMN'):
            passing_data[one_parsed['category']] = one_parsed['fcstValue']
    return passing_data

def get_api_date():
    standard_time = [2,5,8,11,14,17,20,23]
    time_now = datetime.datetime.now(tz=pytz.timezone('Asia/Seoul')).strftime('%H')
    check_time = int(time_now) -1
    day_calibrate=0

    while not check_time in standard_time:
        check_time -= 1
        if check_time <2:
            day_calibrate = 1
            check_time = 23
    date_now = datetime.datetime.now(tz=pytz.timezone('Asia/Seoul')).strftime('%Y%m%d')
    check_date = int(date_now) - day_calibrate

    return (str(check_date), (str(check_time)+'00'))

print(get_weather_data())