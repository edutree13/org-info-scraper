import os
import pandas as pd
import requests
import re
import time

# API 설정
NAVER_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_SECRET = os.getenv('NAVER_CLIENT_SECRET')

def extract_emails(text):
    """텍스트에서 이메일 패턴을 찾아냅니다."""
    # HTML 태그 제거 및 텍스트 정제
    clean_text = re.sub('<[^>]*>', ' ', text)
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, clean_text)
    # 시스템 이메일 및 무의미한 도메인 제외
    return [e for e in set(emails) if not any(x in e for x in ['w3.org', 'reporter', 'news', 'example'])]

def search_and_extract(org_name, address):
    # 검색어 고도화: 학교의 경우 "교직원" 키워드가 효과적입니다.
    query = f"{org_name} 교직원 연락처 \"@\""
    
    # [수정된 부분] 네이버 API 전체 주소 연결
    url = f"https://openapi.naver.com{query}&display=10"
    headers = {
        "X-Naver-Client-Id": NAVER_ID, 
        "X-Naver-Client-Secret": NAVER_SECRET
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            items = res.json().get('items', [])
            all_emails = []
            
            for item in items:
                # 제목과 요약문에서 이메일 추출
                snippet = item['title'] + " " + item['description']
                found = extract_emails(snippet)
                all_emails.extend(found)
                
            if all_emails:
                # 중복 제거 후 최대 2개 반환
                return {"이메일": ", ".join(list(set(all_emails))[:2]), "상태": "수집성공"}
            
        return {"이메일": "정보없음", "상태": f"결과없음(코드:{res.status_code})"}
    except Exception as e:
        return {"이메일": "통신오류", "상태": f"에러:{str(e)}"}

if __name__ == "__main__":
    # 파일 읽기
    df = None
    for enc in ['utf-8-sig', 'cp949', 'utf-8']:
        try:
            df = pd.read_csv('input.csv', encoding=enc)
            break
        except: continue

    if df is not None:
        results = []
        for index, row in df.iterrows():
            print(f"[{index+1}/{len(df)}] {row['기관명']} 수집 중...")
            info = search_and_extract(row['기관명'], row.get('주소', ''))
            results.append({**row.to_dict(), **info})
            time.sleep(0.4) # API 차단 방지
            
        pd.DataFrame(results).to_csv('output.csv', index=False, encoding='utf-8-sig')
        print("모든 작업 완료!")
