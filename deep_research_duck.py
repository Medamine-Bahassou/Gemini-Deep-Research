import os
import asyncio
from duckduckgo_search import DDGS
from crawl4ai import *
from google import genai

class TerminalColors:
    """Provides ANSI escape codes for coloring terminal text."""
    RESET = '\033[0m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[34m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

async def crawl(urls):
    res = []
    async with AsyncWebCrawler() as crawler:
        for url in urls:
            try:
                result = await crawler.arun(
                    url=url,
                )
                res.append(result.markdown)
            except Exception as e:
                print(f"Error crawling {url}: {e}")
                res.append("")  # Use an empty string as a placeholder
    return res

def search(query, num_results=10):
    """
    Search the web using DuckDuckGo and return a list of URLs.
    
    Args:
        query (str): The search query.
        num_results (int, optional): Maximum number of results to return. Defaults to 10.
        
    Returns:
        list: A list of URL strings.
    """
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=num_results)
            return [result['href'] for result in results]
    except Exception as e:
        print(f"Search error: {e}")
        return []

def prompt(content):
    try : 
        client = genai.Client(api_key="api")  # Replace with your actual API key
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp", contents=content
        )
    except Exception as e : 
        return f"error prompt : {e}"

    return response.text

async def main():
    os.system('cls' if os.name == 'nt' else 'clear')

    user_input = input(f"{TerminalColors.GREEN}> {TerminalColors.RESET}")

    # get search data
    search_data = prompt(
        user_input +
        """
            summarize this input in one line to search in google
        """
    )
    search_history = [] # search history to avoid redendance
    search_history.append(search_data) 

    global_data = [] # the global data of research
    out = [] # final output

    
    # iterations = 2
    iterations = int(input(f"{TerminalColors.YELLOW}iterations > "))

    print(f"{TerminalColors.YELLOW}number of iterations: {iterations}")
    urls = []

    for i in range(iterations): 
        # the search decision
        print(f"{TerminalColors.RESET}>> {search_data}")
        
        # iteration to get the best results
        print(f"{TerminalColors.YELLOW}The iteration n°{i+1}")

        s = search(search_data)
        s = list(set(s) - set(urls))[:3]

        for idx, result in enumerate(s, 1):
            try:
                # result is already a list of URLs
                crawl_results = await crawl([result])
                out.extend(crawl_results)  # add results from crawling that URL.
                
                urls.append(result) # urls used before 

            except Exception as e:
                print(f"Error processing result {idx}: {e}")

        # Filter out any None or non-string elements from the list
        out = [item for item in out if isinstance(item, str)]
        data = "".join(out)
        global_data_template = f"""
                
                Do not exceed 50000 tokens in the response.
                
                <data>
                    {data}
                </data>

                <user_input>
                    {user_input}
                </user_input>

                <task>
                    Analyze the provided data to extract and summarize all key points relevant to the user's request.
                </task>

                
                <instructions>
                    - Ensure the summary is concise and directly addresses the user's needs.
                    - Maintain clarity and coherence in the summary.
                </instructions>
            """

        global_data.append(prompt(global_data_template))

        next_move = f"""

                Generate a Google search query based on the following data: \n {"\n ; ".join(global_data)} \n , 
                to get a best result for user needs. 
                Return only the query without any explanations or additional text.  


                <user>
                    {user_input}
                </user>

                <task>
                    Analyze the provided data and user input to generate a unique and effective search query that addresses the user's needs. Ensure this query is distinct from previous searches to avoid redundancy.
                </task>


                <search_history>
                    {"; ".join(search_history)}
                </search_history>

                <techniques>
                    - **Chain-of-Thought (CoT) Prompting**: Break down the analysis into a series of reasoning steps to systematically arrive at the search query. This approach enhances the model's reasoning capabilities by mimicking a train of thought.
                    - **Self-Consistency Decoding**: Generate multiple potential search queries and select the one that is most consistent across these iterations, ensuring reliability and effectiveness.
                </techniques>

                <instructions>
                    - Return only the query without any explanations or additional text
                    - Develop a concise and precise search query based on the analysis.
                    - Ensure the new query does not duplicate any listed in the search history.
                    - Maintain clarity and coherence in the query formulation.
                    - Adhere to a token limit of <20 word.
                </instructions>
                
                
            """
        
        search_data = prompt(next_move)

        search_history.append(search_data) # add the next move in search history to avoid redendance

    template = f"""
        <data>  
            {"; ".join(global_data)}  
        </data>  

        <role>  
            Act as an academic research expert with an exceptional ability to analyze, synthesize, and extract the most relevant insights from complex data.  
        </role>  

        Carefully analyze the provided data, understand its context, and generate the best possible answer that fully satisfies the user's request.  
        Do not mention or reference the provided data in the response. Present the answer naturally as if it was derived independently.  
        
        Also mention the source name or link if necessary to make the answer more valuable

        user : {user_input}

    """

    # all moves the ai decides
    print(
        f"""
        the history : \n
        {search_history}
        \n
        -------------------
        \n
        """
    )

    # last output
    print(prompt(template))

if __name__ == "__main__":
    asyncio.run(main())
