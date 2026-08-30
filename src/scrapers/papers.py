import asyncio
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Optional
import aiohttp

from src.utils.logging import setup_logger
from src.utils.retry import with_retry
from src.models import ResearchPaperEntity

logger = setup_logger("papers_scraper")

NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom"
}

GITHUB_REGEX = re.compile(r"https?://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)")

class ResearchPapersScraper:
    """Asynchronous crawler for AI research papers and GitHub metrics."""
    
    def __init__(self, session: aiohttp.ClientSession, concurrency_limit: int = 5):
        self.session = session
        self.semaphore = asyncio.Semaphore(concurrency_limit)

    @with_retry(max_retries=3, base_delay=2.0)
    async def fetch_github_stars(self, owner: str, repo: str) -> int:
        """Queries GitHub API for repository star count."""
        repo = repo.rstrip(".,;)")
        url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {"User-Agent": "AI-Intelligence-Pipeline/1.0"}
        
        async with self.semaphore:
            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("stargazers_count", 0)
                elif response.status in (403, 429):
                    logger.warning(f"GitHub Rate limit hit for {owner}/{repo}.")
                    return 0
                return 0

    def _extract_github_url(self, text: str) -> Optional[str]:
        """Extracts GitHub URL from abstract text if available."""
        match = GITHUB_REGEX.search(text)
        if match:
            owner, repo = match.group(1), match.group(2).rstrip(".,;)")
            return f"https://github.com/{owner}/{repo}"
        return None

    @with_retry(max_retries=4, base_delay=3.0)
    async def fetch_arxiv_batch(self, start: int, max_results: int) -> List[ResearchPaperEntity]:
        """Fetches AI papers batch directly from arXiv API."""
        url = (
            f"http://export.arxiv.org/api/query?"
            f"search_query=cat:cs.AI&start={start}&max_results={max_results}&sortBy=submittedDate"
        )
        
        async with self.session.get(url, timeout=15) as response:
            if response.status != 200:
                raise Exception(f"arXiv API responded with status {response.status}")
            xml_data = await response.text()
            
        root = ET.fromstring(xml_data)
        papers = []
        tasks = []

        for entry in root.findall("atom:entry", NAMESPACES):
            title_node = entry.find("atom:title", NAMESPACES)
            id_node = entry.find("atom:id", NAMESPACES)
            published_node = entry.find("atom:published", NAMESPACES)
            summary_node = entry.find("atom:summary", NAMESPACES)

            if title_node is None or id_node is None or published_node is None:
                continue

            title = title_node.text.strip().replace("\n", " ")
            paper_url = id_node.text.strip()
            
            pub_date_str = published_node.text.strip()
            try:
                published_date = datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except ValueError:
                published_date = datetime.now(timezone.utc)

            authors = [
                author.find("atom:name", NAMESPACES).text.strip()
                for author in entry.findall("atom:author", NAMESPACES)
                if author.find("atom:name", NAMESPACES) is not None
            ]

            summary_text = summary_node.text if summary_node is not None else ""
            github_url = self._extract_github_url(summary_text)

            paper_dict = {
                "content.title": title,
                "content.authors": authors,
                "content.paper_url": paper_url,
                "content.github_url": github_url,
                "content.published_date": published_date
            }
            
            if github_url:
                match = GITHUB_REGEX.search(github_url)
                if match:
                    owner, repo = match.group(1), match.group(2)
                    tasks.append(self._enrich_paper_stars(paper_dict, owner, repo))
            else:
                paper_dict["content.github_stars"] = 0
                papers.append(ResearchPaperEntity(**paper_dict))

        if tasks:
            enriched_papers = await asyncio.gather(*tasks)
            papers.extend(enriched_papers)

        return papers

    async def _enrich_paper_stars(self, paper_dict: dict, owner: str, repo: str) -> ResearchPaperEntity:
        """Enriches paper metadata with live GitHub star counts."""
        stars = await self.fetch_github_stars(owner, repo)
        paper_dict["content.github_stars"] = stars
        return ResearchPaperEntity(**paper_dict)

    async def collect_papers(self, target_count: int = 10) -> List[ResearchPaperEntity]:
        """Collects the target count of AI research papers."""
        all_papers = []
        current_offset = 0
        batch_size = 20

        while len(all_papers) < target_count:
            logger.info(f"Gathering paper batch. Current offset: {current_offset}...")
            try:
                batch = await self.fetch_arxiv_batch(current_offset, batch_size)
                if not batch:
                    break
                all_papers.extend(batch)
                current_offset += batch_size
                await asyncio.sleep(1.0)
            except Exception as e:
                logger.error(f"Batch recovery step failed: {str(e)}")
                break

        return all_papers[:target_count]


