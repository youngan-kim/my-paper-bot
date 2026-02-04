import requests
import datetime
import time
import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

# 1. 설정: 키워드 및 확장된 저널 리스트
KEYWORDS = [
    "neighborhood and crime", "spatial crime pattern", "spatial analysis", "urban studies",
    "machine learning spatial analysis", "spatial econometrics", "geospatial machine learning",
    "spatial political science", "spatial economics", "place", "space", "neighborhood" 
]

TARGET_JOURNALS = [
    "Criminology", "Journal of Quantitative Criminology", "Justice Quarterly", 
    "Journal of Research in Crime and Delinquency", "British Journal of Criminology",
    "The British Journal of Criminology", "Annual Review of Criminology", "Journal of Criminal Justice",
    "Crime and Delinquency", "American Journal of Criminal Justice", "Journal of Crime and Justice",
    "Race and Justice", "Annals of the American Association of Geographers", "Geographical Analysis",
    "Applied Geography", "Professional Geographer", "Transactions in GIS",
    "Cities", "Urban Studies", "Journal of Urban Affairs",
    "American Sociological Review", "Annual Review of Sociology",
    "American Journal of Sociology", "Social Forces", "Health & Place",
    "Social Science & Medicine", "Sociological Methodology",
    "Journal of Urban Economics", "Journal of Economic Geography", 
    "Journal of Applied Econometrics", "Econometrica", "Quarterly Journal of Economics",
    "American Political Science Review", "American Journal of Political Science", 
    "Journal of Politics", "Political Analysis", "Political Geography",
    "Science", "Nature"
]

DB_FILE = "visited_papers.txt"
FIXED_FILENAME = "latest_research_report.md"

def load_visited_papers():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_visited_papers(new_titles):
    with open(DB_FILE, "a", encoding="utf-8") as f:
        for title in new_titles:
            f.write(title + "\n")

def fetch_papers(keyword, offset=0):
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={keyword}&limit=100&offset={offset}&sort=publicationDate:desc&fields=title,venue,year,authors,externalIds,abstract,publicationDate"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            return response.json().get('data', [])
        elif response.status_code == 429:
            time.sleep(15)
            return fetch_papers(keyword, offset)
    except Exception as e:
        print(f"Error fetching {keyword}: {e}")
    return []

def upload_or_update_drive(filename):
    scope = ['https://www.googleapis.com/auth/drive']
    key_dict = json.loads(os.environ['GDRIVE_SERVICE_ACCOUNT'])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    gauth = GoogleAuth()
    gauth.credentials = creds
    drive = GoogleDrive(gauth)
    folder_id = os.environ['GDRIVE_FOLDER_ID']

    # 폴더 내 동일한 이름의 파일 찾기
    file_list = drive.ListFile({'q': f"'{folder_id}' in parents and title='{filename}' and trashed=false"}).GetList()
    
    if file_list:
        file_drive = file_list[0] # 기존 파일 선택
        print(f"Updating existing file: {filename}")
    else:
        file_drive = drive.CreateFile({'title': filename, 'parents': [{'id': folder_id}]})
        print(f"Creating new file: {filename}")

    file_drive.SetContentFile(filename)
    file_drive.Upload()

def main():
    visited_titles = load_visited_papers()
    all_candidate_papers = []
    seen_titles_this_run = set()

    for kw in KEYWORDS:
        for page in range(3): 
            papers = fetch_papers(kw, offset=page*100)
            if not papers: break
            for p in papers:
                title, venue = p.get('title'), p.get('venue', '')
                if not title or not venue: continue
                
                venue_clean = venue.lower().replace(" ", "")
                is_target = any(j.lower().replace(" ", "") in venue_clean for j in TARGET_JOURNALS)
                
                if is_target and title not in visited_titles and title not in seen_titles_this_run:
                    authors = ", ".join([a['name'] for a in p.get('authors', [])]) or "Unknown Authors"
                    p['author_display'] = authors
                    p['pub_date'] = p.get('publicationDate') or str(p.get('year', 'N/A'))
                    all_candidate_papers.append(p)
                    seen_titles_this_run.add(title)

    all_candidate_papers.sort(key=lambda x: x['pub_date'], reverse=True)
    final_papers = all_candidate_papers[:20]

    # 파일 작성 (기존 내용을 덮어쓰고 최신 데이터만 유지)
    with open(FIXED_FILENAME, "w", encoding="utf-8") as f:
        f.write(f"# Latest Research Update: {datetime.date.today()}\n\n")
        f.write(f"**추출 기준:** {len(TARGET_JOURNALS)}개 주요 저널 내 최신 발행물 (중복 제외)\n\n")
        
        if not final_papers:
            f.write("> **알림:** 새로운 타겟 저널 논문이 발견되지 않았습니다. 내일 다시 확인해 주세요.\n\n")
        else:
            for i, p in enumerate(final_papers, 1):
                doi = p.get('externalIds', {}).get('DOI')
                link = f"https://doi.org/{doi}" if doi else f"https://www.semanticscholar.org/paper/{p.get('paperId')}"
                
                f.write(f"## {i}. [{p['title']}]({link})\n")
                f.write(f"- **Authors:** {p['author_display']}\n")
                f.write(f"- **Journal:** {p.get('venue')}\n")
                f.write(f"- **Date:** {p.get('pub_date')}\n")
                if doi: f.write(f"- **DOI:** [{doi}](https://doi.org/{doi})\n")
                f.write(f"- **Abstract:** {p.get('abstract', 'N/A')}\n\n---\n")

    if final_papers:
        save_visited_papers([p['title'] for p in final_papers])
        upload_or_update_drive(FIXED_FILENAME)

if __name__ == "__main__":
    main()
