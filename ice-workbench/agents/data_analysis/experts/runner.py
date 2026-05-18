import asyncio
import json

from openai import AsyncOpenAI

from config import MODEL_EXPERT, API_BASE_URL, API_KEY, MAX_DEBATE_ROUNDS
from experts.prompts import (
    SQL_ENGINEER_PROMPT,
    DATA_ANALYST_PROMPT,
    BUSINESS_ADVISOR_PROMPT,
    REPORT_MERGE_PROMPT,
    CHALLENGE_PROMPT,
    RESPONSE_PROMPT,
    ARBITER_PROMPT,
    ENHANCED_REPORT_PROMPT,
)

client = AsyncOpenAI(base_url=API_BASE_URL, api_key=API_KEY)

EXPERT_ROLES = {
    "SQL工程师": SQL_ENGINEER_PROMPT,
    "数据分析师": DATA_ANALYST_PROMPT,
    "业务顾问": BUSINESS_ADVISOR_PROMPT,
}
ROLE_NAMES = list(EXPERT_ROLES.keys())


async def run_expert(role_name: str, system_prompt: str, context: str) -> dict:
    response = await client.chat.completions.create(
        model=MODEL_EXPERT,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context},
        ],
    )
    return {
        "role": role_name,
        "analysis": response.choices[0].message.content or "",
    }


async def run_expert_analysis(
    sql_used: str,
    csv_data: str,
    chart_paths: list[str],
    analysis_brief: str,
    analysis_package_summary: str = "",
) -> dict:
    shared_context = (
        f"## 分析目标\n\n{analysis_brief}\n\n"
        f"## 使用的 SQL\n\n```sql\n{sql_used}\n```\n\n"
        f"## 查询结果数据（CSV）\n\n```csv\n{csv_data}\n```\n\n"
        f"## 生成的图表\n\n" + "\n".join(f"- {p}" for p in chart_paths)
    )
    if analysis_package_summary:
        shared_context += f"\n\n## 分析引擎补充分析\n\n{analysis_package_summary}"

    sql_engineer_task = run_expert("SQL工程师", SQL_ENGINEER_PROMPT, shared_context)
    data_analyst_task = run_expert("数据分析师", DATA_ANALYST_PROMPT, shared_context)

    sql_result, analyst_result = await asyncio.gather(sql_engineer_task, data_analyst_task)

    advisor_context = (
        shared_context
        + f"\n\n## 数据分析师的初步发现\n\n{analyst_result['analysis']}"
    )
    advisor_result = await run_expert("业务顾问", BUSINESS_ADVISOR_PROMPT, advisor_context)

    return {
        "SQL工程师": sql_result["analysis"],
        "数据分析师": analyst_result["analysis"],
        "业务顾问": advisor_result["analysis"],
    }


async def _run_challenge_round(expert_outputs: dict) -> dict:
    challenges = {}
    for role in ROLE_NAMES:
        others = {k: v for k, v in expert_outputs.items() if k != role}
        other_names = list(others.keys())
        other_opinions = "\n\n".join(
            f"### {name} 的分析\n\n{text}" for name, text in others.items()
        )
        prompt = CHALLENGE_PROMPT.format(
            role=role,
            other_opinions=other_opinions,
            expert_a=other_names[0],
            expert_b=other_names[1],
        )
        result = await run_expert(role, EXPERT_ROLES[role], prompt)
        challenges[role] = result["analysis"]
    return challenges


async def _run_response_round(expert_outputs: dict, challenges: dict) -> dict:
    responses = {}
    for role in ROLE_NAMES:
        directed_challenges = []
        for challenger, text in challenges.items():
            if challenger != role and role in text:
                directed_challenges.append(f"### {challenger} 的质疑\n\n{text}")
        if not directed_challenges:
            for challenger, text in challenges.items():
                if challenger != role:
                    directed_challenges.append(f"### {challenger} 的质疑\n\n{text}")

        prompt = RESPONSE_PROMPT.format(
            role=role,
            challenges="\n\n".join(directed_challenges),
        )
        result = await run_expert(role, EXPERT_ROLES[role], prompt)
        responses[role] = result["analysis"]
    return responses


async def _run_arbiter(debate_transcript: str) -> dict:
    response = await client.chat.completions.create(
        model=MODEL_EXPERT,
        max_tokens=4096,
        messages=[
            {"role": "user", "content": ARBITER_PROMPT.format(debate_transcript=debate_transcript)},
        ],
    )
    text = (response.choices[0].message.content or "").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return {
        "converged": True,
        "consensus_conclusions": [],
        "disagreements": [],
        "final_recommendation": text,
        "confidence": "low",
    }


def _build_transcript(rounds: list[dict]) -> str:
    parts = []
    for i, rnd in enumerate(rounds, 1):
        parts.append(f"# Round {i}: {rnd['phase']}\n")
        for role, text in rnd["content"].items():
            parts.append(f"## {role}\n\n{text}\n")
    return "\n".join(parts)


async def run_debate(
    expert_outputs: dict,
    analysis_package_summary: str = "",
) -> dict:
    rounds = [{"phase": "Initial Opinions", "content": expert_outputs}]

    for debate_round in range(MAX_DEBATE_ROUNDS):
        challenges = await _run_challenge_round(expert_outputs)
        rounds.append({"phase": "Cross-Challenges", "content": challenges})

        responses = await _run_response_round(expert_outputs, challenges)
        rounds.append({"phase": "Responses", "content": responses})

        transcript = _build_transcript(rounds)
        verdict = await _run_arbiter(transcript)

        if verdict.get("converged", True):
            break

        expert_outputs = responses

    return {
        "rounds": rounds,
        "verdict": verdict,
        "debate_count": debate_round + 1,
    }


async def merge_expert_reports(
    expert_outputs: dict,
    sql_used: str,
    analysis_brief: str,
    analysis_package_summary: str = "",
    debate_result: dict | None = None,
) -> str:
    if debate_result and debate_result.get("verdict"):
        context = ENHANCED_REPORT_PROMPT.format(
            analysis_brief=analysis_brief,
            analysis_package=analysis_package_summary or "(无补充分析)",
            arbiter_verdict=json.dumps(debate_result["verdict"], ensure_ascii=False, indent=2),
            sql_used=sql_used,
        )
        response = await client.chat.completions.create(
            model=MODEL_EXPERT,
            max_tokens=8192,
            messages=[{"role": "user", "content": context}],
        )
        return response.choices[0].message.content or ""

    merge_context = (
        f"## 分析目标\n\n{analysis_brief}\n\n"
        f"## SQL 工程师分析\n\n{expert_outputs.get('SQL工程师', expert_outputs.get('sql_engineer', ''))}\n\n"
        f"## 数据分析师分析\n\n{expert_outputs.get('数据分析师', expert_outputs.get('data_analyst', ''))}\n\n"
        f"## 业务顾问分析\n\n{expert_outputs.get('业务顾问', expert_outputs.get('business_advisor', ''))}\n\n"
        f"## 使用的 SQL\n\n```sql\n{sql_used}\n```"
    )

    response = await client.chat.completions.create(
        model=MODEL_EXPERT,
        max_tokens=8192,
        messages=[
            {"role": "system", "content": REPORT_MERGE_PROMPT},
            {"role": "user", "content": merge_context},
        ],
    )
    return response.choices[0].message.content or ""
