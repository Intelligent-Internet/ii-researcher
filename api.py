import asyncio
import json
import logging
from typing import Any, Callable, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from ii_researcher.reasoning.agent import ReasoningAgent
from ii_researcher.utils.stream import StreamManager

app = FastAPI(
    title="Deep Search API", description="API for streaming Deep Search results"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


async def handle_reasoning_event(
    stream_event: Callable[[str, Dict[str, Any]], None], token: str
):
    if stream_event:
        print(token, end="", flush=True)
        await stream_event("reasoning", {"reasoning": token})
        await asyncio.sleep(0)


async def stream_generator(question: str, max_steps: int = 20):
    """Generate SSE events from the agent's search process"""
    stream_manager = StreamManager()

    search_task = None
    reasoning_agent = ReasoningAgent(
        question=question, stream_event=stream_manager.create_event_message
    )

    def handle_token(token):
        return asyncio.create_task(
            handle_reasoning_event(stream_manager.create_event_message, token)
        )

    search_task = asyncio.create_task(
        reasoning_agent.run(on_token=handle_token, is_stream=True)
    )

    try:
        while True:
            try:
                event = await asyncio.wait_for(stream_manager.queue.get(), timeout=1.0)
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"

            except asyncio.TimeoutError:
                if search_task.done():
                    if search_task.exception():
                        yield stream_manager.create_error_event(
                            str(search_task.exception())
                        )
                    try:
                        result = search_task.result()
                        yield stream_manager.create_complete_event(result)
                    except Exception:
                        pass
                    break
    finally:
        if not search_task.done():
            search_task.cancel()
            try:
                await search_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                print(f"Error during search task cancellation: {e}")

        if not search_task.done() or search_task.exception():
            yield stream_manager.create_close_event()


@app.get("/search")
async def stream_search(request: Request):
    """
    Stream search results in real-time

    This endpoint returns a Server-Sent Events (SSE) stream with updates from each step
    of the search process.
    """
    try:
        question = request.query_params.get("question", "")
        max_steps = int(request.query_params.get("max_steps", "10"))

        if not question:
            return {"error": "Question is required"}

        return StreamingResponse(
            stream_generator(question, max_steps),
            media_type="text/event-stream",
        )
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
