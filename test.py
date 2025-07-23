import boto3
import json
import uuid

account_id = '861976376325'
region = 'us-east-1'
agentcore_id = 'open_research_agent-eMPR6V2ANq'  # This is the ID of your deployed agent

client = boto3.client('bedrock-agentcore', region_name=region)
session_id = f'user-session-{uuid.uuid4().hex}'

try:
    while True:
        prompt = input("Enter prompt (CTRL+C to exit): ")
        if not prompt.strip():
            continue
            
        response = client.invoke_agent_runtime(
            agentRuntimeArn=f"arn:aws:bedrock-agentcore:{region}:{account_id}:runtime/{agentcore_id}",
            qualifier="DEFAULT",
            runtimeSessionId=session_id,
            payload=json.dumps({"prompt": prompt}).encode() 
        )

        if "text/event-stream" in response.get("contentType", ""):
            # Handle streaming response
            content = []
            for line in response["response"].iter_lines(chunk_size=10):
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        line = line[6:]
                        print(line)
                        content.append(line)
            print("\nComplete response:", "\n".join(content))

        elif response.get("contentType") == "application/json":
            # Handle standard JSON response
            content = []
            for chunk in response.get("response", []):
                content.append(chunk.decode('utf-8'))
            print(json.loads(''.join(content)))
          
        else:
            # Print raw response for other content types
            print(response)
            
except KeyboardInterrupt:
    print("\nGoodbye!")