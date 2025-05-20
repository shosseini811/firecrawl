// Import the required modules from local Firecrawl SDK source file
import FirecrawlApp from './index.js';
// import FirecrawlApp from './index.js';
// Don't import directly from TypeScript files - they need compilation first

import 'dotenv/config';
// Initialize the Firecrawl app with your API key
// You can also set this as an environment variable named FIRECRAWL_API_KEY
const app = new FirecrawlApp({apiKey: process.env.FIRECRAWL_API_KEY});

// Add a debug property to see what's happening
console.log('FirecrawlApp initialized:', app);

type ScrapeFormat = "markdown" | "html" | "rawHtml" | "content" | "links" | "screenshot" | "screenshot@fullPage" | "extract" | "json" | "changeTracking";

// Example function to demonstrate website scraping
async function scrapeWebsite() {
  try {
    console.log('About to call scrapeUrl method');
    // Scrape a single website and get content in both markdown and HTML formats
    const params = {
      formats: ['markdown'] as ScrapeFormat[],
    };
    console.log('Parameters for scrapeUrl:', params);
    const scrapeResponse = await app.scrapeUrl('https://www.example.com/', params);

    if (scrapeResponse) {
      console.log('Scraping successful!');
      console.log('Scraped content:', scrapeResponse);
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error('Error while scraping:', errorMessage);
  }
}

// // Example function to demonstrate website crawling
// async function crawlWebsite() {
//   try {
//     // Crawl a website with a limit of 100 pages
//     // The scrapeOptions parameter allows you to specify the output formats
//     const crawlResponse = await app.crawlUrl('https://www.example.com/', {
//       limit: 100,
//       scrapeOptions: {
//         formats: ['markdown', 'html'],
//       }
//     });

//     if (crawlResponse) {
//       console.log('Crawling successful!');
//       console.log('Crawl results:', crawlResponse);
//     }
//   } catch (error) {
//     console.error('Error while crawling:', error.message);
//   }
// }

// Run the example functions
async function runExample() {
  console.log('Starting Firecrawl example...');
  
  // First, let's try scraping a single page
  console.log('\n1. Scraping a single page:');
  await scrapeWebsite();
  
  // // Then, let's crawl multiple pages
  // console.log('\n2. Crawling multiple pages:');
  // await crawlWebsite();
}

// Execute the example
runExample().catch(error => {
  console.error('An error occurred:', error.message);
});