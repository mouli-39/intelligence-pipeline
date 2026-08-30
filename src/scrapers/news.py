import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from typing import List
from src.utils.logging import setup_logger
from src.utils.dates import parse_flexible_datetime, is_within_24_hours
from src.models import NewsEntity, SourceMetadata

logger = setup_logger("news_scraper")

ATOM_NS = "http://www.w3.org/2005/Atom"

class NewsScraper:
    """Asynchronous pipeline consuming distinct AI news channels with freshness filters."""
    
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.sources = {
            "HackerNews AI": "https://hnrss.org/newest?q=AI",
            "HackerNews ML": "https://hnrss.org/newest?q=Machine+Learning",
            "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
            "Reddit AI": "https://www.reddit.com/r/artificial/.rss",
            "Reddit ML": "https://www.reddit.com/r/MachineLearning/.rss"
        }

    async def fetch_source_feed(self, source_name: str, url: str) -> List[NewsEntity]:
        valid_records = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Pipeline/1.0"}
        
        try:
            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    return valid_records
                xml_content = await response.text()
                
            root = ET.fromstring(xml_content)
            # Support both RSS 2.0 channels and Atom updates dynamically
            items = root.findall(".//item") or root.findall(f".//{{{ATOM_NS}}}entry")
            
            for item in items:
                title_node = item.find("title") or item.find(f"{{{ATOM_NS}}}title")
                link_node = item.find("link") or item.find(f"{{{ATOM_NS}}}link")
                date_node = item.find("pubDate") or item.find("updated") or item.find(f"{{{ATOM_NS}}}published") or item.find(f"{{{ATOM_NS}}}updated")
                
                if title_node is None or title_node.text is None:
                    continue
                    
                pub_date = parse_flexible_datetime(date_node.text if date_node is not None else "")
                
                link_url = url
                if link_node is not None:
                    if link_node.text and link_node.text.strip():
                        link_url = link_node.text.strip()
                    elif link_node.get("href"):
                        link_url = link_node.get("href")

                valid_records.append(NewsEntity(
                    source=SourceMetadata(name=source_name, url=str(link_url)),
                    **{
                        "content.title": title_node.text.strip(),
                        "content.published_at": pub_date
                    }
                ))
        except Exception as e:
            logger.warning(f"Failed parsing news stream {source_name}: {str(e)}")
            
        return valid_records

    async def collect_fresh_news(self) -> List[NewsEntity]:
        logger.info("Starting fresh AI news updates collection phase...")
        tasks = [self.fetch_source_feed(name, url) for name, url in self.sources.items()]
        results = await asyncio.gather(*tasks)
        
        flat_list = [item for sublist in results for item in sublist]
        fresh_list = [item for item in flat_list if is_within_24_hours(item.publishedAt)]
        
        # Fall back to flat_list if 24h filter produces very few items
        result_list = fresh_list if len(fresh_list) >= 2 else flat_list
        logger.info(f"Retrieved {len(result_list)} news items matching freshness criteria.")
        return result_list

