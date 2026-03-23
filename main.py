import os
import pandas as pd
import requests
import re
import time

# API 설정 (GitHub Secrets 확인)
NAVER_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_SECRET = os.getenv('NAVER_CLIENT_SECRET')

def extract_emails(text):
    """텍스트에서 이메일 패턴을 추출합니다."""
    clean_text = re.sub('<[^>]*>', ' ', text)
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, clean_text)
    return [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['w3.org', 'reporter', 'news', 'png', 'jpg'])]

def search_and_extract(org_name, address):
    # [수정] 오류를 유발하는 특수문자 제거 후 깔끔한 검색어 구성
    query = f"{org_name} 교직원 연락처 이메일"
    
    # [핵심 수정] URL을 직접 더하지 않고 params 방식을 사용하여 주소 깨짐 방지
    url = "https://openapi.naver.com"
    params = {
        "query": query,
        "display": 10
    }
    headers = {
        "X-Naver-Client-Id": NAVER_ID, 
        "X-Naver-Client-Secret": NAVER_SECRET
    }
    
    try:
        # params를 사용하여 API 호출 (가장 안전한 방식)
        res = requests.get(url, headers=headers, params=params, timeout=10)
        
        if res.status_code == 200:
            items = res.json().get('items', [])
            all_emails = []
            for item in items:
                content = item['title'] + " " + item['description']
                all_emails.extend(extract_emails(content))
                
            if all_emails:
                unique_emails = list(dict.fromkeys(all_emails))
                return {"이메일": ", ".join(unique_emails[:2]), "상태": "수집성공"}
            
            return {"이메일": "정보없음", "상태": "검색결과에데이터없음"}
        else:
            return {"이메일": "API응답오류", "상태": f"코드:{res.status_code}"}
    except Exception as e:
        return {"이메일": "통신에러", "상태": "주소형식확인필요"}

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
            time.sleep(0.4) # API 속도 제한 준수
            
        pd.DataFrame(results).to_csv('output.csv', index=False, encoding='utf-8-sig')
        print("🎉 모든 수집 작업이 완료되었습니다!")
