import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# 깃허브 Secrets에서 API 키 가져오기
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')

def clean_address(addr):
    # 주소에서 우편번호 및 불필요한 텍스트 제거 (정규표현식)
    return re.sub(r'\d{5}|[\(\[].*?[\)\]]', '', str(addr)).strip()

def search_info(org_name, address):
    refined_addr = clean_address(address)
    query = f"{org_name} {refined_addr} 이메일 연락처"
    
    # 1. 네이버 검색 API 우선 사용 (무료 한도가 넉넉함)
    url = f"https://openapi.naver.com{query}&display=5"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        items = res.json().get('items', [])
        for item in items:
            link = item['link']
            # 블랙리스트 필터링 (뉴스기사 등 제외)
            if any(x in link for x in ['lawtimes', 'news', 'reporter']): continue
            
            # 여기서 실제 페이지 접속 후 이메일 추출 로직이 들어갑니다 (생략된 핵심 로직)
            # 수집된 정보와 입력된 주소를 비교하여 '신뢰도' 계산 후 반환
            return {"email": "수집중...", "status": "확인필요", "url": link}
    
    return {"email": "찾지못함", "status": "실패", "url": ""}

# 메인 실행부
if __name__ == "__main__":
    df = pd.read_csv('input.csv')
    results = []
    
    # 무료 한도를 고려하여 샘플 5개만 먼저 테스트 권장
    for index, row in df.head(5).iterrows():
        info = search_info(row['기관명'], row['주소'])
        results.append({**row, **info})
    
    output_df = pd.DataFrame(results)
    output_df.to_csv('output.csv', index=False)
    print("수집 완료! output.csv 확인 요망")
