import os
import glob
import yaml
from dotenv import load_dotenv
from typesafe_sdk import Choice, TypeSafeClient
from crewai import Agent, Task, Crew, LLM

load_dotenv()

KNOWLEDGE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "company-knowledge")
SIMPLE_MODEL = "gpt-5.4-mini"   
SUPER_MODEL = "gpt-5.4"        
MIN_CONFIDENCE = 0.7           

docs = {}

for path in glob.glob(KNOWLEDGE_FOLDER + "/**/*.md", recursive=True):
    text = open(path, encoding="utf-8").read()
    frontmatter = text.split("---")[1]
    meta = yaml.safe_load(frontmatter)

    key = os.path.basename(path).replace(".md", "").replace("-", "_")
    docs[key] = {"path": path, "meta": meta, "text": text}

print("Loaded", len(docs), "OKF files:", list(docs.keys()))

while True:
    question = input("\nAsk a question (or type 'exit'): ").strip()

    if question.lower() == "exit":
        break
    if question == "":
        continue

    file_options = {}
    for key in docs:
        file_options[key] = docs[key]["meta"]["description"]
    file_options["none"] = "No knowledge file is relevant to this question"

    with TypeSafeClient() as client:
        result = client.system_one(
            state=question,
            questions={
                "doc": Choice(
                    instructions="Which knowledge file best helps answer this question?",
                    criteria=file_options,
                ),
                "level": Choice(
                    instructions="How hard is this question?",
                    criteria={
                        "simple": "A short fact, definition or quick lookup",
                        "super": "Needs analysis, planning, comparison, code or many steps",
                    },
                ),
            },
        )

    picked_file = result.answers["doc"]
    picked_level = result.answers["level"]

    print("\n[Jev] File :", picked_file.choice, "| confidence:", round(picked_file.confidence, 2))
    print("[Jev] Level:", picked_level.choice, "| confidence:", round(picked_level.confidence, 2))


    if picked_level.choice == "super":
        model = SUPER_MODEL
    else:
        model = SIMPLE_MODEL

    if picked_file.choice != "none" and picked_file.confidence >= MIN_CONFIDENCE:
        files_to_read = [picked_file.choice] + docs[picked_file.choice]["meta"].get("links", [])
    else:
        files_to_read = list(docs.keys())

    knowledge = ""
    for key in files_to_read:
        if key in docs:
            knowledge = knowledge + "\n\n===== FILE: " + key + " =====\n" + docs[key]["text"]

    print("[Route] Model:", model)
    print("[Route] Files:", files_to_read)

    agent = Agent(
        role="Company Data Assistant",
        goal="Answer questions using ONLY the company knowledge files you are given",
        backstory="You follow the company's definitions exactly. If the answer is not in the files, you say so and never guess.",
        llm=LLM(model=model, temperature=0.2),
    )

    task = Task(
        description="Question: " + question + "\n\nCompany knowledge files:" + knowledge,
        expected_output="A clear, correct answer that names which knowledge files it used",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task])
    answer = crew.kickoff()

    print("\n========== ANSWER ==========")
    print(answer.raw)
