import json
from datetime import datetime, timedelta
import asyncio
from .business_logic import (
    get_farmer,
    # get_customer_appointments,
    # get_customer_orders,
    register_farmer,
    # get_available_appointment_slots,
    prepare_agent_filler_message,
    prepare_farewell_message,
)


async def find_farmer(params):
    print(f'looked in farmers {params}')
    """Look up a customer by phone, email, or ID."""
    national_id = params.get("national_id")
    

    result = await get_farmer(national_id=national_id)
    return result


# async def get_appointments(params):
#     """Get appointments for a customer."""
#     customer_id = params.get("customer_id")
#     if not customer_id:
#         return {"error": "customer_id is required"}

#     result = await get_customer_appointments(customer_id)
#     return result


# async def get_orders(params):
#     """Get orders for a customer."""
#     customer_id = params.get("customer_id")
#     if not customer_id:
#         return {"error": "customer_id is required"}

#     result = await get_customer_orders(customer_id)
#     return result


async def create_farmer(params):
    """Schedule a new appointment."""
    national_id = params.get("national_id")
    name = params.get("name")
    state = params.get("state")
    crop = params.get("crop")
    yield_qty = params.get("yield_qty")
    service = params.get("service")

    if not all([national_id, name, state, crop, yield_qty, service]):
        return {"error": "national_id, name, state, crop, yield_qty and service are required"}

    result = await register_farmer(national_id, name, state, crop, yield_qty, service)
    return result


# async def check_availability(params):
#     """Check available appointment slots."""
#     start_date = params.get("start_date")
#     end_date = params.get(
#         "end_date", (datetime.fromisoformat(start_date) + timedelta(days=7)).isoformat()
#     )

#     if not start_date:
#         return {"error": "start_date is required"}

#     result = await get_available_appointment_slots(start_date, end_date)
#     return result


async def agent_filler(websocket, params):
    """
    Handle agent filler messages while maintaining proper function call protocol.
    """
    result = await prepare_agent_filler_message(websocket, **params)
    return result


async def end_call(websocket, params):
    """
    End the conversation and close the connection.
    """
    farewell_type = params.get("farewell_type", "general")
    result = await prepare_farewell_message(websocket, farewell_type)
    return result


# Function definitions that will be sent to the Voice Agent API
FUNCTION_DEFINITIONS = [
    {
        "name": "agent_filler",
        "description": """Use this function to provide natural conversational filler before looking up information.
        ALWAYS call this function first with message_type='lookup' when you're about to look up farmer information.
        After calling this function, you MUST immediately follow up with the appropriate lookup function (e.g., find_farmer).""",
        "parameters": {
            "type": "object",
            "properties": {
                "message_type": {
                    "type": "string",
                    "description": "Type of filler message to use. Use 'lookup' when about to search for information.",
                    "enum": ["lookup", "general"],
                }
            },
            "required": ["message_type"],
        },
    },
    {
        "name": "find_farmer",
        "description": """Look up a farmers's account information. Use context clues to determine what type of identifier the user is providing:

        National ID formats:
        - Numbers only (e.g., '123432', '678906') → Format as 'N123432', 'N678906'
        - With prefix (e.g., 'N123432', 'N678906') → Format as 'N678906', 'N678906'
        
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "national_id": {
                    "type": "string",
                    "description": "Farmer's National Id. Format as NXXXXXX where XXXXXX is the number padded to 6 digits. Example: if user says '123432', pass 'N123432'",
                },
                
            },
        },
    },    
    
    {
        "name": "create_farmer",
        "description": """Register a new farmer. Use this function when:
        - A farmer's national ID is not there
        - A farmer asks to register
        
        Before registration:
        1. Verify farmer account exists using find_farmer        
        2. Confirm national ID and service type with farmer before register""",
        "parameters": {
            "type": "object",
            "properties": {
                "national_id": {
                    "type": "string",
                    "description": "Farmer's National ID in NXXXXXX format. Must be obtained from find_farmer first.",
                },
                "name": {
                    "type": "string",
                    "description": """normal person name
                    Example: 'abhishek' → 'abhishek'""",
                },
                "state": {
                    "type": "string",
                    "description": """A state name of India
                    Example: 'Kerala' → 'Kerala'""",
                },
                "crop": {
                    "type": "string",
                    "description": """A crop name
                    Example: 'Rubber' → 'Rubber'""",
                },
                "yield_qty": {
                    "type": "integer",
                    "description": """an integer value in tons
                    Example: '1000' → '1000 tons'""",
                },
                "service": {
                    "type": "string",
                    "description": "Type of service requested. Must be one of the following: Consultation, Follow-up, Review, or Planning",
                    "enum": ["Register", "Create"],
                },
            },
            "required": ["national_id", "name", "state", "crop", "yield_qty", "service"],
        },
    },    
    {
        "name": "end_call",
        "description": """End the conversation and close the connection. Call this function when:
        - User says goodbye, thank you, etc.
        - User indicates they're done ("that's all I need", "I'm all set", etc.)
        - User wants to end the conversation
        
        Examples of triggers:
        - "Thank you, bye!"
        - "That's all I needed, thanks"
        - "Have a good day"
        - "Goodbye"
        - "I'm done"
        
        Do not call this function if the user is just saying thanks but continuing the conversation.""",
        "parameters": {
            "type": "object",
            "properties": {
                "farewell_type": {
                    "type": "string",
                    "description": "Type of farewell to use in response",
                    "enum": ["thanks", "general", "help"],
                }
            },
            "required": ["farewell_type"],
        },
    },
]

# Map function names to their implementations
FUNCTION_MAP = {
    "find_farmer": find_farmer,
    "create_farmer": create_farmer,
    "agent_filler": agent_filler,
    "end_call": end_call,
}
