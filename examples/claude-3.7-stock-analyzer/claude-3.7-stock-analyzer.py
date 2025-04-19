import os
import sys
import json
import requests
from dotenv import load_dotenv
import anthropic
from e2b_code_interpreter import Sandbox
import base64

# Add the parent directory to the Python path so we can import firecrawl
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from firecrawl import FirecrawlApp

# ANSI color codes
class Colors:
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

# Load environment variables
print(f"Current working directory: {os.getcwd()}")
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Looking for .env file at: {env_path}")
load_dotenv(env_path)

# Retrieve API keys from environment variables
firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
e2b_api_key = os.getenv("E2B_API_KEY")

# Debug: Check if API keys are loaded
print(f"FIRECRAWL_API_KEY loaded: {firecrawl_api_key is not None}")
print(f"ANTHROPIC_API_KEY loaded: {anthropic_api_key is not None}")
print(f"E2B_API_KEY loaded: {e2b_api_key is not None}")

# Initialize the FirecrawlApp and Anthropic client
# Use localhost instead of cloud service
app = FirecrawlApp(api_url='http://localhost:8000')
client = anthropic.Anthropic(api_key=anthropic_api_key)
sandbox = Sandbox(api_key=e2b_api_key)

# Find the relevant stock pages via map
def find_relevant_page_via_map(stock_search_term, url, app):
    try:
        print(f"{Colors.CYAN}Searching for stock: {stock_search_term}{Colors.RESET}")
        print(f"{Colors.CYAN}Initiating search on the website: {url}{Colors.RESET}")

        map_search_parameter = stock_search_term

        print(f"{Colors.GREEN}Search parameter: {map_search_parameter}{Colors.RESET}")

        print(f"{Colors.YELLOW}Mapping website using the identified search parameter...{Colors.RESET}")
        
        # Call map_url with the search term
        map_website = app.map_url(url, search=map_search_parameter)
        print(f"{Colors.GREEN}Website mapping completed successfully.{Colors.RESET}")
        
        # Handle both dictionary and object responses
        if isinstance(map_website, dict):
            if 'success' in map_website and map_website['success'] and 'data' in map_website:
                data = map_website['data']
                if 'links' in data:
                    print(f"{Colors.GREEN}Located {len(data['links'])} relevant links.{Colors.RESET}")
                    return data['links']
            elif 'links' in map_website:
                print(f"{Colors.GREEN}Located {len(map_website['links'])} relevant links.{Colors.RESET}")
                return map_website['links']
        elif hasattr(map_website, 'links'):
            print(f"{Colors.GREEN}Located {len(map_website.links)} relevant links.{Colors.RESET}")
            return map_website.links
        
        print(f"DEBUG: No links found in response")
        return []
    except Exception as e:
        # Check if the error response contains useful information
        try:
            error_str = str(e)
            if 'success' in error_str:
                # Try to parse the error string as JSON-like dictionary
                import ast
                error_data = ast.literal_eval(error_str.split('Error: ', 1)[1])
                if error_data.get('success') and 'data' in error_data:
                    data = error_data['data']
                    if 'links' in data:
                        print(f"{Colors.GREEN}Found links in response.{Colors.RESET}")
                        return data['links']
        except:
            pass
            
        if hasattr(e, 'response') and hasattr(e.response, 'json'):
            try:
                error_data = e.response.json()
                if isinstance(error_data, dict):
                    if error_data.get('success') and 'data' in error_data:
                        data = error_data['data']
                        if 'links' in data:
                            print(f"{Colors.GREEN}Found links in error response.{Colors.RESET}")
                            return data['links']
                    elif 'links' in error_data:
                        print(f"{Colors.GREEN}Found links in error response.{Colors.RESET}")
                        return error_data['links']
            except:
                pass
                
        print(f"{Colors.RED}Error encountered during relevant page identification: {str(e)}{Colors.RESET}")
        return None

# Function to plot the scores using e2b
def plot_scores(stock_names, stock_scores):
    print(f"{Colors.YELLOW}Plotting scores...{Colors.RESET}")
    code_to_run = f"""
import matplotlib.pyplot as plt

stock_names = {stock_names}
stock_scores = {stock_scores}

plt.figure(figsize=(10, 5))
plt.bar(stock_names, stock_scores, color='blue')
plt.xlabel('Stock Names')
plt.ylabel('Scores')
plt.title('Stock Investment Scores')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('chart.png')
plt.show()
"""
    # Run the code inside the sandbox
    execution = sandbox.run_code(code_to_run)

    # Check if there are any results
    if execution.results and execution.results[0].png:
        first_result = execution.results[0]

        # Get the directory where the current python file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Save the png to a file in the examples directory. The png is in base64 format.
        with open(os.path.join(current_dir, 'chart.png'), 'wb') as f:
            f.write(base64.b64decode(first_result.png))
        print('Chart saved as examples/chart.png')
    else:
        print(f"{Colors.RED}No results returned from the sandbox execution.{Colors.RESET}")

