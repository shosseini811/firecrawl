# Claude 3.7 Stock Analyzer

A Python application that uses Claude 3.7, Firecrawl, and E2B to analyze stocks and provide investment recommendations.

## Overview

This tool helps you analyze stocks by:

1. Searching for stock information on Robinhood
2. Scraping relevant stock pages
3. Using Claude 3.7 to analyze the data and score investment opportunities
4. Generating a visualization of the stock scores

## Requirements

- Python 3.8+
- Firecrawl API key
- Anthropic API key
- E2B API key

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   ```
   source venv/bin/activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project directory with your API keys:
   ```
   # Anthropic API Key
   ANTHROPIC_API_KEY=your_anthropic_api_key_here

   # E2B API Key
   E2B_API_KEY=your_e2b_api_key_here

   # FireCrawl API Key
   FIRECRAWL_API_KEY=your_firecrawl_api_key_here
   ```

## Usage

Run the script:
```
python claude-3.7-stock-analyzer.py
```

When prompted, enter the stock symbol or name you're interested in (e.g., "AAPL" or "apple").

The script will:
1. Search for relevant stock pages on Robinhood
2. Scrape the content from those pages
3. Analyze the information using Claude 3.7
4. Generate a chart showing the investment scores for the top stocks
5. Save the chart as `chart.png` in the project directory

## How It Works

### 1. Stock Search
The tool uses Firecrawl to search for stock information on Robinhood based on your input.

### 2. Data Collection
It scrapes the top 10 relevant stock pages to gather information.

### 3. AI Analysis
Claude 3.7 analyzes the collected data and assigns investment scores to each stock.

### 4. Visualization
The E2B code interpreter generates a bar chart showing the relative scores of each stock.

## Project Structure

- `claude-3.7-stock-analyzer.py` - Main script
- `requirements.txt` - Python dependencies
- `.env` - API keys (not included in repository)
- `chart.png` - Generated visualization (created when script runs)

## Dependencies

- firecrawl - For web crawling and data extraction
- anthropic - For accessing Claude 3.7 AI
- e2b-code-interpreter - For running code in a sandbox environment
- python-dotenv - For loading environment variables
- matplotlib - For creating visualizations
