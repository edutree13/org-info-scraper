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
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    # 불필요한 시스템 이메일 제외
    return [e for e in set(emails) if not any(x in e for x in ['w3.org', 'reporter', 'news'])]

def search_and_extract(org_name, address):
    # 검색어 최적화: "기관명 이메일 @" (큰따옴표 포함 시 이메일이 포함된 결과 위주로 나옴)
    query = f"{org_name} \"@\" 이메일 연락처"
    url = f"https://openapi.naver.com{query}&display=10"
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            items = res.json().get('items', [])
            all_emails = []
            
            for item in items:
                # 1. 검색 결과의 '제목'과 '요약문(Description)'에서 바로 이메일 추출 (보안 차단 우회)
                snippet = item['title'] + " " + item['description']
                found = extract_emails(snippet)
                all_emails.extend(found)
                
            if all_emails:
                # 중복 제거 후 최대 2개 반환
                return {"이메일": ", ".join(list(set(all_emails))[:2]), "상태": "검색결과추출"}
            
        return {"이메일": "찾지못함", "상태": "데이터없음"}
    except Exception as e:
        return {"이메일": "오류", "상태": f"에러:{str(e)}"}

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
            print(f"[{index+1}/{len(df)}] {row['기관명']} 분석 중...")
            info = search_and_extract(row['기관명'], row.get('주소', ''))
            results.append({**row.to_dict(), **info})
            time.sleep(0.3) # API 속도 조절
            
        pd.DataFrame(results).to_csv('output.csv', index=False, encoding='utf-8-sig')
        print("수집 완료!")
