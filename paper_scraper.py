import requests
import datetime

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
    # 최신성(publicationDate:desc)을 최우선으로 정렬하여 검색
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={keyword}&limit=100&sort=publicationDate:desc&fields=title,venue,year,authors,externalIds,abstract,publicationDate"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('data', [])
    return []

def main():
    all_candidate_papers = []
    seen_titles = set()

    for kw in KEYWORDS:
        papers = fetch_papers(kw)
        for p in papers:
            venue = p.get('venue', '')
            # 타겟 저널 필터링 (대소문자 무시)
            if any(journal.lower() in venue.lower() for journal in TARGET_JOURNALS):
                if p['title'] not in seen_titles:
                    # 저자 명단 추출 (쉼표로 구분)
                    author_names = [author['name'] for author in p.get('authors', [])]
                    p['author_display'] = ", ".join(author_names) if author_names else "Unknown Authors"
                    
                    # 정렬을 위한 날짜 처리
                    p['pub_date'] = p.get('publicationDate') if p.get('publicationDate') else "0000-00-00"
                    
                    all_candidate_papers.append(p)
                    seen_titles.add(p['title'])
    
    # 전체 수집 결과에서 한 번 더 날짜 최신순으로 정렬 (현재 일자 기준 가장 따끈따끈한 논문 상단 배치)
    all_candidate_papers.sort(key=lambda x: x['pub_date'], reverse=True)
    
    # 최종 상위 20편 선택
    final_papers = all_candidate_papers[:20]

    # 2. 결과 Markdown 파일 생성
    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"Daily_Research_{today}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Daily Research Update: {today}\n\n")
        f.write(f"**검색 기준:** 타겟 저널 내 최신 발행 논문 (상위 20편 우선순위 정렬)\n\n")
        
        if not final_papers:
            f.write("현재 일자 기준, 조건에 맞는 새로운 논문을 찾지 못했습니다.\n")
        else:
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
