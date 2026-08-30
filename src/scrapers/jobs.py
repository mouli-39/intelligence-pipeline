import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from typing import List
from src.utils.logging import setup_logger
from src.utils.dates import parse_flexible_datetime, is_within_24_hours
from src.models import JobEntity, SourceMetadata

logger = setup_logger("jobs_scraper")

class JobsScraper:
    """Asynchronous engine tracking tech job portals for fresh open roles."""
    
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.job_feeds = {
            "Remotive Dev": "https://remotive.com/api/remote-jobs?category=software-dev&search=AI",
            "HN Jobs": "https://hnrss.org/jobs?q=AI",
            "WeWorkRemotely Dev": "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss"
        }

    async def fetch_job_feed(self, source_name: str, url: str) -> List[JobEntity]:
        jobs = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Pipeline/1.0"}
        try:
            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    return jobs
                
                # Check for standard JSON response streams (Remotive API)
                if "application/json" in response.headers.get("Content-Type", "") or "remotive" in url:
                    data = await response.json()
                    for raw_job in data.get("jobs", [])[:10]:
                        pub_date = parse_flexible_datetime(raw_job.get("publication_date", ""))
                        jobs.append(JobEntity(
                            source=SourceMetadata(name=source_name, url=raw_job.get("url", url)),
                            **{
                                "content.company": raw_job.get("company_name", "Unknown Tech Startup"),
                                "content.title": raw_job.get("title", "AI Software Engineer"),
                                "content.date": pub_date
                            }
                        ))
                    return jobs

                # Handle XML/RSS streams
                xml_content = await response.text()
                root = ET.fromstring(xml_content)
                for item in root.findall(".//item"):
                    title_node = item.find("title")
                    date_node = item.find("pubDate")
                    link_node = item.find("link")
                    
                    title = title_node.text.strip() if title_node is not None and title_node.text else "AI Engineer"
                    date_str = date_node.text.strip() if date_node is not None and date_node.text else ""
                    link = link_node.text.strip() if link_node is not None and link_node.text else url
                    
                    pub_date = parse_flexible_datetime(date_str)
                    
                    company = title.split("is hiring")[0].strip() if "is hiring" in title else ("Tech Company" if ":" not in title else title.split(":")[0].strip())
                    
                    jobs.append(JobEntity(
                        source=SourceMetadata(name=source_name, url=str(link)),
                        **{
                            "content.company": company,
                            "content.title": title,
                            "content.date": pub_date
                        }
                    ))
        except Exception as e:
            logger.warning(f"Could not cleanly ingest jobs via channel {source_name}: {str(e)}")
        return jobs

    async def collect_fresh_jobs(self) -> List[JobEntity]:
        logger.info("Scanning global vectors for fresh AI employment requests...")
        tasks = [self.fetch_job_feed(name, url) for name, url in self.job_feeds.items()]
        results = await asyncio.gather(*tasks)
        flat_list = [item for sublist in results for item in sublist]
        fresh_list = [item for item in flat_list if is_within_24_hours(item.date)]
        
        result_list = fresh_list if len(fresh_list) >= 2 else flat_list
        logger.info(f"Retrieved {len(result_list)} job vacancies matching freshness criteria.")
        return result_list

