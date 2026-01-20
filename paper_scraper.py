import requests
import datetime
import time

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

def fetch_papers(keyword, offset=0, limit=100):
    # offset을 사용하여 검색 결과의 다음 페이지까지 가져올 수 있도록 설정
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={keyword}&limit={limit}&offset={offset}&sort=publicationDate:desc&fields=title,venue,year,authors,externalIds,abstract,publicationDate"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('data', [])
    elif response.status_code == 429: # 너무 많은 요청 시 잠시 대기
        time.sleep(5)
        return fetch_papers(keyword, offset, limit)
    return []

def main():
    all_candidate_papers = []
    seen_titles = set()

    for kw in KEYWORDS:
        # 각 키워드별로 검색량을 기존 100개에서 300개로 늘림 (3페이지 분량)
        for page in range(3): 
            papers = fetch_papers(kw, offset=page*100)
            if not papers:
                break
                
            for p in papers:
                venue = p.get('venue', '')
                if any(journal.lower() in venue.lower() for journal in TARGET_JOURNALS):
                    if p['title'] not in seen_titles:
                        author_names = [author['name'] for author in p.get('authors', [])]
                        p['author_display'] = ", ".join(author_names) if author_names else "Unknown Authors"
                        p['pub_date'] = p.get('publicationDate') if p.get('publicationDate') else "1900-01-01"
                        
                        all_candidate_papers.append(p)
                        seen_titles.add(p['title'])
            
            # 이미 타겟 저널 논문을 충분히 확보했다면 다음 페이지 검색 중단
            if len(all_candidate_papers) > 50:
                break

    # 최신순 정렬
    all_candidate_papers.sort(key=lambda x: x['pub_date'], reverse=True)
    
    # 상위 20편 선택
    final_papers = all_candidate_papers[:20]

    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"Daily_Research_{today}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Daily Research Update: {today}\n\n")
        f.write(f"**상태:** 타겟 저널 최신 논문 20편 수집 완료 (검색 범위 확대 적용)\n\n")
        
        if len(final_papers) < 20:
            f.write(f"> **알림:** 검색된 후보군 중 타겟 저널 논문이 {len(final_papers)}편 뿐입니다. (검색 범위를 더 넓힐 수 있습니다.)\n\n")

        for i, p in enumerate(final_papers, 1):
            doi = p.get('externalIds', {}).get('DOI', 'N/A')
            pub_date = p.get('publicationDate', 'N/A')
            f.write(f"## {i}. {p['title']}\n")
            f.write(f"- **Authors:** {p['author_display']}\n")
            f.write(f"- **Journal:** {p.get('venue', 'Unknown')}\n")
            f.write(f"- **Publication Date:** {pub_date}\n")
            f.write(f"- **DOI:** {doi}\n")
            f.write(f"- **Abstract:** {p.get('abstract', 'No abstract available.')}\n\n")
            f.write("---\n")

if __name__ == "__main__":
    main()
