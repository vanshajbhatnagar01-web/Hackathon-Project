

import subprocess
import sys
from pathlib import Path

from typing import TypedDict
from langgraph.graph import StateGraph, START, END



class Growth360State(TypedDict):
    completed_agents: list




project_folder = Path(__file__).resolve().parents[2]




def run_agent(agent_name, file_name, state):

    print("\n" + "=" * 50)
    print(f"Running {agent_name}")
    print("=" * 50)

    agent_file = project_folder / "backend" / "agents" / file_name

    result = subprocess.run(
        [sys.executable, str(agent_file)],
        cwd=project_folder,
        capture_output=True,
        text=True
    )

    
    print(result.stdout)

    
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(f"{agent_name} failed!")

   
    completed_agents = state["completed_agents"] + [agent_name]

    return {"completed_agents": completed_agents}



def review_node(state):
    return run_agent(
        "Review Agent",
        "review_agent.py",
        state
    )


def demand_node(state):
    return run_agent(
        "Demand Agent",
        "demand_agent.py",
        state
    )


def doctor_node(state):
    return run_agent(
        "Business Doctor",
        "business_doctor.py",
        state
    )


def marketing_node(state):
    return run_agent(
        "Marketing Agent",
        "marketing_agent.py",
        state
    )




workflow = StateGraph(Growth360State)


workflow.add_node("review", review_node)
workflow.add_node("demand", demand_node)
workflow.add_node("doctor", doctor_node)
workflow.add_node("marketing", marketing_node)


workflow.add_edge(START, "review")
workflow.add_edge("review", "demand")
workflow.add_edge("demand", "doctor")
workflow.add_edge("doctor", "marketing")
workflow.add_edge("marketing", END)


growth360_graph = workflow.compile()




if __name__ == "__main__":

    print("\nGrowth360 AI WORKFLOW STARTED")
    print("-" * 50)

    initial_state = {
        "completed_agents": []
    }

    
    final_state = growth360_graph.invoke(initial_state)

  
    print("\n" + "=" * 50)
    print("GROWTH360 WORKFLOW COMPLETED!")
    print("=" * 50)

    print("\nAgents completed successfully:")

    for agent in final_state["completed_agents"]:
        print(f"[SUCCESS] {agent}")

    print("\nAll four agents have finished running.")
    print("Growth360 has generated updated business reports and campaigns.")
