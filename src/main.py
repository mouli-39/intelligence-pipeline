import asyncio
import aiohttp
from datetime import datetime, timezone

from src.utils.logging import setup_logger
from src.scrapers.papers import ResearchPapersScraper
from src.scrapers.startups import StartupsScraper
from src.scrapers.products import ProductsScraper
from src.scrapers.news import NewsScraper
from src.scrapers.jobs import JobsScraper
from src.entity.resolver import EntityResolver
from src.storage.google_sheets import GoogleSheetsDataStore

logger = setup_logger("production_pipeline")

async def run_pipeline():
    logger.info("LAUNCHING PRODUCTION-SCALE AI INTELLIGENCE INGESTION PIPELINE")

    resolver = EntityResolver()
    store = GoogleSheetsDataStore()

    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        paper_scraper = ResearchPapersScraper(session, concurrency_limit=3)
        startup_scraper = StartupsScraper(session, concurrency_limit=3)
        product_scraper = ProductsScraper(session)
        news_scraper = NewsScraper(session)
        jobs_scraper = JobsScraper(session)

        logger.info("Spawning ingestion workers concurrently across data sources...")
        
        tasks = [
            paper_scraper.collect_papers(target_count=5),
            startup_scraper.collect_startups(target_count=5),
            product_scraper.collect_products(target_count=5),
            news_scraper.collect_fresh_news(),
            jobs_scraper.collect_fresh_jobs()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        papers_data = results[0] if not isinstance(results[0], Exception) else []
        startups_data = results[1] if not isinstance(results[1], Exception) else []
        products_data = results[2] if not isinstance(results[2], Exception) else []
        news_data = results[3] if not isinstance(results[3], Exception) else []
        jobs_data = results[4] if not isinstance(results[4], Exception) else []

        if papers_data:
            paper_rows = []
            for paper in papers_data:
                paper_rows.append([
                    paper.title,
                    ", ".join(paper.authors),
                    paper.paperUrl,
                    paper.githubUrl or "None",
                    paper.githubStars,
                    paper.publishedDate.strftime("%Y-%m-%d")
                ])
            store.append_rows_to_tab("Research Papers", paper_rows)

        if startups_data:
            startup_rows = []
            for startup in startups_data:
                canonical_name, _ = resolver.resolve_entity(startup.entityName)
                startup_rows.append([
                    canonical_name,
                    startup.employeeCount or "Unknown",
                    startup.source.name,
                    startup.source.url,
                    startup.collectedAt.isoformat()
                ])
            store.append_rows_to_tab("Startups", startup_rows)

        if products_data:
            product_rows = []
            for product in products_data:
                canonical_company, _ = resolver.resolve_entity(product.startupName)
                product_rows.append([
                    canonical_company,
                    product.pricingModel.value,
                    product.source.name,
                    product.source.url,
                    product.collectedAt.isoformat()
                ])
            store.append_rows_to_tab("Products", product_rows)

        if news_data:
            news_rows = []
            for item in news_data:
                news_rows.append([
                    item.title,
                    item.source.name,
                    item.source.url,
                    item.publishedAt.isoformat()
                ])
            store.append_rows_to_tab("News", news_rows)

        if jobs_data:
            job_rows = []
            for job in jobs_data:
                canonical_org, _ = resolver.resolve_entity(job.company)
                job_rows.append([
                    job.title,
                    canonical_org,
                    job.source.name,
                    job.source.url,
                    job.date.isoformat()
                ])
            store.append_rows_to_tab("Jobs", job_rows)

        if resolver.resolution_log:
            log_rows = [[raw, canonical] for raw, canonical in resolver.resolution_log.items()]
            store.append_rows_to_tab("Entity Mapping Log", log_rows)

        store.export_unified_spreadsheet()

    logger.info("PIPELINE EXECUTION SUCCESSFULLY COMPLETED. DATA STAGED.")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
