import os
import pandas as pd
import requests
import re
import time

# API 키 가져오기 (Secrets 설정 확인 필수)
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')

def search_info(org_name, address):
    # 주소에서 '구', '동'만 추출하여 검색 정확도 향상
    addr_match = re.search(r'([가-힣]+구|[가-힣]+동|[가-힣]+로)', str(address))
    short_addr = addr_match.group(1) if addr_match else ""
    
    query = f"{org_name} {short_addr} 이메일 연락처"
    url = f"https://openapi.naver.com{query}&display=5"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            items = res.json().get('items', [])
            for item in items:
                link = item['link'].lower()
                # 필터링: 뉴스 기사나 광고 사이트 제외
                if any(x in link for x in ['news', 'reporter', 'press', 'blog.naver']): continue
                
                # 결과 반환 (추후 고도화 가능)
                return {"이메일_추출_URL": item['link'], "상태": "수집시도"}
        return {"이메일_추출_URL": "결과없음", "상태": f"에러:{res.status_code}"}
    except:
        return {"이메일_추출_URL": "통신오류", "상태": "실패"}

if __name__ == "__main__":
    # 인코딩 문제를 해결하기 위해 여러 방식을 시도하며 파일 읽기
    df = None
    for enc in ['utf-8', 'cp949', 'euc-kr']:
        try:
            df = pd.read_csv('input.csv', encoding=enc)
            print(f"{enc} 인코딩으로 파일을 읽었습니다.")
            break
        except:
            continue

    if df is not None:
        results = []
        # 무료 한도를 아끼기 위해 처음엔 5개만 테스트
        for index, row in df.head(5).iterrows():
            print(f"{row['기관명']} 수집 중...")
            info = search_info(row['기관명'], row['주소'])
            results.append({**row.to_dict(), **info})
            time.sleep(0.5) # 차단 방지를 위한 짧은 휴식
            
        pd.DataFrame(results).to_csv('output.csv', index=False, encoding='utf-8-sig')
        print("정상 종료: output.csv를 확인하세요.")
    else:
        print("파일을 읽을 수 없습니다. 인코딩을 확인하세요.")
