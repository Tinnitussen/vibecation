## 3. Trip Brainstorm Page (`/trips/{tripID}/brainstorm`)

### Layout
- **Split Layout**: 
  - **Left Side (60%)**: Activity cards visualization
  - **Right Side (40%)**: Chat interface

------
## Unified Endpoint: `/trip_brinstorm`

The brainstorm functionality uses a single unified endpoint that handles both initial trip generation and iteration.

### Endpoint Behavior

- **First Message**: When `old_plan` is empty JSON (`{}`), the endpoint generates an initial trip plan.
- **Subsequent Messages**: When `old_plan` contains existing plan data (JSON string of VibecationDay array), the endpoint iterates on the existing plan.

### Implementation

Use the following python components:

```python
from pydantic import BaseModel, Field
import openai
import json

class Trip(BaseModel):
    """
    Model representing a complete trip itinerary.
    """
    trip_name: str = Field(..., description="Name of the trip")
    trip_id: str = Field(..., description="Unique identifier for the trip")
    activities: List[Activity] = Field(..., description="List of activities in the trip")
    trip_summary = Field(..., description="A comprehensive description of the trip and activities")

# Parse old_plan parameter  # Iteration on existing plan
old_trip_json = json.dumps(old_plan_json)
prompt = query + "\n\nOld trip\n\n" + old_trip_json

async_client = openai.AsyncClient()
model = 'gpt-4.1'
autotuning_res = await async_client.responses.parse(
    model=model,
    input=[
        {
            "role": "system",
            "content": "You are a helpful assistant and a expert trip planner",
        },
        {"role": "user", "content": prompt},
    ],
    text_format=Trip,
)
```

### Frontend Implementation

- **First message**: Send `old_plan` as empty JSON string: `"{}"`
- **Subsequent messages**: Send `old_plan` as JSON string of current days array: `JSON.stringify(days)`