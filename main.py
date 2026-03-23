import os
import pandas as pd
import requests
import re
import time
from bs4 import BeautifulSoup

# API 설정 (Secrets 확인 필수)
NAVER_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_SECRET = os.getenv('NAVER_CLIENT_SECRET')
GOOGLE_KEY = os.getenv('GOOGLE_API_KEY') # 구글 API 추가 활용

def get_emails_from_url(url):
    """실제 웹페이지에 접속하여 이메일 패턴을 추출합니다."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            # 이메일 정규표현식 패턴
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res.text)
            # 불필요한 공통 이메일 제외
            filtered = [e for e in set(emails) if not any(x in e for x in ['reporter', 'news', 'w3.org'])]
            return ", ".join(filtered[:3]) # 최대 3개만 반환
    except:
        return ""
    return ""

def search_integrated(org_name, address):
    # 검색어 최적화: 기관명 + 주소(구/동) + 연락처
    addr_part = re.search(r'([가-힣]+구|[가-힣]+동)', str(address))
    query = f"{org_name} {addr_part.group(1) if addr_part else ''} 공식홈페이지 이메일"
    
    # 네이버 검색 실행
    url = f"https://openapi.naver.com{query}&display=10"
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            items = res.json().get('items', [])
            for item in items:
                link = item['link']
                # 신뢰도 낮은 사이트 필터링
                if any(x in link for x in ['blog.naver', 'kin.naver', 'youtube']): continue
                
                # 페이지 내부에서 이메일 직접 추출 시도
                found_email = get_emails_from_url(link)
                if found_email:
                    return {"이메일": found_email, "출처": link, "상태": "수집성공"}
                    
        return {"이메일": "찾지못함", "출처": "검색결과없음", "상태": "재검토필요"}
    except:
        return {"이메일": "오류", "출처": "통신에러", "상태": "실패"}

if __name__ == "__main__":
    # 인코딩 대응 파일 읽기
    for enc in ['utf-8-sig', 'cp949', 'utf-8']:
        try:
            df = pd.read_csv('input.csv', encoding=enc)
            break
        except: continue

    results = []
    # .head(5)를 제거하여 전체 리스트(63개 이상) 모두 수행
    for index, row in df.iterrows():
        print(f"[{index+1}/{len(df)}] {row['기관명']} 검색 중...")
        info = search_integrated(row['기관명'], row['주소'])
        results.append({**row.to_dict(), **info})
        time.sleep(0.5) # API 차단 방지용

    # 결과 저장 (엑셀에서 바로 보기 편하게 utf-8-sig 사용)
    pd.DataFrame(results).to_csv('output.csv', index=False, encoding='utf-8-sig')
    print("모든 작업이 완료되었습니다!")
