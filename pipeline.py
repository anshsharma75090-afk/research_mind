from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain

def run_research_pipeline(topic:str) -> dict:
    state = {}
    # Step 1: Search Agent
    print("\n"+" ="*50)
    print('step1 - Search Agent')
    print("="*50)
    
    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        'messages':[('user',f'find recent,reliable and detailed information about:{topic}')]
    })
    state['search_results'] = search_result['messages'][-1].content
    
    print('\n search results',state['search_results'])
    
    #step 2
    print("\n"+" ="*50)
    print('step2 - Reader Agent')
    print("="*50)
    
    reader_agent = build_reader_agent()
    reader_results = reader_agent.invoke({
                'messages' : [('user',
                    f"based on the following search results about {topic}, "
                    f"pick the most relevant URL and scrape it for deeper content.\n\n"
                    f"Search Results:\n{state['search_results'][:800]}"
                )]
    })
    
    state['scraped_content'] = reader_results['messages'][-1].content
    print('\n scraped content\n',state['scraped_content'])
    
    # step 3 - writer chain
    print("\n"+" ="*50)
    print('step3 - writer chain combined search results')
    print("="*50)
    
    research_combined = (
        f"SEARCH RESULTS: \n{state['search_results']}\n\n"
        f"DETAILED SCRAPED CONTENT: \n {state['scraped_content']}"   
    )
    
    state['report'] = writer_chain.invoke({
        'topic': topic,
        'research' : research_combined
    })
    
    print("\n Final Report\n",state['report'])
    
    #critic report
    print("\n"+" ="*50)
    print('step4- Search Agent')
    print("="*50)
    
    state['feedback'] = critic_chain.invoke({
        'report': state['report']
    })
    
    print('\n critic report \n',state['feedback'])
    
    return state
    
    
if __name__ =="__main__":
   topic = input('\n Enter a research topic:')
   run_research_pipeline(topic)
