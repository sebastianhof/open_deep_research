from bedrock_agentcore.runtime import BedrockAgentCoreApp
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from open_deep_research.deep_researcher import deep_researcher_builder

app = BedrockAgentCoreApp()

graph = deep_researcher_builder.compile(checkpointer=MemorySaver())

@app.entrypoint
async def invoke_agent(request, context):
    user_msg = request.get("prompt", "No prompt found in input, please guide customer as to what tools can be used")

    stream = graph.astream(
        {
            "messages": [HumanMessage(content=user_msg)]
        },
        config={
            "configurable": {
                "thread_id": context.session_id,
            }
        },
        stream_mode="updates"
    )

    async for event in stream:
        yield event

if __name__ == "__main__":
    app.run()