from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from langgraph.checkpoint.postgres import PostgresSaver,CheckpointTuple
import time
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HumanInputType(Enum):
    APPROVAL = "APPROVAL"
    QUESTION = "QUESTION"

class InputStatus(Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"

# Simple PostgresSaver with human input tracking
class HumanApprovalPostgresSaver(PostgresSaver):
    def setup(self) -> None:
        """Setup tables"""
        super().setup()
        with self.conn.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS human_inputs (
                    thread_id TEXT,
                    checkpoint_id TEXT,
                    input_type TEXT,
                    question TEXT,
                    status TEXT,
                    created_at TIMESTAMP WITH TIME ZONE,
                    metadata JSONB,
                    response TEXT,
                    PRIMARY KEY (thread_id, checkpoint_id)
                );
                """)
            conn.commit()

    def create_input_request(
        self, 
        config: Dict, 
        input_type: HumanInputType,
        question: Optional[str] = None,
        metadata: Dict = None
    ):
        try:
            thread_id = config["configurable"]["thread_id"]
            checkpoint_id = config["configurable"]["checkpoint_id"]
            print(f"create_input_request start for thread_id {thread_id} checkpoint_id {checkpoint_id}")
            with self.conn.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                    INSERT INTO human_inputs 
                    (thread_id, checkpoint_id, input_type, question, status, created_at, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        thread_id,
                        checkpoint_id,
                        input_type.value,
                        question,
                        InputStatus.PENDING.value,
                        datetime.now(),
                        json.dumps(metadata)
                    ))
                conn.commit()
            print(f"create_input_request completed for thread_id {thread_id} checkpoint_id {checkpoint_id}")  
        except Exception as e:
            logger.error(f"Error in create_input_request: {e}")  

    def get_pending_inputs(self) -> List[Dict]:
        with self.conn.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                WITH latest_checkpoints AS (
                    SELECT 
                        thread_id,
                        MAX(checkpoint_id) as latest_checkpoint_id
                    FROM human_inputs
                    WHERE status = %s
                    GROUP BY thread_id
                )
                SELECT hi.*
                FROM human_inputs hi
                INNER JOIN latest_checkpoints lc 
                    ON hi.thread_id = lc.thread_id 
                    AND hi.checkpoint_id = lc.latest_checkpoint_id
                ORDER BY hi.created_at DESC
                """, (InputStatus.PENDING.value,))
                
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]

    def submit_response(
        self, 
        thread_id: str, 
        checkpoint_id: str, 
        response: str
    ):
        try: 
            with self.conn.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                    UPDATE human_inputs 
                    SET status = %s,
                        response = %s
                    WHERE thread_id = %s AND checkpoint_id = %s
                    """, (InputStatus.COMPLETED.value, response, thread_id, checkpoint_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Error in submit_response: {e}")
   

    def get_conversation_history(self, thread_id: str) -> List[CheckpointTuple]:
        """Get conversation history using get_state_history"""
        checkpoints = []
        try: 
            print("get_conversation_history start" )
            start = time.time()
            config = {
                "configurable": {
                    "thread_id": thread_id,
                }
            }

            # Get all checkpoints for this thread
            checkpoints = list(self.list(config))
            checkpoints.reverse()
            # Pre-process and filter checkpoints to reduce data
            #filtered_checkpoints = [
            #    cp for cp in checkpoints 
            #    if cp.metadata and 'writes' in cp.metadata
            #]
            end = time.time() - start
            print(f"get_conversation_history end. Size: {len(checkpoints)}, time:{end} s" )
        except Exception as e:
            logger.error(f"Error in get_conversation_history: {e}")
        return checkpoints
     