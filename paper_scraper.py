import requests
import datetime
import time
import os

# 1. 설정: 키워드 및 저널 리스트
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
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={keyword}&limit=100&offset={offset}&sort=publicationDate:desc&fields=title,venue,year,authors,externalIds,abstract,publicationDate,paperId"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            return response.json().get('data', [])
        elif response.status_code == 429:
            time.sleep(15)
            return fetch_papers(keyword, offset)
    except Exception as e:
        print(f"Error: {e}")
    return []

def main():
    visited_titles = load_visited_papers()
    all_candidate_papers = []
    seen_titles_this_run = set()

    print("새로운 논문을 검색 중입니다...")
    for kw in KEYWORDS:
        for page in range(2): # 검색 효율을 위해 페이지 조절
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

    # 발행일 순 정렬 후 상위 5편 추출
    all_candidate_papers.sort(key=lambda x: x['pub_date'], reverse=True)
    new_papers = all_candidate_papers[:5]

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    # 파일이 없으면 헤더 생성, 있으면 이어쓰기(Append)
    mode = "a" if os.path.exists(FIXED_FILENAME) else "w"
    
    with open(FIXED_FILENAME, mode, encoding="utf-8") as f:
        if mode == "w":
            f.write("# Research Archive: Spatial Crime & Urban Studies\n\n")
            f.write("이 파일은 매일 아침 중복되지 않은 최신 논문 5편을 자동으로 추가합니다.\n\n")

        if not new_papers:
            print("오늘 추가할 새로운 논문이 없습니다.")
        else:
            f.write(f"## 📅 Added on: {today_str}\n\n")
            for i, p in enumerate(new_papers, 1):
                doi = p.get('externalIds', {}).get('DOI')
                link = f"https://doi.org/{doi}" if doi else f"https://www.semanticscholar.org/paper/{p.get('paperId')}"
                f.write(f"### {i}. [{p['title']}]({link})\n")
                f.write(f"- **Journal:** {p.get('venue')}\n")
                f.write(f"- **Authors:** {p['author_display']}\n")
                f.write(f"- **Pub Date:** {p.get('pub_date')}\n")
                if doi: f.write(f"- **DOI:** {doi}\n")
                f.write(f"- **Abstract:** {p.get('abstract', 'N/A')}\n\n")
            f.write("---\n\n") # 날짜별 구분선

    if new_papers:
        save_visited_papers([p['title'] for p in new_papers])
        print(f"성공적으로 {len(new_papers)}편의 논문을 {FIXED_FILENAME}에 추가했습니다.")

if __name__ == "__main__":
    main()