# Analyze the top stocks and provide investment recommendation
def analyze_top_stocks(map_website, app, client):
    try:
        # Get top 5 links from the map result
        top_links = map_website[:10]
        print(f"{Colors.CYAN}Proceeding to analyze top {len(top_links)} links: {top_links}{Colors.RESET}")

        # Scrape each URL individually since we're using a local server
        batch_scrape_result = {
            'success': True,
            'data': []
        }
        
        for url in top_links:
            try:
                # Make a POST request to the scrape endpoint
                response = requests.post(
                    'http://localhost:8000/v1/scrape',
                    json={'url': url}
                )
                response.raise_for_status()
                
                # Add the results to our batch result
                result = response.json()
                if result.get('success') and result.get('data'):
                    batch_scrape_result['data'].extend(result['data'])
            except Exception as e:
                print(f"Error scraping {url}: {e}")

        # Get all attributes of the FirecrawlDocument object
        # all_attributes = dir(batch_scrape_result.data[0])
        # print("All attributes of FirecrawlDocument:")
        # print(all_attributes)

        print(f"{Colors.GREEN}Batch page scraping completed successfully.{Colors.RESET}")
        
        # Debug the response type
        print(f"DEBUG: batch_scrape_result type: {type(batch_scrape_result)}")
        print(f"DEBUG: batch_scrape_result attributes: {dir(batch_scrape_result)[:10]}...")
        
        # Prepare content for LLM
        stock_contents = []
        
        # Handle both dictionary and object responses for batch_scrape_result
        data = []
        if isinstance(batch_scrape_result, dict):
            if batch_scrape_result.get('success') and 'data' in batch_scrape_result:
                data = batch_scrape_result['data']
        elif hasattr(batch_scrape_result, 'data'):
            data = batch_scrape_result.data
        
        # Process all results
        for scrape_result in data:
            content = None
            # Handle both dictionary and object responses for scrape_result
            if isinstance(scrape_result, dict) and 'markdown' in scrape_result:
                content = scrape_result['markdown']
            elif hasattr(scrape_result, 'markdown'):
                content = scrape_result.markdown
            
            if content:
                stock_contents.append({'content': content})
            else:
                print(f"DEBUG: No markdown content found in result")

        # Pass all the content to the LLM to analyze and decide which stock to invest in
        analyze_prompt = f"""
        Based on the following information about different stocks from their Robinhood pages, 
        analyze and determine which stock is the best investment opportunity. DO NOT include any other text, just the JSON.
        Return the result in the following JSON format. 
        Only return the JSON, nothing else. Do not include backticks or any other formatting, just the JSON.
{{
    "scores": [
        {{
            "stock_name": "<stock_name>",
            "score": <score-out-of-100>
        }},
        ...
    ]
}}

Stock Information:
"""

        for stock in stock_contents:
            analyze_prompt += f"Content:\n{stock['content']}\n"

        print(f"{Colors.YELLOW}Analyzing stock information with LLM...{Colors.RESET}")
        analyze_prompt += f"\n\nStart JSON:\n"
        completion = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1000,
            temperature=0,
            system="You are a financial analyst. Only return the JSON, nothing else.",
            messages=[
                {
                    "role": "user",
                    "content": analyze_prompt
                }
            ]
        )

        result = completion.content[0].text
        print(f"{Colors.GREEN}Analysis completed. Here is the recommendation:{Colors.RESET}")
        print(f"{Colors.MAGENTA}{result}{Colors.RESET}")

        # Plot the scores using e2b
        try:
            result_json = json.loads(result)
            scores = result_json['scores']
            stock_names = [score['stock_name'] for score in scores]
            stock_scores = [score['score'] for score in scores]

            plot_scores(stock_names, stock_scores)
        except json.JSONDecodeError as json_err:
            print(f"{Colors.RED}Error decoding JSON response: {str(json_err)}{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}Error encountered during stock analysis: {str(e)}{Colors.RESET}")

# Main function to execute the process
def main():
    # Get user input
    stock_search_term = input(f"{Colors.BLUE}Enter the stock you're interested in: {Colors.RESET}")
    if not stock_search_term.strip():
        print(f"{Colors.RED}No stock entered. Exiting.{Colors.RESET}")
        return

    url = "https://robinhood.com/stocks"

    print(f"{Colors.YELLOW}Initiating stock analysis process...{Colors.RESET}")
    # Find the relevant pages
    map_website = find_relevant_page_via_map(stock_search_term, url, app)

    if map_website:
        print(f"{Colors.GREEN}Relevant stock pages identified. Proceeding with detailed analysis...{Colors.RESET}")
        # Analyze top stocks
        print("map_website:", map_website)
        analyze_top_stocks(map_website, app, client)
    else:
        print(f"{Colors.RED}No relevant stock pages identified. Consider refining the search term or trying a different stock.{Colors.RESET}")

if __name__ == "__main__":
    main()
