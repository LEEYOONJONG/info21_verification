import re
import csv
from django.shortcuts import render
# 여기 밑은 새롭게 작성한 부분
from django.http import HttpResponse
from django.shortcuts import render_to_response

# 이하는 크롤링을 위한 헤더부분
from selenium import webdriver
from urllib.request import urlopen
from bs4 import BeautifulSoup
import ssl
import time

# 이하는 오류팝업처리를 위한 부분
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
# 로딩에 따른 크롤링 지연 방지 부분
from selenium.webdriver.common.by import By

# 크롬창 숨기기 위한 부분
"""
chrome_option = webdriver.ChromeOptions()
chrome_option.add_argument('headless')
chrome_option.add_argument('--disable-gpu')
chrome_option.add_argument('lang=ko_KR')
"""

# 날씨 API 이용위한 부분
import urllib.request
import json
import datetime
import pytz


def get_weather_data():
    api_date, api_time = get_api_date()
    # http://apis.data.go.kr/1360000/VilageFcstInfoService/getVilageFcst?serviceKey=~~&pageNo=1&numOfRows=10&dataType=XML&base_date=20200210&base_time=0500&nx=62&ny=120
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService/getVilageFcst"
    key = "?serviceKey=kr%2FQXx6vPof0PDy8c%2BYL6vB2U7M7rv%2ByDaBzN%2FJ1orHghEJnhIds2hOmt59WFhziYr0vvgFzsKAg1UlTpPLuQw%3D%3D"
    pageNo = "&pageNo=1"
    numOfRows = "&numOfRows=10"
    dataType = "&dataType=JSON"
    date = "&base_date=" + api_date  # 실제 날짜가 아닌, 크롤링을 위한 날짜
    time = "&base_time=" + api_time  # 마찬가지.
    nx = "&nx=62"
    ny = "&ny=120"

    api_url = url+key+pageNo+numOfRows+dataType+date+time+nx+ny

    data = urllib.request.urlopen(api_url).read().decode('utf8')
    data_json = json.loads(data)
    # print(data_json)

    parsed_json = data_json['response']['body']['items']['item']

    target_date = parsed_json[0]['fcstDate']  # 문서상 날짜
    target_time = parsed_json[0]['fcstTime']  # 문서상 시각

    date_calibrate = target_date
    if target_time > '1300':
        # 문서상 시각이 13시를 넘을 때, 아침 날씨를 다음날로 받기 위한 코드
        date_calibrate = str(int(target_date) + 1)
    passing_data = {}
    for one_parsed in parsed_json:
        if one_parsed['fcstDate'] == target_date and one_parsed['fcstTime'] == target_time:
            passing_data[one_parsed['category']] = one_parsed['fcstValue']
        if one_parsed['fcstDate'] == date_calibrate and (one_parsed['category'] == 'TMX' or one_parsed['category'] == 'TMN'):
            passing_data[one_parsed['category']] = one_parsed['fcstValue']
    return passing_data


def get_api_date():
    standard_time = [2, 5, 8, 11, 14, 17, 20, 23]
    time_now = datetime.datetime.now(
        tz=pytz.timezone('Asia/Seoul')).strftime('%H')
    check_time = int(time_now) - 1
    day_calibrate = 0

    while not check_time in standard_time:
        check_time -= 1
        if check_time < 2:
            day_calibrate = 1
            check_time = 23
    date_now = datetime.datetime.now(
        tz=pytz.timezone('Asia/Seoul')).strftime('%Y%m%d')
    check_date = int(date_now) - day_calibrate

    return (str(check_date), (str(check_time)+'00'))

# 날씨 API 이용위한 부분 끝


# csv파일 저장 위한 부분


