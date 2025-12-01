
from src.dispatcher import InitialRequest, UserOutputData, SolveRequest, SolveResponse, UpdateOutput


async def on_startup(request: InitialRequest) -> list[SolveRequest]:
    requests = []
    for problem_group in request.problem_groups:
        for problem in problem_group.problems:
            for instance in problem.instances:
                for solver in problem_group.extras["solvers"]:
                    for _ in range(problem_group.extras["repetitions"]):
                        requests.append(
                            SolveRequest(
                                problem_id=problem.problem,
                                instance_id=instance,
                                solver_id=solver["id"],
                                vcpus=solver["vcpus"],
                            )
                        )
    return requests



async def on_update(response: SolveResponse) -> UpdateOutput:
    output_data: UserOutputData = {
        "solver_id": response["solver_id"],
        "problem_id": response["problem_id"],
        "instance_id": response["instance_id"],
        "result": response["result"],
        "vcpus": response["vcpus"],
    }

    return UpdateOutput(requests=[], output_data=output_data)