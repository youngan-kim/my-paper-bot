import requests
import datetime
import time
import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

# 1. 설정: 키워드 및 타겟 저널 리스트
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
    # GitHub Secrets에서 가져온 JSON으로 인증
    scope = ['https://www.googleapis.com/auth/drive']
    try:
        key_dict = json.loads(os.environ['GDRIVE_SERVICE_ACCOUNT'])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
        
        gauth = GoogleAuth()
        gauth.credentials = creds
        drive = GoogleDrive(gauth)

        folder_id = os.environ['GDRIVE_FOLDER_ID']
        file_drive = drive.CreateFile({
            'title': filename,
            'parents': [{'id': folder_id}]
        })
        file_drive.SetContentFile(filename)
        file_drive.Upload()
        print(f"Successfully uploaded {filename} to Google Drive!")
    except Exception as e:
        print(f"Drive upload failed: {e}")

def main():
    all_candidate_papers = []
    seen_titles = set()

    for kw in KEYWORDS:
        for page in range(2): 
            papers = fetch_papers(kw, offset=page*100)
            if not papers:
                break
                
            for p in papers:
                venue = p.get('venue', '')
                if not venue: continue
                
                if any(journal.lower() in venue.lower() for journal in TARGET_JOURNALS):
                    if p['title'] not in seen_titles:
                        author_names = [author['name'] for author in p.get('authors', [])]
                        p['author_display'] = ", ".join(author_names) if author_names else "Unknown Authors"
                        p['pub_date'] = p.get('publicationDate') if p.get('publicationDate') else "1900-01-01"
                        all_candidate_papers.append(p)
                        seen_titles.add(p['title'])
            
            if len(all_candidate_papers) > 100:
                break

    all_candidate_papers.sort(key=lambda x: x['pub_date'], reverse=True)
    final_papers = all_candidate_papers[:20]

    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"Daily_Research_{today}.md"
    
    # 파일 쓰기 부분의 들여쓰기를 확인하세요
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Daily Research Update: {today}\n\n")
        f.write(f"**Field:** Spatial Analysis & ML Focused\n\n")
        
        if not final_papers:
            f.write("No papers found for today.\n")
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

    # 업로드 실행 (함수 밖으로 나가지 않게 주의)
    upload_to_drive(filename)

if __name__ == "__main__":
    main()