def toCSV(info_list):
    # 사람이 겹치면 안되므로 파일을 미리 읽어 중복여부 확인.
    
    file = open('info21_list.csv', 'r')
    csvfile = csv.reader(file)
    lines=[]
    #학번이 같다면 덮어써야 하므로 작업필요, 학번 같지 않다면 새 인원 추가만 하면 됨
    #학번이 같을 경우를 대비해 일단 기반작업. 새로운 csv 파일 작성하는 작업.
    isoverlapped = False
    for line in csvfile:
        if line[1] == info_list[1]: #새로운 데이터의 학번과 기존 학번이 같다면,
            lines.append(info_list) #새로운 데이터로 추가 ~= 대체.
            isoverlapped = True
        else:
            lines.append(line)      #새로운 데이터의 학번과 기존 학번이 같지 않다면, 기존 데이터 그대로 작성.
    if isoverlapped == False:         #새로운 데이터가 기존 데이터와 중복된적 없다면, 완전히 새로운 데이터 추가.
        lines.append(info_list)
    file.close()
    
    
    file_replace = open('info21_list.csv', 'w', encoding='utf-8', newline='')
    csvfile = csv.writer(file_replace)
    for line in lines:
        csvfile.writerow(line)
    file_replace.close()

def scoreCalc(info_list):
    arrSize = len(info_list[3])
    print(info_list[0] + "님은")
    for i in range(0, arrSize): #대상의 특정 학기 (ex 2017/1학기) 에 대해서,
        ppcount = 1
        goodcount = 0
        file = open('info21_list.csv', 'r')
        csvfile = csv.reader(file)
        for line in csvfile:
            line_major = line[2].replace('\xa0', ' ') # 과 중간에 \xa0 나와서 없애기 위한 부분.
            info_list_major = info_list[2].replace('\xa0', ' ')
            if line[1] == info_list[1]: #리스트 대상이 내가 아니여야
                continue
            elif line_major != info_list_major: # 리스트 대상과 학과가 같아야
                continue
            else: 
                from ast import literal_eval
                line[3] = literal_eval(line[3]) ########### 필수 !!! ########
                from ast import literal_eval
                line[4] = literal_eval(line[4]) ########### 필수 !!! ########
                objSemesterSize = len(line[3])
                for j in range(0, objSemesterSize):
                    if info_list[3][i] == line[3][j]: #대상의 특정학기와 리스트대상의 특정학기가 같다면,
                        ppcount = ppcount + 1   #인원 카운트
                        if info_list[4][i] >= line[4][j]: #새로운 대상의 성적이 더 좋거나 같다면
                            goodcount = goodcount + 1
        print(info_list[3][i] + "에 대상 " + str(ppcount) + "명 중에 " + str(ppcount-goodcount) + "등입니다.")
        file.close()





def post_list(request):
    # 여기가 핵심인 듯. 메인페이지
    return render(request, 'blog/post_list.html', {})


