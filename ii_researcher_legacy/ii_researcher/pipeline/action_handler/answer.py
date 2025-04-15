from baml_client.async_client import b
from baml_client.types import Answer, KnowledgeItem, KnowledgeType
from ii_researcher_legacy.ii_researcher.events import Event
from ii_researcher_legacy.ii_researcher.pipeline.action_handler.base import ActionHandler
from ii_researcher_legacy.ii_researcher.pipeline.evaluator import evaluate_answer
from ii_researcher_legacy.ii_researcher.pipeline.schemas import ActionWithThinkB, Reference
from ii_researcher_legacy.ii_researcher.utils.prompt import (
    ANSWER_BAD_PROMPT,
    ANSWER_GOOD_PROMPT,
    ANSWER_SUBQUESTION_PROMPT,
)
from ii_researcher_legacy.ii_researcher.utils.text_tools import choose_k


class AnswerHandler(ActionHandler):

    async def handle(self, action_with_think: ActionWithThinkB) -> None:
        """
        Handle an answer action
        """
        assert isinstance(action_with_think.action, Answer)
        action = action_with_think.action

        if self.state.step == 1:
            # LLM is so confident and answer immediately, skip all evaluations
            self.state.is_final = True
            return

        print(f"Answer: {action.answer_text[:100]}...")
        await self._send_event(
            Event.DRAFT_ANSWER.value,
            {
                "answer": action.answer_text,
                "is_final": self.state.is_final
            },
        )

        # Normalize references
        normalized_refs = []
        if action.references:
            for ref in action.references:
                normalized_refs.append(
                    Reference(
                        exactQuote=ref.exactQuote,
                        title=(self.state.all_urls[ref.url]["title"] if ref.url in self.state.all_urls else ""),
                        url=self.state.get_actual_url(ref.url),
                    ))
            action.references = normalized_refs

        # evaluate the answer
        evaluation = await evaluate_answer(
            question=self.state.current_question,
            action=action,
            evaluation_types=self.state.evaluation_metrics[self.state.current_question],
            visited_urls=self.state.visited_urls,
        )

        if (self.state.current_question.strip() == self.state.question):  # if the answer is the final answer
            if evaluation.pass_evaluation:
                step_diary = ANSWER_GOOD_PROMPT.format(
                    step=self.state.step,
                    question=self.state.question,
                    answer_text=action.answer_text,
                    evaluation_think=evaluation.think,
                )
                self._add_to_diary(step_diary)

                self.state.is_final = True

                await self._send_event(
                    Event.EVAL_ANSWER.value,
                    {
                        "thinking": f"The evaluator thinks the answer is good because: {evaluation.think}",
                        "is_final": self.state.is_final,
                    },
                )

                self.state.final_references = action.references  # for report generation

                return
            # if not pass
            if self.state.bad_attempts >= self.state.config.max_bad_attempts:
                return

            step_diary = ANSWER_BAD_PROMPT.format(
                step=self.state.step,
                question=self.state.question,
                answer_text=action.answer_text,
                evaluation_think=evaluation.think,
            )
            self._add_to_diary(step_diary)

            await self._send_event(
                Event.EVAL_ANSWER.value,
                {
                    "thinking": f"The evaluator thinks the answer is bad because: {evaluation.think}",
                    "is_final": self.state.is_final,
                },
            )

            # store the bad context and reset the diary context
            error_analysis = await b.AnalyzeSteps(
                diary_context=self.state.diary_context,
            )

            self.state.bad_context.append({
                "question": self.state.current_question,
                "answer": action.answer_text,
                "evaluation": evaluation.think,
                **error_analysis.model_dump(),
            })

            if error_analysis.next_search:
                # reranker? maybe
                error_analysis.next_search = choose_k(
                    error_analysis.next_search,
                    self.state.config.max_reflect_per_step,
                )
                self.state.gaps.extend(error_analysis.next_search)
                self.state.all_questions.extend(error_analysis.next_search)
                self.state.gaps.append(self.state.question)
            else:  # if not need to search again, allow answer only
                self.state.allow_answer = True
                self.state.allow_read = False
                self.state.allow_search = False
                self.state.allow_reflect = False

            self.state.bad_attempts += 1
            self.state.allow_answer = (
                False  # disable answer action in the immediate next step
            )
            self.state.diary_context.clear()
            self.state.step = 0
            return

        if (evaluation.pass_evaluation):  # if the answer is not the final answer and pass the evaluation
            step_diary = ANSWER_SUBQUESTION_PROMPT.format(
                step=self.state.step,
                current_question=self.state.current_question,
                answer_text=action.answer_text,
                evaluation_think=evaluation.think,
            )
            self._add_to_diary(step_diary)

            await self._add_to_knowledge(
                KnowledgeItem(
                    question=self.state.current_question,
                    answer=action.answer_text,
                    references=([a.model_dump() for a in action.references] if action.references else []),
                    type=KnowledgeType.QA,
                    updated=self._get_current_date(),
                ))

        else:  # if the answer is not the final answer and not pass the evaluation
            pass
