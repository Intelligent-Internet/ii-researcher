from baml_client.async_client import b
from baml_client.types import Reflect
from ii_researcher_legacy.ii_researcher.pipeline.action_handler.base import ActionHandler
from ii_researcher_legacy.ii_researcher.pipeline.schemas import ActionWithThinkB
from ii_researcher_legacy.ii_researcher.utils.prompt import REFLECT_DUPLICATE_PROMPT, REFLECT_SUCCESS_PROMPT
from ii_researcher_legacy.ii_researcher.utils.text_tools import choose_k


class ReflectHandler(ActionHandler):

    async def handle(self, action_with_think: ActionWithThinkB) -> None:
        """
        Handle a reflect action
        """
        assert isinstance(action_with_think.action, Reflect)
        action = action_with_think.action

        dedup_result = await b.DedupQueries(
            new_queries=action.questions_to_answer,
            existing_queries=self.state.all_questions,
        )
        questions = choose_k(dedup_result.unique_queries, self.state.config.max_reflect_per_step)

        if len(questions) > 0:
            step_diary = REFLECT_SUCCESS_PROMPT.format(
                step=self.state.step,
                current_question=self.state.current_question,
                sub_questions="\n".join([f"- {q}" for q in questions]),
            )
            self._add_to_diary(step_diary)

            self.state.gaps.extend(questions)
            self.state.all_questions.extend(questions)
            self.state.gaps.append(self.state.question)

        else:
            step_diary = REFLECT_DUPLICATE_PROMPT.format(
                step=self.state.step,
                current_question=self.state.current_question,
            )

            self.state.allow_reflect = False