def search(request):

    #   OPEN API
    data_openapi = get_weather_data()
    weather = data_openapi['T3H']
    #

    errors = []
    if 'infoId' in request.GET:
        if 'infoPw' in request.GET:
            id = request.GET['infoId']
            pw = request.GET['infoPw']

            if id == '':
                errors.append('아이디를 입력해주세요.')
                return render_to_response('blog/post_list.html', {'errors': errors})
            else:
                if id != '' and pw != '':
                    #context = ssl._create_unverified_context()
                    driver = webdriver.Chrome(
                        '/Users/leeyoonjong/Downloads/chromedriver')
                    # 위에    , chrome_options=chrome_option   필요함
                    driver.implicitly_wait(10)

                    driver.get(
                        'https://info21.khu.ac.kr/com/LoginCtr/login.do')
                    # 대체휴무 팝업이 있다면
                    if driver.find_element_by_css_selector('body > div:nth-child(10) > div.ui-dialog-titlebar.ui-corner-all.ui-widget-header.ui-helper-clearfix.ui-draggable-handle > button'):
                        driver.find_element_by_css_selector(
                            'body > div:nth-child(10) > div.ui-dialog-titlebar.ui-corner-all.ui-widget-header.ui-helper-clearfix.ui-draggable-handle > button').click()
                    driver.find_element_by_name('userId').send_keys(id)
                    driver.find_element_by_name('userPw').send_keys(pw)
                    driver.find_element_by_xpath(
                        '//*[@id="loginFrm"]/div/div[2]/div[1]/div[2]/button').click()

                    # time.sleep(18)

                    # 오류 체크
                    try:
                        element = WebDriverWait(driver, 2).until(
                            EC.alert_is_present(), 'Timed out waiting'+'blahblah')
                        alert = driver.switch_to.alert
                        alert.accept()
                        errors.append('아이디 또는(그리고) 비밀번호가 틀렸습니다.')
                        return render_to_response('blog/post_list.html', {'errors': errors})
                    except TimeoutException:
                        print("no  alert")

                    # 로딩 시간 지연에 따른 크롤링 오류 방지 위한 부분
                    try:
                        element = WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, ".user_text01"))
                        )
                    except TimeoutException:
                        print("this page didn't open in 20 seconds!")
                        errors.append('서버에서 20초 동안 응답을 받을 수 없습니다.')
                        errors.append(
                            '인터넷 연결상태를 확인하거나 서버 안정화 이후 다시 시도해주시기 바랍니다.')
                        return render_to_response('blog/post_list.html', {'errors': errors})

                    req = driver.page_source
                    soup = BeautifulSoup(req, 'html.parser')

                    name = soup.select(
                        '#baseForm > section > div.main_w > div > div.main_user_w > div > div > div > div > div.user_box01 > p.user_text01')
                    hakbun = soup.select(
                        '#baseForm > section > div.main_w > div > div.main_user_w > div > div > div > div > div.user_box01 > p.user_text02')
                    major = soup.select(
                        '#baseForm > section > div.main_w > div > div.main_user_w > div > div > div > div > div.user_box01 > p.user_text03')
                    
                    # 성적 받기 위한
                    driver.get(
                        'https://portal.khu.ac.kr/haksa/clss/scre/allScre/index.do')

                    req = driver.page_source
                    soup = BeautifulSoup(req, 'html.parser')

                    semesters = []
                    semesters_soup = soup.select(
                        'tr > td.first > a'
                    )
                    for semester_soup in semesters_soup:
                        semesters.append(semester_soup.text)

                    # 밑은 성적처리 for문으로 하기 위한 부분.
                    scores = []
                    scores_soup = soup.select(
                        'tr > td:nth-child(6)'
                    )
                    # scores 성적 저장 위한 부분
                    for score_soup in scores_soup:
                        # print(score_soup.text) #soup
                        scores.append(float(score_soup.text))  # text array
                    scores = scores[1:]
                    # 학번(학적)에서 숫자만 뽑기
                    hakbun = hakbun[0].text
                    hakbun_trans = int(re.findall('\d+', hakbun)[0])
                    hakbun_trans = str(hakbun_trans)
                    # csv파일로 보내기 위한 부분.
                    #info21_li = [name[0].text, hakbun_trans, major[0].text.strip(), semesters, scores]
                    info21_li = ["권은비", "2017205043", "소프트웨어융합대학 소프트웨어융합학과", [' 2017/1학기',' 2017/2학기', ' 2018/1학기', ' 2018/2학기'],[3.5, 1.4, 2.7, 3.7]]
                    # 미리 csv파일 생성해 놓아야 csv파일 못찾았다는 에러 안뜸.
                    file_add = open('info21_list.csv', 'a',
                                    encoding='utf-8', newline='')
                    file_add.close()
                    # csv파일에 사람 추가하기(새로운 사람일 경우에만)
                    toCSV(info21_li)
        
                    scoreCalc(info21_li)

                    return render_to_response('blog/search_results.html', {'name': name[0].text, 'hakbun': hakbun_trans, 'major': major[0].text.strip(), 'semesters': semesters,'scores': scores, 'weather': weather})
                else:
                    errors.append('비밀번호를 입력해주세요.')
                    return render_to_response('blog/post_list.html', {'errors': errors})
    else:
        return render_to_response('blog/post_list.html', {'errors': False})