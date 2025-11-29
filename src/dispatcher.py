from dataclasses import asdict, dataclass
import json
import logging
from typing import Any, Callable, TypeAlias
import aio_pika
from dacite import from_dict
from src.config import Config

logger = logging.getLogger(__name__)

# @dataclass  
# class Solver:
#     id: int
#     vcpus: int
    
@dataclass
class Problem:
    problem: int
    instances: list[int]
    
@dataclass
class ProblemGroup:
    problem_group: int
    # solvers: list[Solver]
    problems: list[Problem]
    extras: dict[str, Any]

@dataclass
class InitialRequest:
    problem_groups: list[ProblemGroup]
        
@dataclass
class SolveRequest:
    problem_id: int
    instance_id: int
    solver_id: int
    vcpus: int


SolveResponse: TypeAlias = dict[str, Any]

UserOutputData: TypeAlias = dict[str, Any]

@dataclass    
class ActualOutputData:
    project_id: str
    solver_id: int
    problem_id: int
    instance_id: int
    vcpus: int
    result: UserOutputData


@dataclass
class UpdateOutput:
    requests: list[SolveRequest]
    output_data: UserOutputData

@dataclass
class DispatcherMetrics:
    total_requests: int = 0
    received: int = 0


async def result_collector(on_update: Callable[[SolveResponse], UpdateOutput], metrics: DispatcherMetrics):
    logger.info(f"Starting result collector, listening to queue: {Config.PROJECT_SOLVER_RESULT_QUEUE}")
    result_queue = Config.PROJECT_SOLVER_RESULT_QUEUE
    director_queue = Config.DIRECTOR_QUEUE
    controller_queue = Config.CONTROL_QUEUE
    output_queue = Config.SOLVER_DIRECTOR_RESULT_QUEUE
    project_id = Config.PROJECT_ID
    
    connection = await aio_pika.connect_robust(
        host=Config.RabbitMQ.HOST,
        port=Config.RabbitMQ.PORT,
        login=Config.RabbitMQ.USER,
        password=Config.RabbitMQ.PASSWORD,
    )
    
    async with connection:  
        channel = await connection.channel()
        queue = await channel.declare_queue(result_queue, durable=True)
        await channel.declare_queue(director_queue, durable=True)
        await channel.declare_queue(controller_queue, durable=True)
        exchange = channel.default_exchange
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    logger.info("Received result message")
                    result_data = message.body.decode()
                    result_json = json.loads(result_data)
                    result = await on_update(result_json)
                    response = ActualOutputData(
                        project_id=project_id,
                        solver_id=result_json["solver_id"],
                        problem_id=result_json["problem_id"],
                        instance_id=result_json["instance_id"],
                        vcpus=result_json["vcpus"],
                        result=result.output_data,
                    )
                    response = asdict(response)

                    for request in result.requests:
                        body = json.dumps(asdict(request)).encode()
                        
                        await exchange.publish(
                            aio_pika.Message(
                                body=body,
                                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                            ),
                            routing_key=controller_queue
                        )
                        metrics.total_requests += 1
                        
                        
                    if metrics.total_requests != 0 and metrics.total_requests-metrics.received == 1:
                        response["final_message"] = True
                        response["total_messages"] = metrics.total_requests
                    
                    body = json.dumps(response).encode()

                    await exchange.publish(
                        aio_pika.Message(
                            body=body,
                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                        ),
                        routing_key=output_queue
                    )
                    
                    metrics.received += 1
                    logger.info("Result processed and dispatched.")
                    
                    
    

async def initial_dispatcher(process_initial_request: Callable[[InitialRequest], list[SolveRequest]], metrics: DispatcherMetrics):

    controller_queue = Config.CONTROL_QUEUE
    director_queue = Config.DIRECTOR_QUEUE

    logger.info(f"Starting dispatcher, listening to queue: {director_queue}")

    connection = await aio_pika.connect_robust(
        host=Config.RabbitMQ.HOST,
        port=Config.RabbitMQ.PORT,
        login=Config.RabbitMQ.USER,
        password=Config.RabbitMQ.PASSWORD,
    )
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(director_queue, durable=True)
        exchange = channel.default_exchange
        controller_queue = Config.CONTROL_QUEUE
        await channel.declare_queue(controller_queue, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    text = message.body.decode()
                    json_message = json.loads(text)
                    initial_request = from_dict(InitialRequest, json_message)
                    logger.info(f"received request {initial_request}")
                    tasks = await process_initial_request(initial_request)
                    logger.info(f"received request processed {tasks}")

                    for task in tasks:
                        metrics.total_requests += 1
                        body = json.dumps({"task": asdict(task)}).encode()

                        await exchange.publish(
                            aio_pika.Message(
                                body=body,
                                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                            ),
                            routing_key=controller_queue
                        )
    logger.info(f"Initial dispatcher in {Config.PROJECT_ID} Done.")

