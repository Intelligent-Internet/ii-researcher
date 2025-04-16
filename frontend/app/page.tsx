"use client";

import { AnimatePresence, LayoutGroup, motion } from "framer-motion";
import { Copy, X } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import Markdown from "@/components/markdown";
import QuestionInput from "@/components/question-input";
import Think from "@/components/think";
import Thoughts from "@/components/thoughts";
import { Button } from "@/components/ui/button";
import { ThoughtStep, ThoughtType } from "@/typings/agent";

export default function Home() {
  const [question, setQuestion] = useState("");
  const [isInChatView, setIsInChatView] = useState(false);
  const [thoughtData, setThoughtData] = useState<ThoughtStep[]>([]);
  const [isStreamingThought, setIsStreamingThought] = useState(false);
  const [streamedResponse, setStreamedResponse] = useState("");
  const [eventSourceInstance, setEventSourceInstance] =
    useState<EventSource | null>(null);
  const [reasoningData, setReasoningData] = useState([""]);

  const [sources, setSources] = useState<{
    [key: string]: {
      url: string;
      result: {
        content: string;
      };
    };
  }>({});
  const modelType = "reasoning";

  const handleSubmit = () => {
    if (!question.trim()) return;

    setIsInChatView(true);
    setIsStreamingThought(true);

    const encodedQuestion = encodeURIComponent(question);
    const eventSource = new EventSource(
      `${
        process.env.NEXT_PUBLIC_API_URL
      }/search?question=${encodedQuestion}&is_reasoning=${
        modelType == "reasoning"
      }`
    );
    setEventSourceInstance(eventSource);
    if (eventSource) {
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          switch (data.type) {
            case ThoughtType.START:
            case ThoughtType.STEP:
            case ThoughtType.STEP_COMPLETED:
            case ThoughtType.KNOWLEDGE:
              break;
            case ThoughtType.TOOL:
              if (data.data.name == "web_search") {
                setThoughtData((prev) => [
                  ...prev,
                  {
                    type: ThoughtType.SEARCH,
                    data: {
                      queries: data.data.arguments.queries,
                    },
                    timestamp: data.data.timestamp,
                  },
                ]);
              }
              if (data.data.name == "page_visit") {
                setThoughtData((prev) => [
                  ...prev,
                  {
                    type: ThoughtType.VISIT,
                    data: {
                      urls: data.data.arguments.urls,
                    },
                    timestamp: data.data.timestamp,
                  },
                ]);
              }
              setReasoningData((prev) => [...prev, ""]);
              break;

            case ThoughtType.REASONING:
              setReasoningData((prev) => {
                const lastItem = prev[prev.length - 1];
                return [...prev.slice(0, -1), lastItem + data.data.reasoning];
              });
              break;

            case ThoughtType.VISIT:
              if (data.data.results) {
                const urlResultMap = data.data.results.reduce(
                  (
                    acc: Record<
                      string,
                      {
                        url: string;
                        result: {
                          content: string;
                        };
                      }
                    >,
                    item: {
                      url: string;
                      result: {
                        content: string;
                      };
                    },
                    index: number
                  ) => ({
                    ...acc,
                    [data.data.urls[index]]: item.result,
                  }),
                  {}
                );
                setSources((prev) => ({
                  ...prev,
                  ...urlResultMap,
                }));
                setThoughtData((prev) => [
                  ...prev,
                  {
                    type: ThoughtType.VISIT,
                    data: {
                      results: data.data.results.map(
                        (item: {
                          url: string;
                          result: { content: string };
                        }) => ({
                          url: item.url,
                          title: item.url,
                          description: item.result.content,
                        })
                      ),
                    },
                    timestamp: data.timestamp,
                  },
                ]);
              }
              break;

            case ThoughtType.WRITING_REPORT:
              setIsStreamingThought(false);
              setStreamedResponse(data.data.final_report);
              break;

            case "complete":
              setStreamedResponse(data.data.final_report);
              eventSource.close();
              break;
            default:
              setThoughtData((prev) => [...prev, data]);
              break;
          }
        } catch (error) {
          console.error("Error parsing SSE data:", error);
        }
      };

      eventSource.onerror = () => {
        toast.error("An error occurred");
        setIsStreamingThought(false);
        eventSource.close();
      };
    }
  };

  useEffect(() => {
    return () => {
      if (eventSourceInstance) {
        eventSourceInstance.close();
      }
    };
  }, [eventSourceInstance]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const resetChat = () => {
    eventSourceInstance?.close();
    setIsInChatView(false);
    setQuestion("");
    setThoughtData([]);
    setIsStreamingThought(false);
    setStreamedResponse("");
    setReasoningData([""]);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 dark:bg-slate-850">
      <div className="flex justify-between w-full">
        <div />
        <motion.h1
          className="text-4xl font-semibold mb-4 text-center"
          layout
          layoutId="page-title"
        >
          II-Researcher
        </motion.h1>
        {isInChatView ? (
          <Button className="cursor-pointer" onClick={resetChat}>
            <X className="size-5" />
          </Button>
        ) : (
          <div />
        )}
      </div>

      <LayoutGroup>
        <AnimatePresence mode="wait">
          {!isInChatView ? (
            <QuestionInput
              question={question}
              setQuestion={setQuestion}
              handleKeyDown={handleKeyDown}
              handleSubmit={handleSubmit}
            />
          ) : (
            <motion.div
              key="chat-view"
              initial={{ opacity: 0, y: 30, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -20, scale: 0.95 }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 30,
                mass: 1,
              }}
              className="w-full flex justify-center write-report rounded-2xl shadow-lg mt-6 overflow-hidden flex-1"
            >
              <motion.div
                className="p-4 w-full max-h-[calc(100vh-128px)] overflow-y-auto"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2, duration: 0.3 }}
              >
                {question && (
                  <motion.div
                    className="mb-4 text-right"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1, duration: 0.3 }}
                  >
                    <motion.div
                      className={`inline-block p-3 max-w-[80%] text-left rounded-lg bg-white text-black`}
                      initial={{ scale: 0.9 }}
                      animate={{ scale: 1 }}
                      transition={{
                        type: "spring",
                        stiffness: 500,
                        damping: 30,
                      }}
                    >
                      {question}
                    </motion.div>
                  </motion.div>
                )}
                {modelType !== "reasoning" && (
                  <Thoughts
                    isStreamingThought={isStreamingThought}
                    thoughtData={thoughtData}
                    sources={sources}
                  />
                )}

                {streamedResponse ? (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{
                      type: "spring",
                      stiffness: 300,
                      damping: 30,
                    }}
                    className={`inline-block p-4 rounded-lg text-md w-full bg-neutral-800 space-y-2 text-left relative`}
                  >
                    <Button
                      className="absolute top-4 right-4 cursor-pointer"
                      onClick={() => {
                        navigator.clipboard.writeText(streamedResponse);
                        toast.success("Copied to clipboard");
                      }}
                    >
                      <Copy className="size-4" />
                    </Button>
                    <Markdown>
                      {streamedResponse.replace(
                        /<url-(\d+)>/g,
                        (_, num) => sources[`<url-${num}>`]?.url || ""
                      )}
                    </Markdown>
                  </motion.div>
                ) : (
                  thoughtData.length > 0 &&
                  !isStreamingThought && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex items-center space-x-2 p-3 bg-neutral-800 rounded-lg w-fit"
                    >
                      <span className="text-sm text-gray-300">
                        Writing report
                      </span>
                      <span className="flex space-x-1">
                        {[0, 1, 2].map((i) => (
                          <motion.span
                            key={i}
                            className="w-1.5 h-1.5 bg-gray-300 rounded-full"
                            initial={{ opacity: 0.3 }}
                            animate={{ opacity: 1 }}
                            transition={{
                              repeat: Infinity,
                              repeatType: "reverse",
                              duration: 0.4,
                              delay: i * 0.15,
                            }}
                          />
                        ))}
                      </span>
                    </motion.div>
                  )
                )}
              </motion.div>

              {modelType == "reasoning" && reasoningData && (
                <motion.div className="w-[400px]">
                  <Think
                    data={reasoningData}
                    thoughtData={thoughtData}
                    sources={sources}
                    isStreamingThought={isStreamingThought}
                  />
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </LayoutGroup>
    </div>
  );
}
