import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import StatusCode, Status 

from config.config import settings
from exception.exceptions import A2ARouterError

from a2a.router import A2ARouter
from a2a.envelope import A2AEnvelope
from a2a.agent_card import AGENT_CARD

#---------------------------------
# Configure logging
#---------------------------------
tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)

# -----------------------------------------
class ClusteringAgent:

    NAME = settings.APP_NAME
    VERSION = settings.VERSION

    def __init__(self):
        self.capabilities = AGENT_CARD
        self.router = A2ARouter()
        self.msg_type = ""
        
    def receive(self, envelope: A2AEnvelope) -> A2AEnvelope:
        with tracer.start_as_current_span("agent.receive") as span:
            """Main entry point for all incoming messages."""
            logger.info("def.receive()") 
            logger.debug("envelope: %s", envelope)

            try:
                result = self.router.route(envelope)

                if envelope.message_type == "TRAIN":
                    self.msg_type = "TRAIN_RESULT"
                elif envelope.message_type == "ACTION":
                    self.msg_type = "ACTION_RESULT"
                else:
                    self.msg_type = "NO_ROUTER"

                return A2AEnvelope.create(
                    source=self.NAME,
                    target=envelope.source_agent,
                    msg_type=self.msg_type ,
                    payload=result
                )
            
            except A2ARouterError:
                # Propagate known router errors so controller can return 400
                raise
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                logger.error(f"Error processing envelope: {e}")
                raise e