import os
import pandas as pd
import requests
import re
import time

# API 설정 (GitHub Secrets에 등록된 이름과 동일해야 합니다)
NAVER_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_SECRET = os.getenv('NAVER_CLIENT_SECRET')

def extract_emails(text):
    """텍스트에서 이메일 주소 패턴을 찾아냅니다."""
    # HTML 태그 제거
    clean_text = re.sub('<[^>]*>', ' ', text)
    # 이메일 정규표현식
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, clean_text)
    # 시스템 이메일 및 이미지 파일명 제외
    return [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['w3.org', 'reporter', 'news', 'png', 'jpg'])]

def search_and_extract(org_name, address):
    # 검색어 구성: 기관명 + 이메일 (가장 표준적인 검색어)
    query = f"{org_name} 이메일 연락처"
    
    # [중요] 주소 조립 방식을 params로 고정하여 URL 깨짐을 원천 차단합니다.
    api_url = "https://openapi.naver.com"
    api_params = {
        "query": query,
        "display": 10
    }
    api_headers = {
        "X-Naver-Client-Id": NAVER_ID, 
        "X-Naver-Client-Secret": NAVER_SECRET
    }

    try:
        # 주소(api_url)와 파라미터(api_params)를 안전하게 결합하여 호출합니다.
        res = requests.get(api_url, headers=api_headers, params=api_params, timeout=10)
        
        if res.status_code == 200:
            items = res.json().get('items', [])
            all_emails = []
            
            for item in items:
                # 제목과 요약문에서 이메일 추출
                content = item['title'] + " " + item['description']
                all_emails.extend(extract_emails(content))

            if all_emails:
                # 중복 제거 후 최대 2개 반환
                unique_emails = list(dict.fromkeys(all_emails))
                return {"이메일": ", ".join(unique_emails[:2]), "상태": "수집성공"}

            return {"이메일": "정보없음", "상태": "검색결과에데이터없음"}
        else:
            return {"이메일": "API오류", "상태": f"응답코드:{res.status_code}"}
            
    except Exception as e:
        # 통신 에러 발생 시 로그를 남깁니다.
        return {"이메일": "통신에러", "상태": "네트워크확인필요"}

if __name__ == "__main__":
    # 인코딩(한글깨짐) 대응 파일 읽기
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
            # 기존 원본 데이터에 수집된 정보를 합칩니다.
            results.append({**row.to_dict(), **info})
            time.sleep(0.4) # API 속도 제한 준수

        # 결과 저장 (엑셀에서 바로 보기 편하도록 utf-8-sig 사용)
        pd.DataFrame(results).to_csv('output.csv', index=False, encoding='utf-8-sig')
        print("🎉 모든 수집 작업이 완료되었습니다!")
    else:
        print("파일을 읽을 수 없습니다. input.csv 파일명을 확인해주세요.")
