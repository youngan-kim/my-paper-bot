import requests
import datetime
import time
import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

# 1. 설정: 키워드 및 저널 리스트 (기존과 동일)
KEYWORDS = [
    "neighborhood and crime", "spatial crime pattern", "spatial analysis", "urban studies",
    "machine learning spatial analysis", "spatial econometrics", "geospatial machine learning",
    "spatial political science", "spatial economics"
]

TARGET_JOURNALS = [
    "Criminology", "Journal of Quantitative Criminology", "Justice Quarterly", 
    "Journal of Research in Crime and Delinquency", "British Journal of Criminology",
    "Annual Review of Criminology", "Journal of Criminal Justice",
    "Annals of the American Association of Geographers", "Geographical Analysis",
    "Applied Geography", "Professional Geographer", "Transactions in GIS",
    "Cities", "Urban Studies", "Journal of Urban Affairs",
    "American Sociological Review", "Annual Review of Sociology",
    "American Journal of Sociology", "Social Forces", "Health & Place",
    "Journal of Urban Economics", "Journal of Economic Geography", 
    "Journal of Applied Econometrics", "Econometrica", "Quarterly Journal of Economics",
    "American Political Science Review", "American Journal of Political Science", 
    "Journal of Politics", "Political Analysis", "Political Geography"
]

DB_FILE = "visited_papers.txt"

def load_visited_papers():
    """과거에 수집했던 논문의 제목들을 불러옵니다."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_visited_papers(new_titles):
    """새로 수집한 논문 제목을 기록 파일에 추가합니다."""
    with open(DB_FILE, "a", encoding="utf-8") as f:
        for title in new_titles:
            f.write(title + "\n")

def fetch_papers(keyword, offset=0, limit=100):
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={keyword}&limit={limit}&offset={offset}&sort=publicationDate:desc&fields=title,venue,year,authors,externalIds,abstract,publicationDate"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json().get('data', [])
        elif response.status_code == 429:
            time.sleep(10)
            return fetch_papers(keyword, offset, limit)
    except Exception as e:
        print(f"Error fetching {keyword}: {e}")
    return []

def upload_to_drive(filename):
    scope = ['https://www.googleapis.com/auth/drive']
    try:
        key_dict = json.loads(os.environ['GDRIVE_SERVICE_ACCOUNT'])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
        gauth = GoogleAuth()
        gauth.credentials = creds
        drive = GoogleDrive(gauth)
        folder_id = os.environ['GDRIVE_FOLDER_ID']
        file_drive = drive.CreateFile({'title': filename, 'parents': [{'id': folder_id}]})
        file_drive.SetContentFile(filename)
        file_drive.Upload()
        print(f"Successfully uploaded {filename} to Google Drive!")
    except Exception as e:
        print(f"Drive upload failed: {e}")

def main():
    visited_titles = load_visited_papers() # 과거 기록 로드
    all_candidate_papers = []
    seen_titles_this_run = set()

    for kw in KEYWORDS:
        # 중복 제외하고 20편을 채우기 위해 검색 범위를 약간 넓힘 (3페이지)
        for page in range(3): 
            papers = fetch_papers(kw, offset=page*100)
            if not papers:
                break
                
            for p in papers:
                title = p.get('title', '')
                venue = p.get('venue', '')
                if not venue or not title: continue
                
                # 1. 타겟 저널 필터링
                if any(journal.lower() in venue.lower() for journal in TARGET_JOURNALS):
                    # 2. 과거에 본 적 없고 + 이번 실행에서도 중복되지 않은 논문만
                    if title not in visited_titles and title not in seen_titles_this_run:
                        author_names = [author['name'] for author in p.get('authors', [])]
                        p['author_display'] = ", ".join(author_names) if author_names else "Unknown Authors"
                        p['pub_date'] = p.get('publicationDate') if p.get('publicationDate') else "1900-01-01"
                        
                        all_candidate_papers.append(p)
                        seen_titles_this_run.add(title)
            
            if len(all_candidate_papers) > 50:
                break

    # 최신순 정렬 후 상위 20편
    all_candidate_papers.sort(key=lambda x: x['pub_date'], reverse=True)
    final_papers = all_candidate_papers[:20]

    # 최종 선택된 20편의 제목만 추출하여 DB에 저장 준비
    final_titles = [p['title'] for p in final_papers]

    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"Daily_Research_{today}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Daily Research Update: {today}\n\n")
        f.write(f"**상태:** 신규 논문 20편 (과거 수집 데이터 제외 완료)\n\n")
        
        if not final_papers:
            f.write("> **알림:** 오늘은 새로운 논문이 없습니다.\n\n")
        else:
            for i, p in enumerate(final_papers, 1):
                doi = p.get('externalIds', {}).get('DOI', 'N/A')
                f.write(f"## {i}. {p['title']}\n")
                f.write(f"- **Authors:** {p['author_display']}\n")
                f.write(f"- **Journal:** {p.get('venue', 'Unknown')}\n")
                f.write(f"- **Date:** {p.get('pub_date', 'N/A')}\n")
                f.write(f"- **Abstract:** {p.get('abstract', 'No abstract available.')}\n\n---\n")

    if final_papers:
        save_visited_papers(final_titles) # DB 업데이트
        upload_to_drive(filename) # 드라이브 업로드

if __name__ == "__main__":
    main()
