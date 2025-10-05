#!/usr/bin/env python3
"""
Simple script to retrieve a conversation by ID and print its history.
"""

import sys
from sqlalchemy import create_engine, text

# Database URL - using SQLite for development
DATABASE_URL = "sqlite:///./buildsure.db"

def get_conversation_history(conversation_id: str):
    """
    Retrieve a conversation by ID and print its history.

    Args:
        conversation_id: The UUID of the conversation to retrieve
    """
    # Create engine and connection
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )

    try:
        with engine.connect() as conn:
            # Query for the conversation using raw SQL
            query = text("SELECT id, history FROM conversation WHERE id = :conversation_id")
            result = conn.execute(query, {"conversation_id": conversation_id})
            conversation = result.fetchone()

            if conversation:
                print(f"Conversation ID: {conversation.id}")
                print(f"History: {conversation.history}")
            else:
                print(f"No conversation found with ID: {conversation_id}")

    except Exception as e:
        print(f"Error retrieving conversation: {e}")


if __name__ == "__main__":
    # Default conversation ID to retrieve
    conversation_id = "123e4567-e89b-12d3-a456-426614174000"

    # Allow command line argument for different ID
    if len(sys.argv) > 1:
        conversation_id = sys.argv[1]

    print(f"Retrieving conversation with ID: {conversation_id}")
    print("-" * 50)

    get_conversation_history(conversation_id)
