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
    # 'sort=publicationDate:desc'와 'limit=100'을 조합해 키워드당 최신 논문을 넉넉히 가져옵니다.
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={keyword}&limit=100&sort=publicationDate:desc&fields=title,venue,year,authors,externalIds,abstract,publicationDate"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('data', [])
    return []

def main():
    all_candidate_papers = []
    seen_titles = set()

    # 각 키워드별로 최신 논문을 수집
    for kw in KEYWORDS:
        papers = fetch_papers(kw)
        for p in papers:
            venue = p.get('venue', '')
            # 타겟 저널 필터링 (대소문자 무시 및 부분 일치 확인)
            if any(journal.lower() in venue.lower() for journal in TARGET_JOURNALS):
                if p['title'] not in seen_titles:
                    # 저자 명단 추출
                    author_names = [author['name'] for author in p.get('authors', [])]
                    p['author_display'] = ", ".join(author_names) if author_names else "Unknown Authors"
                    
                    # 정렬용 날짜 (날짜 정보 없으면 아주 오래된 날짜로 처리)
                    p['pub_date'] = p.get('publicationDate') if p.get('publicationDate') else "1900-01-01"
                    
                    all_candidate_papers.append(p)
                    seen_titles.add(p['title'])
    
    # 2. 전체 후보군을 '발행일' 기준 내림차순(최신순)으로 정렬
    # 이 과정을 통해 '오늘' 논문이 없어도 '어제', '그저께' 논문 순으로 정렬됩니다.
    all_candidate_papers.sort(key=lambda x: x['pub_date'], reverse=True)
    
    # 3. 무조건 최신순 20편 선택
    final_papers = all_candidate_papers[:20]

    # 4. 결과 Markdown 파일 생성
    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"Daily_Research_{today}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Daily Research Update: {today}\n\n")
        f.write(f"**상태:** 타겟 저널 내 최신 발행 논문 20편 추출 완료 (정렬 기준: Publication Date)\n\n")
        
        if not final_papers:
            f.write("검색 결과가 없습니다. 키워드나 저널명을 확인해주세요.\n")
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
