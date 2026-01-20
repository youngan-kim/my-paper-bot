import requests
import datetime
import os

# 1. 설정: 키워드 및 타겟 저널 리스트
KEYWORDS = ["neighborhood and crime", "spatial crime pattern", "spatial analysis", "urban studies"]
TARGET_JOURNALS = [
    "Criminology", "Journal of Quantitative Criminology", "Justice Quarterly", 
    "Journal of Research in Crime and Delinquency", "British Journal of Criminology",
    "Annual Review of Criminology", "Journal of Criminal Justice",
    "Annals of the American Association of Geographers", "Geographical Analysis",
    "Applied Geography", "Professional Geographer", "Transactions in GIS",
    "Cities", "Urban Studies", "Journal of Urban Affairs",
    "American Sociological Review", "Annual Review of Sociology",
    "American Journal of Sociology", "Social Forces", "Health & Place"
]

def fetch_papers(keyword):
    # Semantic Scholar API 사용 (최신순 정렬)
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={keyword}&limit=50&fields=title,venue,year,externalIds,abstract,publicationDate"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('data', [])
    return []

def main():
    all_papers = []
    seen_titles = set()

    for kw in KEYWORDS:
        papers = fetch_papers(kw)
        for p in papers:
            # 저널 필터링 (대소문자 구분 없이 포함 여부 확인)
            venue = p.get('venue', '')
            if any(journal.lower() in venue.lower() for journal in TARGET_JOURNALS):
                if p['title'] not in seen_titles:
                    all_papers.append(p)
                    seen_titles.add(p['title'])

    # 2. 결과 Markdown 파일 생성
    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"Daily_Research_{today}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Research Update: {today}\n\n")
        if not all_papers:
            f.write("오늘 업데이트된 새로운 타겟 저널 논문이 없습니다.\n")
        else:
            for p in all_papers:
                doi = p.get('externalIds', {}).get('DOI', 'N/A')
                f.write(f"### {p['title']}\n")
                f.write(f"- **Journal:** {p.get('venue', 'Unknown')}\n")
                f.write(f"- **Year:** {p.get('year', 'N/A')}\n")
                f.write(f"- **DOI:** {doi}\n")
                f.write(f"- **Abstract:** {p.get('abstract', 'No abstract available.')}\n\n")
                f.write("---\n")

if __name__ == "__main__":
    main()
