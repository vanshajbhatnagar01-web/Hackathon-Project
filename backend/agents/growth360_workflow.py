
import subprocess
import sys
import operator

from pathlib import Path
from typing import TypedDict, Annotated

from langgraph.graph import StateGraph, START, END




class Growth360State(TypedDict):
    completed_agents: Annotated[list[str], operator.add]
    agent_outputs: Annotated[list[str], operator.add]



project_folder = Path(__file__).resolve().parents[2]




def run_agent(agent_name, file_name):

    print("\n" + "=" * 55)
    print(f"Running {agent_name}")
    print("=" * 55)

    agent_file = (
        project_folder / "backend" / "agents" / file_name
    )

   
    if not agent_file.exists():
        raise FileNotFoundError(
            f"Agent file not found: {agent_file}"
        )

   
    result = subprocess.run(
        [sys.executable, str(agent_file)],
        cwd=project_folder,
        capture_output=True,
        text=True
    )

    
    print(result.stdout)

    # Check for errors
    if result.returncode != 0:

        print("\nAgent Error:")
        print(result.stderr)

        raise RuntimeError(
            f"{agent_name} failed!"
        )

    
    return {
        "completed_agents": [agent_name],
        "agent_outputs": [
            f"{agent_name}:\n{result.stdout}"
        ]
    }




def review_node(state):

    return run_agent(
        "Review Agent",
        "review_agent.py"
    )


def demand_node(state):

    return run_agent(
        "Demand Agent",
        "demand_agent.py"
    )


def doctor_node(state):

    return run_agent(
        "Business Doctor",
        "business_doctor.py"
    )


def gemini_doctor_node(state):

    return run_agent(
        "Gemini Business Doctor",
        "business_doctor_gemini.py"
    )


def marketing_node(state):

    return run_agent(
        "Marketing Agent",
        "marketing_agent.py"
    )


def gemini_marketing_node(state):

    return run_agent(
        "Gemini Marketing Agent",
        "marketing_agent_gemini.py"
    )




workflow = StateGraph(Growth360State)



workflow.add_node("review", review_node)
workflow.add_node("demand", demand_node)
workflow.add_node("doctor", doctor_node)
workflow.add_node("gemini_doctor", gemini_doctor_node)
workflow.add_node("marketing", marketing_node)
workflow.add_node("gemini_marketing", gemini_marketing_node)



workflow.add_edge(START, "review")

workflow.add_edge("review", "demand")

workflow.add_edge("demand", "doctor")

workflow.add_edge("doctor", "gemini_doctor")

workflow.add_edge("gemini_doctor", "marketing")

workflow.add_edge("marketing", "gemini_marketing")

workflow.add_edge("gemini_marketing", END)



growth360_graph = workflow.compile()




if __name__ == "__main__":

    print("\nGROWTH360 INTELLIGENT AI WORKFLOW STARTED")
    print("=" * 55)

    initial_state = {
        "completed_agents": [],
        "agent_outputs": []
    }

    
    final_state = growth360_graph.invoke(initial_state)

  
    print("\n" + "=" * 55)
    print("GROWTH360 WORKFLOW COMPLETED SUCCESSFULLY!")
    print("=" * 55)

    print("\nAGENTS COMPLETED:")

    for agent in final_state["completed_agents"]:
        print(f"[SUCCESS] {agent}")

    print("\nTotal agents completed:",
          len(final_state["completed_agents"]))

    print("Total agent outputs stored:",
          len(final_state["agent_outputs"]))

    print("\nAll six stages have finished.")
    print("Growth360 has generated business reports and AI campaigns.")
