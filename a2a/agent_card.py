from config.config import settings

AGENT_CARD = {
    "name": settings.APP_NAME,
    "version": settings.VERSION,
    "url": settings.URL_AGENT,
    "version": "v1",
    "protocol": "a2a/1.0",
    "description": "Reinforced Learn agent (tps data analysis)",
    "maintainer": {
        "contact": "eliezerral@gmail.com",
        "organization": "MLOps"
    },
    "capabilities": [
        {
            "intent": "REINFORCED_LEARN_ANALYSIS",
            "consumes": ["TRAIN"],
            "produces": ["ACTION"],
            "input_modes": ["application/json"],
            "output_modes": ["application/json"],
            "schema": {
                "type": "object",
                "properties": { 
                    "data": { "type": "array" , "items": { "type": "number" },
                    },
                },
                "required": ["data","limit"]
            },
        },
    ],
    "skills": {
        "train": "Train a model based in bellman equation",
        "action": "Show the best action for a given scenario",
    },
    "endpoints": {
        "message": "/a2a/message",
        "health": "/info",
    },
    "security": {
        "type": "none", 
        "description": "Localhost testing mode"
    }
}
