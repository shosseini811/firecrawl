import os
import sys
import json
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
app = FirecrawlApp(api_key=firecrawl_api_key)
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
        
        # Debug - print the app object type
        print(f"DEBUG: app type: {type(app)}")
        
        # Call map_url with the search term
        map_website = app.map_url(url, search=map_search_parameter)
        print(f"{Colors.GREEN}Website mapping completed successfully.{Colors.RESET}")
        
        # Debug the response type
        print(f"DEBUG: map_website type: {type(map_website)}")
        
        # Try to access links as an attribute instead of dictionary key
        if hasattr(map_website, 'links'):
            print(f"{Colors.GREEN}Located {len(map_website.links)} relevant links.{Colors.RESET}")
            return map_website.links
        else:
            print(f"DEBUG: No links attribute found in response")
            return []
    except Exception as e:
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

        # Debug the batch_scrape_urls method
        print(f"DEBUG: batch_scrape_urls method signature: {app.batch_scrape_urls.__code__.co_varnames[:app.batch_scrape_urls.__code__.co_argcount]}")
        print(f"DEBUG: batch_scrape_urls takes {app.batch_scrape_urls.__code__.co_argcount} arguments")
        
        # Call with just the URLs parameter as that's all it accepts
        batch_scrape_result = app.batch_scrape_urls(top_links)

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
        
        # Check if it has a data attribute instead of being subscriptable
        if hasattr(batch_scrape_result, 'data'):
            print(f"DEBUG: Using batch_scrape_result.data, type: {type(batch_scrape_result.data)}")
            
            # Get the first result to inspect its structure
            if batch_scrape_result.data and len(batch_scrape_result.data) > 0:
                first_result = batch_scrape_result.data[0]
                print(f"DEBUG: First result type: {type(first_result)}")
                print(f"DEBUG: First result attributes: {dir(first_result)[:15]}...")
                
                # Try to access markdown as an attribute
                if hasattr(first_result, 'markdown'):
                    print(f"DEBUG: Found 'markdown' attribute")
                    
            # Process all results
            for scrape_result in batch_scrape_result.data:
                # Try to access markdown as an attribute instead of a dictionary key
                if hasattr(scrape_result, 'markdown'):
                    stock_contents.append({
                        'content': scrape_result.markdown
                    })
                else:
                    print(f"DEBUG: No markdown attribute found in result")

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
