import requests
import datetime
import time
import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

# 1. 설정: 확장된 키워드 및 저널 리스트
KEYWORDS = [
    "neighborhood and crime", "spatial crime pattern", "spatial analysis", "urban studies",
    "machine learning spatial analysis", "spatial econometrics", "geospatial machine learning",
    "spatial political science", "spatial economics"
]

TARGET_JOURNALS = [
    # Criminology & Law
    "Criminology", "Journal of Quantitative Criminology", "Justice Quarterly", 
    "Journal of Research in Crime and Delinquency", "British Journal of Criminology",
    "Annual Review of Criminology", "Journal of Criminal Justice",
    # Geography & Urban Studies
    "Annals of the American Association of Geographers", "Geographical Analysis",
    "Applied Geography", "Professional Geographer", "Transactions in GIS",
    "Cities", "Urban Studies", "Journal of Urban Affairs",
    # Sociology
    "American Sociological Review", "Annual Review of Sociology",
    "American Journal of Sociology", "Social Forces", "Health & Place",
    # Economics (추가)
    "Journal of Urban Economics", "Journal of Economic Geography", 
    "Journal of Applied Econometrics", "Econometrica", "Quarterly Journal of Economics",
    # Political Science (추가)
    "American Political Science Review", "American Journal of Political Science", 
    "Journal of Politics", "Political Analysis", "Political Geography"
]

def fetch_papers(keyword, offset=0, limit=100):
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={keyword}&limit={limit}&offset={offset}&sort=publicationDate:desc&fields=title,venue,year,authors,externalIds,abstract,publicationDate"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json().get('data', [])
        elif response.status_code == 429:
            time.sleep(10) # API 제한 시 대기 시간 증가
            return fetch_papers(keyword, offset, limit)
    except Exception as e:
        print(f"Error fetching {keyword}: {e}")
    return []

def main():
    all_candidate_papers = []
    seen_titles = set()

    for kw in KEYWORDS:
        # 검색 깊이를 키워드당 2페이지(200개)로 설정하여 효율성 확보
        for page in range(2): 
            papers = fetch_papers(kw, offset=page*100)
            if not papers:
                break
                
            for p in papers:
                venue = p.get('venue', '')
                if not venue: continue
                
                # 타겟 저널 필터링 (대소문자 무시)
                if any(journal.lower() in venue.lower() for journal in TARGET_JOURNALS):
                    if p['title'] not in seen_titles:
                        # 저자 정보 처리
                        author_names = [author['name'] for author in p.get('authors', [])]
                        p['author_display'] = ", ".join(author_names) if author_names else "Unknown Authors"
                        p['pub_date'] = p.get('publicationDate') if p.get('publicationDate') else "1900-01-01"
                        
                        all_candidate_papers.append(p)
                        seen_titles.add(p['title'])
            
            if len(all_candidate_papers) > 100: # 충분한 후보군 확보 시 다음 키워드로
                break

    # 2. 전체 후보군을 최신 발행일 순으로 정렬
    all_candidate_papers.sort(key=lambda x: x['pub_date'], reverse=True)
    
    # 3. 상위 50편 선택
    final_papers = all_candidate_papers[:30]

    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"latest_papers.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Daily Research Update: {today}\n\n")
        f.write(f"**분야:** 범죄학, 지리학, 사회학, 경제학, 정치학 (Spatial & ML 특화)\n")
        f.write(f"**설정:** 타겟 저널 최신 논문 상위 20편\n\n")
        
        if not final_papers:
            f.write("> **알림:** 현재 조건에 맞는 최신 논문을 찾을 수 없습니다.\n\n")
        else:
            for i, p in enumerate(final_papers, 1):
                doi = p.get('externalIds', {}).get('DOI', 'N/A')
                pub_date = p.get('publicationDate', 'N/A')
                f.write(f"## {i}. {p['title']}\n")
                f.write(f"- **Authors:** {p['author_display']}\n")
                f.write(f"- **Journal:** {p.get('venue', 'Unknown')}\n")
                f.write(f"- **Date:** {pub_date}\n")
                f.write(f"- **DOI:** {doi}\n")
                f.write(f"- **Abstract:** {p.get('abstract', 'No abstract available.')}\n\n")
                f.write("---\n")

def upload_to_drive(filename):
    # GitHub Secrets에서 가져온 JSON으로 인증
    scope = ['https://www.googleapis.com/auth/drive']
    key_dict = json.loads(os.environ['GDRIVE_SERVICE_ACCOUNT'])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    
    gauth = GoogleAuth()
    gauth.credentials = creds
    drive = GoogleDrive(gauth)

    # 파일 업로드
    folder_id = os.environ['GDRIVE_FOLDER_ID']
    file_drive = drive.CreateFile({
        'title': filename,
        'parents': [{'id': folder_id}]
    })
    file_drive.SetContentFile(filename)
    file_drive.Upload()
    print(f"Uploaded {filename} to Google Drive!")

def main():
    # ... (기존 논문 수집 로직 동일) ...
    
    # 결과 Markdown 파일 생성
    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"Daily_Research_{today}.md"
    
    # (파일 저장 로직)
    with open(filename, "w", encoding="utf-8") as f:
        # ... (파일 내용 쓰기) ...
    
    # 구글 드라이브 업로드 실행
    try:
        upload_to_drive(filename)
    except Exception as e:
        print(f"Drive upload failed: {e}")

if __name__ == "__main__":
    main()
