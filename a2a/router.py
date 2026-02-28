import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import StatusCode, Status 

from a2a import envelope
from handlers.agent import handler_train, handler_action
from exception.exceptions import A2ARouterError

#---------------------------------
# Configure logging
#---------------------------------
tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)

#---------------------------------
# A2A Router
class A2ARouter:

    def route(self, envelope):
        with tracer.start_as_current_span("a2a.route") as span:
            logger.info("def.route()")  

            try:
                if envelope.message_type == "TRAIN":
                    return handler_train(envelope.payload)
                elif envelope.message_type == "ACTION":
                    return handler_action(envelope.payload)
                else:
                    message = f"Unsupported message type: {envelope.message_type}"
                    e = A2ARouterError(message)
                    raise e

            except A2ARouterError as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                logger.error("Error clustering data", exc_info=e)
                raise e

            except Exception as e:
                logger.error("Error clustering data", exc_info=e)
                raise e
