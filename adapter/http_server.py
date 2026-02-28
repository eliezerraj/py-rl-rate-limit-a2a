import logging
import time

from log.logger import setup_logger
from tracing.tracer import setup_tracer

from agent import ClusteringAgent
from a2a.envelope import A2AEnvelope
from config.config import settings
from exception.exceptions import A2ARouterError, KmeansError

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi import status

from contextlib import asynccontextmanager

from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

#---------------------------------
# Initialize variables from environment
#---------------------------------
print("---" * 15)
print(f"VERSION: {settings.VERSION}")
print(f"ACCOUNT: {settings.ACCOUNT}")
print(f"APP_NAME: {settings.APP_NAME}")
print(f"HOST: {settings.HOST}")
print(f"PORT: {settings.PORT}")
print(f"SESSION_TIMEOUT: {settings.SESSION_TIMEOUT}")
print(f"OTEL_EXPORTER_OTLP_ENDPOINT: {settings.OTEL_EXPORTER_OTLP_ENDPOINT}")
print(f"LOG_LEVEL: {settings.LOG_LEVEL}")
print(f"OTEL_STDOUT_LOG_GROUP: {settings.OTEL_STDOUT_LOG_GROUP}")
print(f"LOG_GROUP: {settings.LOG_GROUP}")
print("---" * 15)

#---------------------------------
# Configure logging
#---------------------------------
setup_logger(settings.LOG_LEVEL, settings.APP_NAME, settings.OTEL_STDOUT_LOG_GROUP, settings.LOG_GROUP)
logger = logging.getLogger(__name__)

# ---------------------------------
# Lifespan (startup/shutdown)
# ---------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """ Load the ML model """
    logger.info(" **** Starting up the application...")
    yield
    logger.info(" **** Shutting down the application...")
    logger.info(" **** Closing resources (5 seconds)...")
    time.sleep(0)
    logger.info(" **** Resources Closed...")
    logger.info(" **** Shutting down complete, bye ...")

# ---------------------------------
# Create FastAPI instance
# ---------------------------------
app = FastAPI(
    title="Kmeans API",
    version="1.0.0",
    lifespan=lifespan
)

#---------------------------------
# Configure tracer
#---------------------------------
setup_tracer(settings.APP_NAME, settings.OTEL_EXPORTER_OTLP_ENDPOINT)
tracer = trace.get_tracer(__name__)

# Instrument FastAPI + requests
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()

agent = ClusteringAgent()

# ---------------------------------------------------------------
# methods to handle API requests
# ---------------------------------------------------------------
@app.get("/info")
def get_info():
    with tracer.start_as_current_span("controller.get_info"):
        """Get application settings information."""
        logger.info("func.get_info()")

        return settings

@app.get("/.well-known/agent.json")
def agent_card():
    with tracer.start_as_current_span("controller.get_agent_card"):
        """Get application agent card information."""
        logger.info("func.get_agent_card()")
        
        return agent.capabilities
    
@app.post("/a2a/message")
def handle_message(envelope: A2AEnvelope):
    with tracer.start_as_current_span("controller.handle_message") as span:
        """Handle an A2A message."""
        logger.info("func.handle_message()")
    
        try:
            result = agent.receive(envelope)
            span.set_status(Status(StatusCode.OK))
            return result

        except KmeansError as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            logger.error(f"Error handling message: {e}")
            return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except A2ARouterError as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            logger.warning(f"Bad request: {e}")
            return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            logger.error(f"Error handling message: {e}")
            return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)