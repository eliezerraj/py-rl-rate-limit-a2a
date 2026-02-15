import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import StatusCode, Status 

from service.reinforced import ReinforcedService

#---------------------------------
# Configure logging
#---------------------------------
tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)

# Initialize Clustering Service
reinforce_service = ReinforcedService()

# Handlers
def handler_train(payload: dict) -> dict:
    with tracer.start_as_current_span("handler.handler_train") as span:
        logger.info("def.handler_train()")  
        logger.debug("payload: %s", payload)

        try:
            data_train = payload["data"]
            result = reinforce_service.train_model(data=data_train)
            return result

        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            logger.error("Error train reinforced data", exc_info=e)
            raise e

def handler_action(payload: dict) -> dict:
    with tracer.start_as_current_span("handler.handler_action") as span:
        logger.info("def.handler_action()")  
        logger.debug("payload: %s", payload)

        try:
            data_action = payload["data"]
            result = reinforce_service.action(data=data_action)
            return result

        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            logger.error("Error action reinforced data", exc_info=e)
            raise e